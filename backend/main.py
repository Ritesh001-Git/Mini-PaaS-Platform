import os
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, engine, SessionLocal
import models
import deployer


# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(title="CloudOps Mini-PaaS API")

# Templates
templates = Jinja2Templates(directory="templates")

# -----------------------------
# Create database tables
# -----------------------------
models.Base.metadata.create_all(bind=engine)


# -----------------------------
# Schemas
# -----------------------------
class DeployRequest(BaseModel):
    repo_url: str
    name: str
    port: int


# -----------------------------
# Render UI
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# -----------------------------
# Deploy Endpoint (NO AUTH)
# -----------------------------
@app.post("/deploy")
async def deploy(
    data: DeployRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):

    # 👇 Temporary dummy user
    user_id = 1

    # -----------------------------
    # Check if project exists
    # -----------------------------
    existing = db.query(models.Project).filter(
        (models.Project.container_name == data.name) |
        (models.Project.port == data.port)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Project name or port already in use.")

    # -----------------------------
    # Create Project
    # -----------------------------
    project = models.Project(
        repo_url=data.repo_url,
        container_name=data.name,
        port=data.port,
        status="PENDING",
        user_id=user_id
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    # -----------------------------
    # Background Deployment
    # -----------------------------
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
        "url": f"http://{os.getenv('EC2_PUBLIC_IP', 'localhost')}/{project.container_name}/"
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
# List Projects (NO AUTH)
# -----------------------------
@app.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()