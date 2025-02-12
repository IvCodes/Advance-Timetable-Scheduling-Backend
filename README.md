# University Scheduler Backend

Project 24-25J-238


## Project Description
The University Scheduler Backend is an advanced timetable scheduling system that uses multiple AI algorithms to generate optimal schedules for universities. The system employs Genetic Algorithms (GA), Constraint Optimization (CO), Reinforcement Learning (RL), and comprehensive evaluation metrics to create conflict-free timetables while considering various constraints.

## 👥 Team  Members

### Group Leader: IT21259852 - Weerasinghe K.D.E.I - it21259852@my.sliit.lk

### Member 1: IT21172182 - Wijayawardhana G.L.C.N.D. - it21172182@my.sliit.lk  

### Member 2: IT21208980 - De Silva K H P N - it21208980@my.sliit.lk    

### Member 3: IT21266164 - Udayantha D.M.S - it21266164@my.sliit.lk  

## System Architecture

```mermaid
flowchart TD
    A[Frontend] --> B[FastAPI Backend]
    B --> C[Authentication]
    B --> D[Data Management]
    B --> E[Scheduler Engine]
    E --> F[GA Algorithm]
    E --> G[CO Algorithm]
    E --> H[RL Algorithm]
    E --> I[Evaluation]
    D --> J[(Database)]
```

## Component Architecture

```mermaid
flowchart TD
    subgraph Frontend
    A[React UI] --> B[Redux State]
    B --> C[API Integration]
    end

    subgraph Backend
    D[FastAPI] --> E[Routers]
    D --> F[Models]
    D --> G[Services]
    end

    subgraph Algorithms
    H[GA] --> K[Evaluation]
    I[CO] --> K
    J[RL] --> K
    end

    C --> D
    E --> L
    F --> L  

```

### Authentication Flow 

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as Auth Service
    participant D as Database
    
    U->>F: Login Request
    F->>A: Authenticate
    A->>D: Validate Credentials
    D-->>A: User Data
    A-->>F: JWT Token
    F-->>U: Auth Success

```
```mermaid
graph TD
    A[Input Data] --> B[Data Collector]
    B --> C{Algorithm Selection}
    C --> D[GA]
    C --> E[CO]
    C --> F[RL]
    D --> G[Evaluation]
    E --> G
    F --> G
    G --> H[Best Schedule]
    H --> I[Output]
```
## Setup Instructions

### Prerequisites
- Python 3.8+
- MongoDB
- Virtual Environment

### Installation Steps
```bash
# Clone the repository
git clone https://github.com/your-repo/university-scheduler-backend.git
cd university-scheduler-backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload
fastapi dev run
```
