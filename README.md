# University Scheduler Backend

## Project Description
The University Scheduler Backend is an advanced timetable scheduling system that uses multiple AI algorithms to generate optimal schedules for universities. The system employs Genetic Algorithms (GA), Constraint Optimization (CO), Reinforcement Learning (RL), and comprehensive evaluation metrics to create conflict-free timetables while considering various constraints.

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

