FastAPI Tasks API

REST API for task management with user authentication, PostgreSQL, Alembic migrations, and Docker Compose.

Features

User registration with secure Argon2 password hashing

JWT authentication

Tasks belong to their creator

Create, read, update, complete, and delete tasks

PostgreSQL database

Alembic migrations

Docker Compose setup

Basic automated tests with pytest

Tech Stack

Python

FastAPI

SQLAlchemy

PostgreSQL

Alembic

PyJWT

Docker and Docker Compose

Run with Docker

Create a .env file in the project root:

DATABASE\_PASSWORD="your\_postgres\_password"

SECRET\_KEY="your\_secret\_jwt\_key"

DATABASE\_HOST=localhost

Start the application:

docker compose up --build

Open the API documentation:

http://127.0.0.1:8000/docs

To run containers in the background:

docker compose up -d

To stop them:

docker compose down

API Endpoints

Method	Endpoint	Description

POST	/users	Register a user

POST	/token	Get a JWT access token

GET	/users/me	Get the current user

GET	/tasks	Get tasks of the current user

POST	/tasks	Create a task

GET	/tasks/{task\_id}	Get one task

PUT	/tasks/{task\_id}	Update a task title

PUT	/tasks/{task\_id}/done	Mark a task as completed

DELETE	/tasks/{task\_id}	Delete a task





All task endpoints require JWT authorization.

Tests

Activate the virtual environment and run:

pytest

Notes

Never commit the .env file. It contains database credentials and the JWT secret key.

