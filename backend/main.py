from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import BaseModel
import os

from database import get_db, engine, SessionLocal
import models
import deployer

# auth utilities
from auth import hash_password, verify_password, create_token

# OAuth handlers
from oauth import github_login, github_callback, google_login, google_callback


# -----------------------------
# Create tables
# -----------------------------
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="CloudOps Mini-PaaS API")

templates = Jinja2Templates(directory="templates")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = "supersecret"
ALGORITHM = "HS256"


# -----------------------------
# Schemas
# -----------------------------
class DeployRequest(BaseModel):
    repo_url: str
    name: str
    port: int


class UserRegister(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


# -----------------------------
# Auth Helper
# -----------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if email is None:
            raise HTTPException(status_code=401)

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise HTTPException(status_code=401)

    return user


# -----------------------------
# Render UI
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# -----------------------------
# OAuth Routes
# -----------------------------
@app.get("/auth/github")
async def github_auth(request: Request):
    return await github_login(request)


@app.get("/auth/github/callback")
async def github_auth_callback(request: Request, db: Session = Depends(get_db)):
    return await github_callback(request, db)


@app.get("/auth/google")
async def google_auth(request: Request):
    return await google_login(request)


@app.get("/auth/google/callback")
async def google_auth_callback(request: Request, db: Session = Depends(get_db)):
    return await google_callback(request, db)


# -----------------------------
# Register
# -----------------------------
@app.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):

    existing = db.query(models.User).filter(models.User.email == data.email).first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        email=data.email,
        password=hash_password(data.password)
    )

    db.add(user)
    db.commit()

    return {"message": "User registered successfully"}


# -----------------------------
# Login
# -----------------------------
@app.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user.email)

    return {"access_token": token}


# -----------------------------
# Deploy Endpoint
# -----------------------------
@app.post("/deploy")
async def deploy(
    data: DeployRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    existing = db.query(models.Project).filter(
        (models.Project.container_name == data.name) |
        (models.Project.port == data.port)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Project name or port already in use.")

    project = models.Project(
        repo_url=data.repo_url,
        container_name=data.name,
        port=data.port,
        status="PENDING",
        user_id=current_user.id
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    background_tasks.add_task(run_deployment_task, project.id, data)

    return {
        "project_id": project.id,
        "status": "Deployment started"
    }


# -----------------------------
# Deployment Status
# -----------------------------
@app.get("/deployment-status/{project_id}")
def deployment_status(project_id: int, db: Session = Depends(get_db)):

    project = db.query(models.Project).filter(models.Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    docker_user = os.getenv("DOCKERHUB_USERNAME")

    return {
        "status": project.status,
        "container_name": project.container_name,
        "port": project.port,
        "docker_pull": f"docker pull {docker_user}/{project.container_name}:latest",
        "docker_run": f"docker run -p {project.port}:8000 {docker_user}/{project.container_name}:latest",
        "url": f"http://localhost:{project.port}"
    }


# -----------------------------
# Background Deployment
# -----------------------------
def run_deployment_task(project_id: int, data: DeployRequest):

    db = SessionLocal()
    project = db.query(models.Project).filter(models.Project.id == project_id).first()

    try:
        project.status = "DEPLOYING"
        db.commit()

        result = deployer.deploy_project(
            repo_url=data.repo_url,
            container_name=data.name,
            port=data.port
        )

        if "error" in result:
            project.status = "FAILED"
        else:
            project.status = "RUNNING"
            project.docker_id = result.get("docker_id")

        db.commit()

    except Exception as e:
        print("Deployment error:", e)
        project.status = "ERROR"
        db.commit()

    finally:
        db.close()


# -----------------------------
# List User Projects
# -----------------------------
@app.get("/projects")
def list_projects(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    return db.query(models.Project).filter(
        models.Project.user_id == current_user.id
    ).all()