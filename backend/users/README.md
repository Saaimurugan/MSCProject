# User Management Backend

This module handles user authentication and CRUD operations for the MSC Evaluate application.

## Features

- User authentication (login)
- User CRUD operations (Create, Read, Update, Delete)
- Role-based access control (Admin only for CRUD)
- Support for three user roles: admin, tutor, student

## API Endpoints

### Public Endpoints

#### POST /users/login
Login with username and password.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "user_id": "uuid",
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "full_name": "System Administrator",
    "is_active": true
  }
}
```

### Admin-Only Endpoints

All endpoints below require `X-User-Role: admin` header.

#### GET /users
List all users with optional filtering.

**Query Parameters:**
- `role` (optional): Filter by role (admin, tutor, student)
- `is_active` (optional): Filter by active status (true, false)

**Response:**
```json
{
  "users": [...],
  "count": 10
}
```

#### GET /users/{user_id}
Get a specific user by ID.

**Response:**
```json
{
  "user_id": "uuid",
  "username": "student",
  "email": "student@example.com",
  "role": "student",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

#### POST /users
Create a new user.

**Request:**
```json
{
  "username": "newuser",
  "password": "password123",
  "email": "newuser@example.com",
  "role": "student",
  "full_name": "New User",
  "is_active": true
}
```

**Response:**
```json
{
  "message": "User created successfully",
  "user": {...}
}
```

#### PUT /users/{user_id}
Update an existing user.

**Request:**
```json
{
  "email": "updated@example.com",
  "role": "tutor",
  "full_name": "Updated Name",
  "is_active": false
}
```

**Response:**
```json
{
  "message": "User updated successfully",
  "user": {...}
}
```

#### DELETE /users/{user_id}
Delete a user.

**Response:**
```json
{
  "message": "User deleted successfully",
  "user_id": "uuid"
}
```

## Deployment

### 1. Deploy Infrastructure
The CloudFormation stack will create the Users table and Lambda function.

### 2. Package Lambda Function
```bash
cd backend/users
zip user_crud.zip user_crud.py
```

### 3. Update Lambda Function
```bash
aws lambda update-function-code \
  --function-name msc-evaluate-user-crud-dev \
  --zip-file fileb://user_crud.zip
```

### 4. Initialize Default Users
```bash
python init_users.py msc-evaluate-users-dev
```

## Default Users

After initialization, these users are available:

| Username | Password    | Role    |
|----------|-------------|---------|
| admin    | admin123    | admin   |
| tutor    | tutor123    | tutor   |
| student  | student123  | student |

## Security Notes

⚠️ **Important for Production:**

1. **Password Hashing**: Currently passwords are stored in plain text. In production, use bcrypt or similar:
   ```python
   import bcrypt
   hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
   ```

2. **JWT Tokens**: Implement proper JWT token authentication instead of header-based role checking.

3. **Environment Variables**: Store sensitive data in AWS Secrets Manager or Parameter Store.

4. **Input Validation**: Add comprehensive input validation and sanitization.

5. **Rate Limiting**: Implement rate limiting on login endpoint to prevent brute force attacks.

## User Roles

- **Admin**: Full access to all features including user management
- **Tutor**: Can create/edit templates and view student reports
- **Student**: Can take quizzes and view personal results
