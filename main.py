from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, ForeignKey, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone

from jwt.exceptions import InvalidTokenError
from fastapi import status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from database import Base, SessionLocal
import os

from dotenv import load_dotenv

app = FastAPI()


password_hasher = PasswordHash.recommended()

load_dotenv()
SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
class User(Base):
    __tablename__="users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(50),
	unique=True,
	index=True,
    )
    password_hash: Mapped[str]= mapped_column(String(255))

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)

class UserRead(BaseModel):
    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)

class TaskUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TaskRead(BaseModel):
    id: int
    title: str
    description: str | None
    done: bool

    model_config = ConfigDict(from_attributes=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def create_access_token(data:dict) -> str:
    payload = data.copy()
    expires_at = datetime.now(timezone.utc)+timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload["exp"] = expires_at
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить пользователя",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        username = payload.get("sub")

        if username is None:
            raise credentials_error

    except InvalidTokenError:
        raise credentials_error

    user = db.scalar(
        select(User).where(User.username == username)
    )

    if user is None:
        raise credentials_error

    return user
	
def get_owned_task(
    task_id: int,
    current_user: User,
    db: Session,
) -> Task:
    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
	    Task.user_id == current_user.id,
	)
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    return task



@app.get("/")
def home():
    return {"message": "API задач работает с PostgreSQL"}


@app.get("/tasks", response_model=list[TaskRead])
def get_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.scalars(
        select(Task).where(Task.user_id == current_user.id)
    ).all()


@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.scalar(
        select(Task).where(
            Task.id==task_id,
	    Task.user_id == current_user.id,
	)
    )
    
    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    return task


@app.post("/tasks", response_model=TaskRead, status_code=201)
def create_task(
    task_data: TaskCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = Task(
        title=task_data.title,
        description=task_data.description,  
        user_id=current_user.id,
)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.put("/tasks/{task_id}/done", response_model=TaskRead)
def complete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = get_owned_task(task_id, current_user, db)
    task.done = True

    db.commit()
    db.refresh(task)
    return task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = get_owned_task(task_id, current_user, db)
    db.delete(task)
    db.commit()

@app.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task= get_owned_task(task_id, current_user, db)
    
    task.title = task_data.title
    db.commit()
    db.refresh(task)
    return task


@app.post("/users", response_model=UserRead, status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.scalar(
        select(User).where(User.username ==user_data.username)
    )
    if existing_user is not None:
        raise HTTPException(
	    status_code=409,
            detail="Пользователь с таким именем уже существует",
		
        )
    user = User(
        username=user_data.username,
        password_hash=password_hasher.hash(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.username == form_data.username)
    )

    if user is None or not password_hasher.verify(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user.username})

    return {
        "access_token": token,
        "token_type": "bearer",
    }	

@app.get("/users/me", response_model=UserRead)
def read_current_user(
    current_user: User = Depends(get_current_user),
):
    return current_user

    
