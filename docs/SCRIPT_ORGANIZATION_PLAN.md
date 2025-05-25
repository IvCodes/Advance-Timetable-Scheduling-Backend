# Script Organization Plan

## Current Script Inventory

### Testing Scripts (Keep for Future Use)
These scripts are valuable for ongoing development and testing:

#### Database Testing & Validation
- `check_db.py` - General database connectivity testing
- `check_users.py` - User data validation and verification
- `check_faculty_requests.py` - Faculty request system verification
- `check_teacher_faculty.py` - Faculty assignment verification
- `check_pending_requests.py` - Pending request status checking

#### API Testing
- `test_frontend_api.py` - Comprehensive API endpoint testing
- `test_consolidated_system.py` - End-to-end system testing
- `test_faculty_availability.py` - Faculty availability system testing
- `test_new_system.py` - New system functionality testing

#### Data Management
- `create_test_data.py` - Generate test datasets for development
- `assign_faculty_departments.py` - Faculty assignment utility (KEEP - useful for setup)

### One-Time Use Scripts (Can be Removed)
These were created for specific fixes and are no longer needed:

#### Request Creation Scripts (Remove)
- `create_saman_request.py` - Created specific test request
- `create_saman_request_admin.py` - Admin version of above
- `create_pending_request.py` - Created test pending requests

#### Debug Scripts (Remove)
- `debug_pending_requests.py` - One-time debugging
- `test_ruwan_availability.py` - Specific user testing
- `migrate_old_requests.py` - One-time migration script

### HTML Test Files (Remove)
Large HTML files that are no longer needed:
- `test_frontend_api.html` - 12KB test file
- `professional_timetable_test.html` - 110KB test output
- `test_output.html` - 101KB test output
- `Student Timetable for Semester I February 2025 Weekday Version V (2).html` - 396KB

### Documentation Files (Keep)
- `DATABASE_AND_SYSTEM_DOCUMENTATION.md` - Comprehensive system docs
- `UI_UX_FIXES_SUMMARY.md` - UI/UX improvement documentation
- `FACULTY_AVAILABILITY_CONSOLIDATION_SUMMARY.md` - System consolidation docs
- `FACULTY_AVAILABILITY_IMPLEMENTATION.md` - Implementation details
- `FRONTEND_FIXES_SUMMARY.md` - Frontend fix documentation
- `TIMETABLE_UI_FIXES.md` - Timetable UI improvements
- `TIMETABLE_IMPROVEMENTS.md` - General timetable improvements

## Proposed Organization Structure

### Create `scripts/` Directory Structure
```
scripts/
├── testing/
│   ├── database/
│   │   ├── check_db.py
│   │   ├── check_users.py
│   │   ├── check_faculty_requests.py
│   │   ├── check_teacher_faculty.py
│   │   └── check_pending_requests.py
│   ├── api/
│   │   ├── test_frontend_api.py
│   │   ├── test_consolidated_system.py
│   │   ├── test_faculty_availability.py
│   │   └── test_new_system.py
│   └── data/
│       └── create_test_data.py
├── utilities/
│   └── assign_faculty_departments.py
└── README.md
```

### Create `docs/` Directory
```
docs/
├── DATABASE_AND_SYSTEM_DOCUMENTATION.md
├── UI_UX_FIXES_SUMMARY.md
├── FACULTY_AVAILABILITY_CONSOLIDATION_SUMMARY.md
├── FACULTY_AVAILABILITY_IMPLEMENTATION.md
├── FRONTEND_FIXES_SUMMARY.md
├── TIMETABLE_UI_FIXES.md
└── TIMETABLE_IMPROVEMENTS.md
```

## Implementation Plan

### Phase 1: Create Directory Structure
1. Create `scripts/` directory with subdirectories
2. Create `docs/` directory
3. Create README files for each directory

### Phase 2: Move Useful Scripts
1. Move database testing scripts to `scripts/testing/database/`
2. Move API testing scripts to `scripts/testing/api/`
3. Move data creation scripts to `scripts/testing/data/`
4. Move utility scripts to `scripts/utilities/`

### Phase 3: Move Documentation
1. Move all .md files to `docs/` directory
2. Update any relative path references

### Phase 4: Remove Unnecessary Files
1. Delete one-time use scripts
2. Delete large HTML test files
3. Update .gitignore if needed

### Phase 5: Create Documentation
1. Create `scripts/README.md` explaining each script's purpose
2. Create `docs/README.md` with documentation index
3. Update main README.md with new structure

## Script Descriptions for Future Reference

### Database Testing Scripts
- **check_db.py**: Tests basic database connectivity and collection access
- **check_users.py**: Validates user data structure and role assignments
- **check_faculty_requests.py**: Verifies faculty unavailability request system
- **check_teacher_faculty.py**: Checks faculty and department assignments
- **check_pending_requests.py**: Monitors pending request status and workflow

### API Testing Scripts
- **test_frontend_api.py**: Comprehensive testing of all API endpoints
- **test_consolidated_system.py**: End-to-end testing of integrated systems
- **test_faculty_availability.py**: Specific testing of faculty availability features
- **test_new_system.py**: Testing of newly implemented functionality

### Utility Scripts
- **create_test_data.py**: Generates realistic test data for development
- **assign_faculty_departments.py**: Assigns faculty and department fields to users

## Benefits of This Organization

1. **Clear Structure**: Easy to find and understand script purposes
2. **Maintainability**: Organized scripts are easier to maintain and update
3. **Reusability**: Testing scripts can be reused for future development
4. **Documentation**: Centralized documentation for easy reference
5. **Clean Root**: Removes clutter from main project directory

## Next Steps

1. Execute the reorganization plan
2. Test that moved scripts still work correctly
3. Update any hardcoded paths in scripts
4. Create comprehensive README files
5. Update project documentation to reference new structure 