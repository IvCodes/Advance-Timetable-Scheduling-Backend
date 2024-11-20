# University Scheduler Backend

A FastAPI-based backend system for managing university schedules, including spaces, faculty, modules, and student information.

## Features

- User Management (Students, Faculty, Admin)
- Space Management (Lecture Halls, Labs, etc.)
- Faculty Management
- Module/Course Management
- Year and Student Group Management
- Information Management

## Tech Stack

- Python 3.x
- FastAPI
- Pydantic
- MongoDB
- JWT Authentication

## Setup

Clone the repository

python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate


pip install -r requirements.txt


uvicorn main:app --reload