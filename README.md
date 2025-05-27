# Advanced Timetable Scheduling System - Backend

A comprehensive timetable scheduling system using advanced optimization algorithms including Genetic Algorithm (GA), NSGA-II, and Constraint Optimization techniques.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB
- Virtual Environment

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd Advance-Timetable-Scheduling-Backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Running the Application
```bash
# Start the FastAPI server
uvicorn app.main:app --reload

# The API will be available at:
# - Main API: http://localhost:8000
# - API Documentation: http://localhost:8000/docs
# - Alternative docs: http://localhost:8000/redoc
```

## 📁 Project Structure

```
Advance-Timetable-Scheduling-Backend/
├── app/                    # Main application code
│   ├── algorithms_2/       # Optimization algorithms
│   ├── models/            # Database models
│   ├── routers/           # API route handlers
│   ├── Services/          # Business logic services
│   └── utils/             # Utility functions
├── scripts/               # Testing and utility scripts
│   ├── testing/           # Organized testing scripts
│   │   ├── database/      # Database testing
│   │   ├── api/           # API testing
│   │   └── data/          # Test data generation
│   └── utilities/         # System maintenance scripts
├── docs/                  # Comprehensive documentation
├── logs/                  # Application logs
├── Data/                  # Data files
└── venv/                  # Virtual environment
```

## 🔧 Key Features

### Timetable Generation
- **Multiple Algorithms**: Genetic Algorithm, NSGA-II, Constraint Optimization
- **Constraint Handling**: Hard and soft constraints
- **Multi-objective Optimization**: Balancing multiple criteria
- **Real-time Generation**: Dynamic timetable creation

### Faculty Management
- **Availability Tracking**: Faculty unavailability management
- **Substitute Assignment**: Automatic substitute teacher assignment
- **Workload Balancing**: Optimal distribution of teaching loads
- **Request Workflow**: Admin approval process for leave requests

### System Administration
- **User Management**: Role-based access control
- **Data Management**: CRUD operations for all entities
- **Reporting**: Comprehensive reports and analytics
- **API Documentation**: Auto-generated Swagger documentation

## 📚 Documentation

### Quick Links
- **[System Architecture](docs/DATABASE_AND_SYSTEM_DOCUMENTATION.md)** - Complete system overview
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when running)
- **[Scripts Guide](scripts/README.md)** - Testing and utility scripts
- **[Documentation Index](docs/README.md)** - All documentation files

### Key Documentation Files
- `docs/DATABASE_AND_SYSTEM_DOCUMENTATION.md` - Database structure and algorithms
- `docs/FACULTY_AVAILABILITY_IMPLEMENTATION.md` - Faculty management system
- `docs/UI_UX_FIXES_SUMMARY.md` - Recent improvements and fixes
- `docs/SCRIPT_ORGANIZATION_PLAN.md` - Script organization and usage

## 🧪 Testing

### Database Testing
```bash
# Test database connectivity
python scripts/testing/database/check_db.py

# Validate user data
python scripts/testing/database/check_users.py

# Check faculty assignments
python scripts/testing/database/check_teacher_faculty.py
```

### API Testing
```bash
# Test all API endpoints
python scripts/testing/api/test_frontend_api.py

# Test faculty availability system
python scripts/testing/api/test_faculty_availability.py

# End-to-end system testing
python scripts/testing/api/test_consolidated_system.py
```

### Test Data Generation
```bash
# Generate test data for development
python scripts/testing/data/create_test_data.py
```

## 🛠 Development

### Environment Setup
1. Ensure MongoDB is running
2. Configure `.env` file with database connection
3. Activate virtual environment
4. Install dependencies from `requirements.txt`

### Database Collections
- `Users` - User management (faculty, admin, students)
- `faculty_unavailability` - Faculty availability requests
- `subjects` - Course definitions
- `spaces` - Room and facility management
- `days` - Academic day definitions
- `periods` - Time period definitions

### API Endpoints
- `/api/v1/faculty-availability/` - Faculty availability management
- `/api/v1/data/` - Data management (CRUD operations)
- `/api/v1/timetable/` - Timetable generation and retrieval
- `/api/v1/auth/` - Authentication and authorization

## 🔍 Algorithms

### Genetic Algorithm (GA)
- Population-based optimization
- Crossover and mutation operations
- Fitness evaluation based on constraints

### NSGA-II
- Multi-objective optimization
- Pareto front generation
- Non-dominated sorting

### Constraint Optimization
- Hard and soft constraint satisfaction
- Penalty-based scoring
- Backtracking algorithms

## 📊 System Insights

### Recent Improvements
- ✅ Fixed faculty assignment data issues
- ✅ Improved UI/UX across all interfaces
- ✅ Enhanced PDF export functionality
- ✅ Consolidated faculty availability management
- ✅ Organized testing and utility scripts

### Database Statistics
- 22 Faculty members properly assigned
- Multiple optimization algorithms integrated
- Comprehensive API coverage
- Role-based access control implemented

## 🤝 Contributing

### Development Workflow
1. Run database tests to ensure connectivity
2. Run API tests to verify functionality
3. Use test data generation for development
4. Update documentation for any changes

### Adding Features
1. Follow existing code structure
2. Add appropriate tests in `scripts/testing/`
3. Update documentation in `docs/`
4. Ensure API documentation is current

## 📝 Maintenance

### Regular Tasks
- Run database tests weekly
- Update test data monthly
- Review and update documentation quarterly
- Monitor system performance and logs

### Utility Scripts
- `scripts/utilities/assign_faculty_departments.py` - Faculty assignment utility
- Various testing scripts for system validation
- Data generation scripts for development

## 🆘 Troubleshooting

### Common Issues
1. **Database Connection**: Check MongoDB service and connection string
2. **Import Errors**: Ensure virtual environment is activated
3. **Permission Errors**: Check file permissions and database access

### Getting Help
1. Check `docs/` directory for detailed documentation
2. Review script output for specific error messages
3. Consult API documentation at `/docs` endpoint
4. Check logs in `logs/` directory

## 📄 License

This project is part of the Advanced Timetable Scheduling System research project.

## 🔗 Related Projects

- **Frontend**: Advance-Timetable-Scheduling-Frontend (React application)
- **Algorithms**: Specialized optimization algorithm implementations
- **Documentation**: Comprehensive system documentation in `docs/`

---

For detailed information about any aspect of the system, please refer to the documentation in the `docs/` directory or the organized scripts in the `scripts/` directory. 