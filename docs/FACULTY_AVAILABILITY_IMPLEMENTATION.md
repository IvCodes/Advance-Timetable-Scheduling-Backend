# Faculty Unavailability Management System

## Overview

This implementation provides a comprehensive faculty unavailability management system with proper approval workflow, notification system, and substitute assignment functionality. The system allows faculty members to request time off, admins to review and approve/deny requests, assign substitutes, and ensures all parties are notified of changes.

## Features

### ✅ Core Functionality
- **Faculty Request Submission**: Faculty can submit unavailability requests with reason and type
- **Admin Approval Workflow**: Admins can approve/deny requests with notes
- **Substitute Assignment**: Admins can assign available faculty as substitutes
- **Real-time Notifications**: All parties receive notifications for status changes
- **Statistics Dashboard**: Comprehensive statistics for admin oversight
- **Role-based Access Control**: Proper permissions for different user roles

### ✅ API Endpoints

#### Faculty Availability Management (`/api/v1/faculty-availability/`)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|---------|
| POST | `/unavailability-requests` | Submit new unavailability request | Faculty/Admin |
| GET | `/unavailability-requests` | Get unavailability requests (filtered by role) | Faculty/Admin |
| GET | `/unavailability-requests/pending` | Get pending requests | Admin only |
| PUT | `/unavailability-requests/{request_id}/status` | Approve/deny request | Admin only |
| DELETE | `/unavailability-requests/{request_id}` | Cancel pending request | Faculty/Admin |
| GET | `/faculty/{faculty_id}/unavailable-dates` | Get approved unavailable dates | Faculty/Admin |
| GET | `/statistics` | Get availability statistics | Admin only |
| GET | `/available-substitutes` | Get available substitutes for date | Admin only |

#### Notifications (`/api/v1/`)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|---------|
| GET | `/notifications` | Get user notifications | All authenticated |
| PUT | `/notifications/{notification_id}/read` | Mark notification as read | All authenticated |
| GET | `/notifications/unread-count` | Get unread notification count | All authenticated |

## Data Models

### UnavailabilityRecord
```python
class UnavailabilityRecord(MongoBaseModel):
    faculty_id: str
    date: date
    reason: Optional[str] = None
    unavailability_type: UnavailabilityType = UnavailabilityType.OTHER
    status: UnavailabilityStatus = UnavailabilityStatus.PENDING
    substitute_id: Optional[str] = None
    substitute_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    approved_by: Optional[str] = None
    admin_notes: Optional[str] = None
```

### Enums
- **UnavailabilityStatus**: `PENDING`, `APPROVED`, `DENIED`
- **UnavailabilityType**: `SICK_LEAVE`, `PERSONAL_LEAVE`, `CONFERENCE`, `TRAINING`, `EMERGENCY`, `OTHER`

## Workflow

### 1. Faculty Submits Request
```python
# Faculty submits unavailability request
POST /api/v1/faculty-availability/unavailability-requests
{
    "faculty_id": "FA0000001",
    "date": "2025-03-15",
    "reason": "Medical appointment",
    "unavailability_type": "personal_leave"
}
```

### 2. Admin Receives Notification
- System automatically creates notification for all admins
- Notification includes faculty name, date, and reason
- Admin can view pending requests in dashboard

### 3. Admin Reviews and Decides
```python
# Admin approves request with substitute
PUT /api/v1/faculty-availability/unavailability-requests/{request_id}/status
{
    "status": "approved",
    "substitute_id": "FA0000002",
    "admin_notes": "Approved - substitute assigned"
}
```

### 4. Notifications Sent
- **Faculty**: Receives approval/denial notification
- **Substitute**: Receives assignment notification (if assigned)
- **Students**: Can receive timetable update notifications (future enhancement)

## Database Collections

### faculty_unavailability
```javascript
{
    "_id": ObjectId,
    "faculty_id": "FA0000001",
    "date": "2025-03-15",
    "reason": "Medical appointment",
    "unavailability_type": "personal_leave",
    "status": "pending",
    "substitute_id": null,
    "substitute_name": null,
    "created_at": ISODate,
    "updated_at": ISODate,
    "approved_by": null,
    "admin_notes": null
}
```

### notifications
```javascript
{
    "_id": ObjectId,
    "title": "New Faculty Unavailability Request",
    "message": "John Doe has requested to be unavailable on 2025-03-15 - Medical appointment",
    "timestamp": ISODate,
    "type": "info",
    "category": "faculty_unavailability",
    "read": false,
    "target_roles": ["admin"],
    "data": {
        "faculty_id": "FA0000001",
        "date": "2025-03-15",
        "action_required": true
    }
}
```

## Testing

### Prerequisites
1. Server running on `localhost:8000`
2. Admin user: `username=admin`, `password=Test123`
3. Faculty users with `password=Test123`

### Run Test Script
```bash
python test_faculty_availability.py
```

The test script demonstrates the complete workflow:
1. Faculty submits unavailability request
2. Admin receives notification
3. Admin approves request and assigns substitute
4. All parties receive appropriate notifications
5. Statistics are updated

## Integration Points

### Frontend Integration
The system is designed to integrate with the existing frontend components:

1. **Faculty Dashboard**: 
   - Calendar component for marking unavailable dates
   - Request status tracking
   - Notification panel

2. **Admin Dashboard**:
   - Pending requests management
   - Substitute assignment interface
   - Statistics overview

### Existing System Integration
- **User Management**: Uses existing user authentication and role system
- **Notification System**: Extends existing notification infrastructure
- **Database**: Uses existing MongoDB collections and connection

## Security Features

1. **Role-based Access Control**: Faculty can only manage their own requests
2. **Authentication Required**: All endpoints require valid JWT tokens
3. **Input Validation**: Comprehensive validation using Pydantic models
4. **Permission Checks**: Proper authorization checks for admin-only operations

## Future Enhancements

1. **Timetable Integration**: Automatically update timetables when substitutes are assigned
2. **Recurring Unavailability**: Support for recurring unavailability patterns
3. **Email Notifications**: Send email notifications in addition to in-app notifications
4. **Mobile App Support**: API is ready for mobile app integration
5. **Advanced Analytics**: More detailed reporting and analytics
6. **Conflict Detection**: Detect and prevent scheduling conflicts

## Error Handling

The system includes comprehensive error handling:
- **404 Errors**: When requests or users are not found
- **403 Errors**: When users lack proper permissions
- **400 Errors**: When requests already exist or invalid data is provided
- **Validation Errors**: Detailed validation error messages

## Performance Considerations

1. **Database Indexing**: Indexes on faculty_id, date, and status fields
2. **Pagination**: Support for paginated results in list endpoints
3. **Caching**: Notification counts and statistics can be cached
4. **Async Operations**: All database operations are asynchronous

## Monitoring and Logging

- All operations are logged with appropriate log levels
- Failed operations include detailed error information
- Success operations include relevant metadata for auditing

## Conclusion

This faculty unavailability management system provides a robust, scalable solution for managing faculty availability with proper approval workflows, notifications, and substitute assignments. The system is designed to integrate seamlessly with the existing timetable management system while providing a foundation for future enhancements. 