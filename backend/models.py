from sqlalchemy import Column, Integer, String
from database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    repo_url = Column(String)
    container_name = Column(String)
    port = Column(Integer)
    status = Column(String)