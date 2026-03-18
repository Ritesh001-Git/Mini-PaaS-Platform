import os
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, engine, SessionLocal
import models
import deployer

app = FastAPI()

templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)


class DeployRequest(BaseModel):
    repo_url: str
    name: str
    port: int


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/deploy")
async def deploy(data: DeployRequest,
                 background_tasks: BackgroundTasks,
                 db: Session = Depends(get_db)):

    # dummy user
    user_id = "1"

    existing = db.query(models.Project).filter(
        (models.Project.container_name == data.name) |
        (models.Project.port == data.port)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Name or port already used")

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

    background_tasks.add_task(run_deployment_task, project.id, data)

    return {"project_id": project.id}


@app.get("/deployment-status/{project_id}")
def status(project_id: int, db: Session = Depends(get_db)):

    project = db.query(models.Project).filter_by(id=project_id).first()

    if not project:
        raise HTTPException(404)

    return {
        "status": project.status,
        "url": f"http://{os.getenv('EC2_PUBLIC_IP', 'localhost')}/{project.container_name}/"
    }


def run_deployment_task(project_id, data):

    db = SessionLocal()
    project = db.query(models.Project).get(project_id)

    try:
        project.status = "DEPLOYING"
        db.commit()

        result = deployer.deploy_project(
            repo_url=data.repo_url,
            container_name=data.name,
            port=data.port
        )

        project.status = "RUNNING" if "error" not in result else "FAILED"
        db.commit()

    except Exception as e:
        project.status = "ERROR"
        db.commit()

    finally:
        db.close()