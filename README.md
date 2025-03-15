# University Scheduler Backend

Project 24-25J-238

## Project Description

The University Scheduler Backend is an advanced timetable scheduling system that uses multiple AI algorithms to generate optimal schedules for universities. The system employs Genetic Algorithms (GA), Constraint Optimization (CO), Reinforcement Learning (RL), and comprehensive evaluation metrics to create conflict-free timetables while considering various constraints.

## 👥 Team Members

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

## ER Diagram

```mermaid
erDiagram
    Users {
        string id
        string first_name
        string last_name
        string username
        string email
        string telephone
        string position
        string role
        string hashed_password
        object subjects
        number target_hours
        object unavailable_dates
    }

    Roles {
        string role_id
        string role_name
    }

    Timetable {
        string code
        string algorithm
        string semester
        object timetable
        boolean is_active
    }

    AlgorithmSelection {
        string selected_algorithm
        object assigned_timetable_id
    }

    timetable_history {
        object timetable_id
        object previous_state
        object new_state
        string modified_by
        object modified_at
    }

    old_scores {
        object value
    }

    settings {
        string option
        object value
    }

    constraints {
        string code
        string type
        string scope
        string name
        string description
        object settings
        object applicability
        number weight
        object created_at
        object updated_at
    }

    modules {
        string code
        string name
        string long_name
        string description
    }

    days_of_operation {
        string name
        string long_name
    }

    periods_of_operation {
        string name
        string long_name
        boolean is_interval
    }

    Activities {
        string code
        string name
        string subject
        object teacher_ids
        object subgroup_ids
        number duration
    }

    faculties {
        string code
        string short_name
        string long_name
    }

    Years {
        number name
        string long_name
        number total_capacity
        number total_students
        object subgroups
    }

    old_timetables {
        string code
        string algorithm
        string semester
        object timetable
        object date_created
    }

    notifications {
        string message
        string type
        boolean read
    }

    Spaces {
        string name
        string long_name
        string code
        number capacity
        object attributes
    }

    university_info {
        string institution_name
        string description
        object id
    }

    AlgorithmSelection ||--o| Timetable : "assigns"
    AlgorithmSelection ||--o| constraints : "considers"
    AlgorithmSelection ||--o| days_of_operation : "considers"
    AlgorithmSelection ||--o| periods_of_operation : "considers"
    AlgorithmSelection ||--o| university_info : "considers"
    Users ||--o{ Activities : "teaches"
    Users ||--o| Roles : "has role"
    Users ||--o{ Timetable : "assigned to"
    faculties ||--o{ Timetable : "assigned to"
    Timetable ||--|{ timetable_history : "has history"
    Timetable ||--o{ old_timetables : "previous versions"
    Activities ||--o{ modules : "relates to"
    Activities ||--o{ faculties : "associated with"
    Activities ||--o{ Years : "scheduled in"
    Spaces ||--o{ Timetable : "assigned to"
    constraints ||--o{ settings : "defined by"
    Users ||--o{ notifications : "receives"
    faculties ||--o{ Spaces : "manages"

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
