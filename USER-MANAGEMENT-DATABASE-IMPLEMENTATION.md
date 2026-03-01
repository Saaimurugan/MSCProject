# User Management Database Implementation

## Overview
The user management system is fully implemented with database-backed storage and admin-only CRUD operations.

## Architecture

### Database Layer
- **DynamoDB Table**: `msc-evaluate-users-{environment}`
- **Primary Key**: `user_id` (String)
- **Billing Mode**: PAY_PER_REQUEST (on-demand)

### User Schema
```json
{
  "user_id": "uuid",
  "username": "string (unique, lowercase)",
  "password": "string (plain text - should be hashed in production)",
  "email": "string (lowercase)",
  "role": "admin | tutor | student",
  "full_name": "string",
  "is_active": "boolean",
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp"
}
```

## Backend Implementation

### Lambda Function: `msc-evaluate-user-crud-{environment}`
**File**: `backend/users/user_crud.py`

#### Endpoints

| Method | Path | Access | Description |
|--------|------|--------|-------------|
| POST | `/users/login` | Public | User authentication |
| GET | `/users` | Admin Only | List all users with optional filters |
| GET | `/users/{user_id}` | Admin Only | Get specific user details |
| POST | `/users` | Admin Only | Create new user |
| PUT | `/users/{user_id}` | Admin Only | Update existing user |
| DELETE | `/users/{user_id}` | Admin Only | Delete user |

#### Admin Access Control
- All CRUD operations (except login) require admin role
- Verified via `X-User-Role` header
- Returns 403 Forbidden if non-admin attempts access

#### Features
- Username uniqueness validation
- Role validation (admin, tutor, student)
- Active/inactive user status
- Query filtering by role and status
- Password excluded from all responses
- Full CORS support

## Frontend Implementation

### User Management Component
**File**: `frontend/src/components/users/UserManagement.js`

#### Features
- List all users with role filtering
- Create new users (admin only)
- Edit existing users (admin only)
- Delete users with confirmation (admin only)
- Active/inactive status toggle
- Modal-based forms
- Real-time error handling

#### Access Control
- Component only accessible to admin users
- API calls automatically include `X-User-Role` header
- Graceful error handling for unauthorized access

### API Service
**File**: `frontend/src/services/api.js`

```javascript
// Automatic role injection
api.interceptors.request.use((config) => {
  const user = JSON.parse(localStorage.getItem('user'));
  if (user.role) {
    config.headers['X-User-Role'] = user.role;
  }
  return config;
});

// User API methods
usersAPI.getUsers(filters)
usersAPI.getUserById(userId)
usersAPI.createUser(userData)
usersAPI.updateUser(userId, userData)
usersAPI.deleteUser(userId)
```

## Authentication Flow

1. User submits login credentials
2. Backend queries DynamoDB by username
3. Password verification (plain text comparison)
4. User info stored in localStorage
5. Role included in all subsequent API requests via header

## Default Users

Created by `backend/users/init_users.py`:

| Username | Password | Role | Email |
|----------|----------|------|-------|
| admin | admin123 | admin | admin@example.com |
| tutor | tutor123 | tutor | tutor@example.com |
| student | student123 | student | student@example.com |

## Deployment

### Infrastructure
CloudFormation template (`cloudformation/deploy-stack.yaml`) includes:
- DynamoDB Users table
- Lambda function with DynamoDB permissions
- API Gateway endpoints with CORS
- IAM roles and policies

### Initialize Users
```bash
# After stack deployment
python backend/users/init_users.py msc-evaluate-users-dev
```

Or use deployment script:
```bash
./cloudformation/deploy-users.sh
```

## Security Considerations

### Current Implementation
✅ Admin-only CRUD operations
✅ Role-based access control
✅ Username uniqueness validation
✅ Active/inactive user status
✅ CORS properly configured

### Production Recommendations
⚠️ **Password Hashing**: Currently using plain text passwords
   - Implement bcrypt or similar hashing
   - Add salt for additional security

⚠️ **JWT Tokens**: Replace header-based auth with JWT
   - Implement token expiration
   - Add refresh token mechanism

⚠️ **API Gateway Authorizer**: Add Lambda authorizer
   - Validate tokens at gateway level
   - Reduce Lambda invocations for unauthorized requests

⚠️ **Rate Limiting**: Add throttling
   - Prevent brute force attacks
   - Protect against DDoS

⚠️ **Audit Logging**: Track user operations
   - Log all CRUD operations
   - Monitor suspicious activity

## Testing

### Test User CRUD Operations

```bash
# Login (Public)
curl -X POST https://api-url/dev/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# List Users (Admin Only)
curl -X GET https://api-url/dev/users \
  -H "X-User-Role: admin"

# Create User (Admin Only)
curl -X POST https://api-url/dev/users \
  -H "Content-Type: application/json" \
  -H "X-User-Role: admin" \
  -d '{
    "username":"newuser",
    "password":"pass123",
    "email":"new@example.com",
    "role":"student",
    "full_name":"New User"
  }'

# Update User (Admin Only)
curl -X PUT https://api-url/dev/users/{user_id} \
  -H "Content-Type: application/json" \
  -H "X-User-Role: admin" \
  -d '{"email":"updated@example.com","is_active":false}'

# Delete User (Admin Only)
curl -X DELETE https://api-url/dev/users/{user_id} \
  -H "X-User-Role: admin"
```

### Test Non-Admin Access (Should Fail)

```bash
# Attempt CRUD as student (should return 403)
curl -X GET https://api-url/dev/users \
  -H "X-User-Role: student"
```

## File Structure

```
backend/users/
├── user_crud.py          # Lambda function with CRUD operations
├── init_users.py         # Script to create default users
└── README.md             # User management documentation

frontend/src/
├── components/users/
│   ├── UserManagement.js    # User management UI component
│   └── UserManagement.css   # Styling
├── components/auth/
│   ├── Login.js             # Login component
│   └── Login.css            # Login styling
└── services/
    └── api.js               # API service with user endpoints

cloudformation/
├── deploy-stack.yaml     # Infrastructure definition
├── deploy-users.sh       # User initialization script
└── deploy-users.ps1      # Windows user initialization
```

## Summary

✅ **Database-Backed**: All users stored in DynamoDB
✅ **Admin-Only CRUD**: Create, Update, Delete restricted to admins
✅ **Role-Based Access**: Three roles (admin, tutor, student)
✅ **Full CRUD Operations**: Complete create, read, update, delete functionality
✅ **Frontend UI**: User-friendly management interface
✅ **API Integration**: RESTful API with proper error handling
✅ **Infrastructure as Code**: CloudFormation deployment
✅ **Default Users**: Pre-configured demo accounts

The system is production-ready with the exception of password hashing and JWT token implementation, which should be added before production deployment.
