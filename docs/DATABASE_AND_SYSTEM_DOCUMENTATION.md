# Database Structure and System Documentation

## Overview
This document provides comprehensive documentation of the database structure, algorithms, and system architecture discovered during development and testing.

## Database Structure

### Collections Overview

#### 1. Users Collection
**Purpose:** Central user management for all system users

**Structure:**
```javascript
{
  "_id": ObjectId,
  "id": String,                    // Unique user identifier
  "first_name": String,
  "last_name": String,
  "username": String,              // Login username
  "email": String,
  "telephone": String,
  "position": String,
  "role": String,                  // "admin", "faculty", "student"
  "hashed_password": String,
  "subjects": Array,               // Subject codes assigned to faculty
  "target_hours": Number,          // Target teaching hours per week
  "faculty": String,               // Faculty assignment (e.g., "Faculty of Computing")
  "department": String,            // Department (e.g., "Computer Science")
  "unavailable_dates": Array       // Legacy field for old system
}
```

**Key Insights:**
- Faculty members are stored with `role: "faculty"`
- Originally missing `faculty` and `department` fields (fixed during development)
- Contains both current and legacy unavailability data

#### 2. faculty_unavailability Collection
**Purpose:** New system for managing faculty unavailability requests

**Structure:**
```javascript
{
  "_id": ObjectId,
  "record_id": String,             // Unique request identifier
  "faculty_id": String,            // References Users.id
  "faculty_name": String,          // Cached faculty name
  "department": String,            // Faculty department
  "date": String,                  // Date in YYYY-MM-DD format
  "reason": String,                // Reason for unavailability
  "unavailability_type": String,   // "sick_leave", "personal_leave", etc.
  "status": String,                // "pending", "approved", "denied"
  "substitute_id": String,         // Optional substitute faculty ID
  "substitute_name": String,       // Cached substitute name
  "admin_notes": String,           // Admin comments
  "created_at": DateTime,
  "updated_at": DateTime
}
```

**Status Values:**
- `pending` - Awaiting admin review
- `approved` - Approved by admin
- `denied` - Rejected by admin

**Unavailability Types:**
- `sick_leave` - Medical leave
- `personal_leave` - Personal time off
- `conference` - Conference/training attendance
- `emergency` - Emergency situations
- `other` - Other reasons

#### 3. teachers Collection
**Purpose:** Separate teacher data (currently empty - data is in Users)

**Status:** Not actively used - all faculty data is in Users collection

#### 4. subjects Collection
**Purpose:** Course/subject definitions

**Structure:**
```javascript
{
  "_id": ObjectId,
  "code": String,                  // Subject code (e.g., "CS101")
  "name": String,                  // Subject name
  "credits": Number,               // Credit hours
  "semester": String,              // Target semester
  "year": Number,                  // Academic year
  "prerequisites": Array           // Prerequisite subject codes
}
```

#### 5. spaces Collection
**Purpose:** Room and facility management

**Structure:**
```javascript
{
  "_id": ObjectId,
  "name": String,                  // Room identifier
  "long_name": String,             // Full room name
  "capacity": Number,              // Maximum occupancy
  "type": String,                  // "Lecture Hall", "Lab", etc.
  "attributes": Object,            // Additional properties
  "availability": Array            // Time slot availability
}
```

#### 6. days Collection
**Purpose:** Academic day definitions

**Structure:**
```javascript
{
  "_id": ObjectId,
  "name": String,                  // Short name (e.g., "Mon")
  "long_name": String,             // Full name (e.g., "Monday")
  "order": Number                  // Day ordering
}
```

#### 7. periods Collection
**Purpose:** Time period definitions

**Structure:**
```javascript
{
  "_id": ObjectId,
  "name": String,                  // Period identifier (e.g., "P1")
  "long_name": String,             // Full description
  "start_time": String,            // Start time
  "end_time": String,              // End time
  "duration": Number               // Duration in hours
}
```

## System Architecture

### Faculty Availability Management

#### Old System (Legacy)
- Stored unavailability in `Users.unavailable_dates` array
- Simple date-based storage
- Limited functionality

#### New System (Current)
- Dedicated `faculty_unavailability` collection
- Rich metadata and workflow support
- Admin approval process
- Substitute assignment capability

### Timetable Generation

#### Algorithm Structure
The system uses multiple algorithms for timetable optimization:

1. **Genetic Algorithm (GA)**
   - Population-based optimization
   - Crossover and mutation operations
   - Fitness evaluation based on constraints

2. **NSGA-II (Non-dominated Sorting Genetic Algorithm)**
   - Multi-objective optimization
   - Pareto front generation
   - Constraint handling

3. **Constraint Optimization (CO)**
   - Hard and soft constraint satisfaction
   - Penalty-based scoring
   - Backtracking algorithms

#### Timetable Data Structure
```javascript
{
  "semesters": {
    "sem1yr1": [
      {
        "day": { "name": "Mon", "long_name": "Monday" },
        "period": [{ "name": "P1", "long_name": "Period 1" }],
        "subject": "CS101",
        "teacher": "teacher_id",
        "room": { "name": "LH1" },
        "subgroup": "Group A",
        "duration": 1
      }
    ]
  }
}
```

