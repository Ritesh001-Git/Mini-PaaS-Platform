from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db, engine
import models
import deployer
from pydantic import BaseModel

# Initialize database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="CloudOps Mini-PaaS API")

# Request Schema
class DeployRequest(BaseModel):
    repo_url: str
    name: str
    port: int

@app.post("/deploy")
async def deploy(data: DeployRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Check if project name or port is already taken
    existing_project = db.query(models.Project).filter(
        (models.Project.container_name == data.name) | (models.Project.port == data.port)
    ).first()
    
    if existing_project:
        raise HTTPException(status_code=400, detail="Project name or Port already in use.")

    # 2. Save initial "PENDING" state to Database
    new_project = models.Project(
        repo_url=data.repo_url,
        container_name=data.name,
        port=data.port,
        status="PENDING"
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # 3. Run deployment in the background to prevent API timeout
    background_tasks.add_task(run_deployment_task, new_project.id, data)
    
    return {"message": "Deployment started", "project_id": new_project.id}

def run_deployment_task(project_id: int, data: DeployRequest):
    # Create a fresh DB session for the background thread
    from database import SessionLocal
    db = SessionLocal()
    project = db.query(models.Project).filter(models.Project.id == project_id).first()

    try:
        # Update status to DEPLOYING
        project.status = "DEPLOYING"
        db.commit()

        # Trigger the actual Docker/Git logic
        success = deployer.deploy_project(data.repo_url, data.name, data.port)

        if success:
            project.status = "RUNNING"
        else:
            project.status = "FAILED"
            
    except Exception as e:
        print(f"Error during background deployment: {e}")
        project.status = "ERROR"
    finally:
        db.commit()
        db.close()

@app.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()