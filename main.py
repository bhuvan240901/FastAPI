from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from sqlalchemy.orm import declarative_base
from typing import List, Optional
# SQLAlchemy models
Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    completed = Column(Boolean, default=False)

# Pydantic model for request
class TaskCreate(BaseModel):
    title: str
    description: str
    completed: bool

# Pydantic model for response
class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool

# Database configuration
DATABASE_URL = "mysql+mysqlconnector://root:root@localhost:3306/fastapi"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI app
app = FastAPI()

# Create Endpoint
@app.post("/tasks/", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

# Read Endpoint
@app.get("/tasks/{task_id}", response_model=TaskResponse)
def read_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(**task.__dict__)

# Read all tasks Endpoint
@app.get("/tasks/", response_model=List[TaskResponse])
def read_all_tasks(completed: Optional[bool] = None, db: Session = Depends(get_db)):
    if completed is not None:
        tasks = db.query(Task).filter(Task.completed == completed).all()
    else:
        tasks = db.query(Task).all()
    return [TaskResponse(**task.__dict__) for task in tasks]

# Update Endpoint
@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, updated_task: TaskCreate, db: Session = Depends(get_db)):
    existing_task = db.query(Task).filter(Task.id == task_id).first()
    if existing_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in updated_task.dict().items():
        setattr(existing_task, field, value)

    db.commit()
    db.refresh(existing_task)
    return TaskResponse(**existing_task.__dict__)

# Delete Endpoint
@app.delete("/tasks/{task_id}", response_model=dict)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}