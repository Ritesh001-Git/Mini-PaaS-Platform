from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    repo_url = Column(String, nullable=False) #
    container_name = Column(String, unique=True, nullable=False) #
    port = Column(Integer, unique=True, nullable=False) #
    status = Column(String, default="PENDING") #
    
    # New Industry-Level Fields
    docker_id = Column(String, nullable=True)  # Store the actual Docker Container ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())