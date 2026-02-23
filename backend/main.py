from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import get_db, engine, SessionLocal
import models
import deployer
from pydantic import BaseModel
import uuid

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="CloudOps Mini-PaaS API")

templates = Jinja2Templates(directory="templates")

# -----------------------------
# Schema
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
# Deploy Endpoint
# -----------------------------
@app.post("/deploy")
async def deploy(
    data: DeployRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    existing = db.query(models.Project).filter(
        (models.Project.container_name == data.name) |
        (models.Project.port == data.port)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Project name or port already in use.")

    new_project = models.Project(
        repo_url=data.repo_url,
        container_name=data.name,
        port=data.port,
        status="PENDING"
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    background_tasks.add_task(run_deployment_task, new_project.id, data)

    return {
        "project_id": new_project.id,
        "status": "Deployment started"
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

        success = deployer.deploy_project(
            repo_url=data.repo_url,
            container_name=data.name,
            port=data.port
        )

        project.status = "RUNNING" if success else "FAILED"

    except Exception as e:
        print(f"Deployment error: {e}")
        project.status = "ERROR"
    finally:
        db.commit()
        db.close()

# -----------------------------
# List Projects
# -----------------------------
@app.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()