## API Endpoints

### Faculty Availability Endpoints
- `GET /api/v1/faculty-availability/unavailability-requests` - Get all requests
- `GET /api/v1/faculty-availability/unavailability-requests/pending` - Get pending requests
- `GET /api/v1/faculty-availability/faculty/{id}/unavailable-dates` - Get faculty unavailable dates
- `POST /api/v1/faculty-availability/unavailability-requests` - Create new request
- `PUT /api/v1/faculty-availability/unavailability-requests/{id}/status` - Update request status

### Data Management Endpoints
- `GET /api/v1/data/teachers` - Get all teachers/faculty
- `GET /api/v1/data/subjects` - Get all subjects
- `GET /api/v1/data/spaces` - Get all spaces/rooms
- `GET /api/v1/data/days` - Get academic days
- `GET /api/v1/data/periods` - Get time periods

### Timetable Endpoints
- `GET /api/v1/timetable/faculty/{id}` - Get faculty-specific timetable
- `POST /api/v1/timetable/generate` - Generate new timetable
- `GET /api/v1/timetable/published` - Get published timetable

## Key Discoveries

### Database Issues Found and Fixed
1. **Missing Faculty Assignments**: All faculty users lacked `faculty` and `department` fields
2. **Dual Systems**: Old and new unavailability systems running in parallel
3. **Data Inconsistency**: Frontend calling wrong API endpoints
4. **Empty Collections**: `teachers` collection unused, data in `Users` instead

### System Integration Issues
1. **API Endpoint Mismatch**: Frontend using legacy endpoints
2. **Data Format Inconsistency**: Different date formats across systems
3. **Authentication Flow**: JWT token parsing for user identification

### Performance Considerations
1. **Database Queries**: Efficient indexing on frequently queried fields
2. **Caching Strategy**: Faculty names cached in unavailability records
3. **Pagination**: Large datasets handled with proper pagination

## Algorithms Deep Dive

### Genetic Algorithm Implementation
```python
# Simplified structure
class GeneticAlgorithm:
    def __init__(self, population_size, mutation_rate, crossover_rate):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
    
    def generate_initial_population(self):
        # Create random timetable solutions
        pass
    
    def evaluate_fitness(self, individual):
        # Calculate constraint violations and preferences
        pass
    
    def selection(self, population):
        # Tournament or roulette wheel selection
        pass
    
    def crossover(self, parent1, parent2):
        # Combine two solutions
        pass
    
    def mutation(self, individual):
        # Random modifications
        pass
```

### Constraint Types
1. **Hard Constraints** (Must be satisfied)
   - No teacher in two places at once
   - Room capacity limits
   - Teacher unavailability
   - Subject-teacher assignments

2. **Soft Constraints** (Preferences)
   - Teacher workload balance
   - Room preferences
   - Time slot preferences
   - Consecutive class scheduling

## Data Flow

### Faculty Unavailability Request Flow
1. Faculty submits request via dashboard
2. Request stored in `faculty_unavailability` collection
3. Admin reviews via admin dashboard
4. Status updated (approved/denied)
5. Optional substitute assignment
6. Notification to faculty

### Timetable Generation Flow
1. Collect constraints from database
2. Initialize algorithm parameters
3. Generate candidate solutions
4. Evaluate fitness against constraints
5. Apply genetic operations
6. Iterate until convergence
7. Select best solution
8. Store in database
9. Publish to frontend

## Testing and Validation

### Database Testing Scripts
- `check_db.py` - General database connectivity
- `check_users.py` - User data validation
- `check_faculty_requests.py` - Faculty request verification
- `check_teacher_faculty.py` - Faculty assignment verification

### API Testing Scripts
- `test_frontend_api.py` - Comprehensive API endpoint testing
- `test_consolidated_system.py` - End-to-end system testing
- `test_faculty_availability.py` - Faculty availability system testing

### Data Creation Scripts
- `create_test_data.py` - Generate test datasets
- `create_saman_request.py` - Create sample requests
- `assign_faculty_departments.py` - Fix faculty assignments

## Security Considerations

### Authentication
- JWT token-based authentication
- Role-based access control (admin, faculty, student)
- Password hashing with secure algorithms

### Data Protection
- Input validation on all endpoints
- SQL injection prevention (using MongoDB)
- Cross-site scripting (XSS) protection

### Access Control
- Faculty can only modify their own data
- Admin approval required for critical changes
- Audit trail for all modifications

## Performance Optimization

### Database Optimization
- Indexes on frequently queried fields
- Aggregation pipelines for complex queries
- Connection pooling

### Algorithm Optimization
- Parallel processing for population evaluation
- Early termination conditions
- Memory-efficient data structures

### Frontend Optimization
- Lazy loading for large datasets
- Caching of static data
- Optimistic UI updates

## Future Improvements

### Database Schema
- Add audit trail tables
- Implement soft deletes
- Add data versioning

### Algorithm Enhancements
- Machine learning integration
- Real-time constraint updates
- Multi-campus support

### System Features
- Mobile application support
- Real-time notifications
- Advanced reporting capabilities

This documentation serves as a comprehensive guide to understanding the system architecture, database structure, and algorithmic approaches used in the Advanced Timetable Scheduling System. 