# Scripts Directory

This directory contains organized scripts for testing, development, and maintenance of the Advanced Timetable Scheduling System.

## Directory Structure

```
scripts/
├── testing/
│   ├── database/     # Database testing and validation scripts
│   ├── api/          # API endpoint testing scripts
│   └── data/         # Test data generation scripts
├── utilities/        # Utility scripts for system maintenance
└── README.md         # This file
```

## Testing Scripts

### Database Testing (`testing/database/`)

#### `check_db.py`
**Purpose:** Tests basic database connectivity and collection access
**Usage:** `python scripts/testing/database/check_db.py`
**Description:** Verifies that the application can connect to MongoDB and access all required collections.

#### `check_users.py`
**Purpose:** Validates user data structure and role assignments
**Usage:** `python scripts/testing/database/check_users.py`
**Description:** Examines user records to ensure proper role assignments and data integrity.

#### `check_faculty_requests.py`
**Purpose:** Verifies faculty unavailability request system
**Usage:** `python scripts/testing/database/check_faculty_requests.py`
**Description:** Tests the faculty unavailability request workflow and data consistency.

#### `check_teacher_faculty.py`
**Purpose:** Checks faculty and department assignments
**Usage:** `python scripts/testing/database/check_teacher_faculty.py`
**Description:** Validates that all faculty members have proper faculty and department assignments.

#### `check_pending_requests.py`
**Purpose:** Monitors pending request status and workflow
**Usage:** `python scripts/testing/database/check_pending_requests.py`
**Description:** Examines pending unavailability requests and their processing status.

### API Testing (`testing/api/`)

#### `test_frontend_api.py`
**Purpose:** Comprehensive testing of all API endpoints
**Usage:** `python scripts/testing/api/test_frontend_api.py`
**Description:** Tests all major API endpoints for proper functionality and response formats.

#### `test_consolidated_system.py`
**Purpose:** End-to-end testing of integrated systems
**Usage:** `python scripts/testing/api/test_consolidated_system.py`
**Description:** Tests the complete workflow from frontend to backend integration.

#### `test_faculty_availability.py`
**Purpose:** Specific testing of faculty availability features
**Usage:** `python scripts/testing/api/test_faculty_availability.py`
**Description:** Focused testing of the faculty availability management system.

#### `test_new_system.py`
**Purpose:** Testing of newly implemented functionality
**Usage:** `python scripts/testing/api/test_new_system.py`
**Description:** Tests recently added features and system improvements.

### Data Management (`testing/data/`)

#### `create_test_data.py`
**Purpose:** Generates realistic test data for development
**Usage:** `python scripts/testing/data/create_test_data.py`
**Description:** Creates sample users, subjects, rooms, and other test data for development and testing.

## Utility Scripts (`utilities/`)

#### `assign_faculty_departments.py`
**Purpose:** Assigns faculty and department fields to users
**Usage:** `python scripts/utilities/assign_faculty_departments.py`
**Description:** Utility to assign or update faculty and department information for existing users. Useful for system setup and data migration.

#### `configure_gitignore.py`
**Purpose:** Configure .gitignore settings for testing scripts and documentation
**Usage:** `python scripts/utilities/configure_gitignore.py [command]`
**Description:** Interactive utility to manage which files are tracked or ignored by Git. Supports commands like `status`, `ignore-tests`, `track-tests`, `ignore-docs`, `track-docs`, `minimal`, and `full`.

## Usage Guidelines

### Prerequisites
- Ensure the virtual environment is activated: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
- Ensure MongoDB is running and accessible
- Ensure environment variables are properly configured (`.env` file)

### Running Scripts
All scripts should be run from the project root directory:

```bash
# Example: Run database connectivity test
python scripts/testing/database/check_db.py

# Example: Generate test data
python scripts/testing/data/create_test_data.py

# Example: Test API endpoints
python scripts/testing/api/test_frontend_api.py
```

### Environment Setup
Most scripts require:
1. Active virtual environment
2. Proper database connection
3. Environment variables loaded from `.env`

### Error Handling
- Scripts include comprehensive error handling and logging
- Check console output for detailed error messages
- Ensure database connectivity before running database-dependent scripts

## Development Workflow

### Adding New Scripts
1. Place scripts in appropriate subdirectory based on purpose
2. Follow naming convention: `verb_noun.py` (e.g., `test_authentication.py`)
3. Include proper documentation and error handling
4. Update this README with script description

### Testing Workflow
1. Run database tests first to ensure connectivity
2. Run API tests to verify endpoint functionality
3. Use data generation scripts for development environments
4. Run utility scripts as needed for maintenance

## Maintenance

### Regular Testing
- Run database tests weekly to ensure data integrity
- Run API tests before major deployments
- Generate fresh test data for development environments monthly

### Script Updates
- Update scripts when database schema changes
- Modify API tests when endpoints are added or modified
- Keep utility scripts current with system requirements

## Troubleshooting

### Common Issues
1. **Database Connection Errors**: Check MongoDB service and connection string
2. **Import Errors**: Ensure virtual environment is activated and dependencies installed
3. **Permission Errors**: Check file permissions and database access rights

### Getting Help
- Check script output for specific error messages
- Verify environment configuration
- Consult main project documentation in `docs/` directory

## Related Documentation
- Database structure: `docs/DATABASE_AND_SYSTEM_DOCUMENTATION.md`
- API documentation: Project README and Swagger docs
- System architecture: `docs/` directory files 