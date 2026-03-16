from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


# ---------------------------
# User Model
# ---------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship → one user can have many projects
    projects = relationship("Project", back_populates="owner", cascade="all, delete")


# ---------------------------
# Project Model
# ---------------------------
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    repo_url = Column(String, nullable=False)
    container_name = Column(String, unique=True, nullable=False)
    port = Column(Integer, unique=True, nullable=False)

    status = Column(String, default="PENDING")

    docker_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Link project → user
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="projects")