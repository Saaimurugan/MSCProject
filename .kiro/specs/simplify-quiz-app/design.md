# Design Document: Simplify Quiz Application

## Overview

This design outlines the simplification of the quiz application by removing all authentication, user management, admin, and reporting functionality. The simplified system will consist of two core features: template creation and quiz taking. The application will be publicly accessible without requiring user accounts.

The architecture will maintain the existing AWS Lambda + DynamoDB backend with a React frontend, but with significantly reduced complexity by removing 4 of the 7 backend modules and 4 of the 6 frontend component groups.

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│  React Frontend │
│                 │
│  - Home/Landing │
│  - Templates    │
│  - Quiz Taking  │
└────────┬────────┘
         │ HTTPS/REST
         ▼
┌─────────────────┐
│   API Gateway   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│      Lambda Functions           │
│                                  │
│  - create_template              │
│  - get_templates                │
│  - get_template_by_id (new)     │
│  - submit_quiz                  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│         DynamoDB                │
│                                  │
│  - Templates Table              │
│  - QuizResults Table            │
└─────────────────────────────────┘
```

### Removed Components

**Backend Modules to Remove:**
- `backend/admin/` - All user management functions
- `backend/auth/` - Login and signup functions
- `backend/profile/` - Profile and password management
- `backend/reports/` - All reporting functions
- `backend/shared/auth_utils.py` - Authentication utilities

**Frontend Components to Remove:**
- `frontend/src/components/admin/` - Admin interface
- `frontend/src/components/auth/` - Login and signup forms
- `frontend/src/components/profile/` - Profile management
- `frontend/src/components/reports/` - Reports display
- `frontend/src/services/auth.js` - Authentication service

**Database Tables to Remove:**
- Users table (msc-evaluate-users-dev)

### Retained Components

**Backend:**
- `backend/templates/create_template.py` - Modified to remove user authentication
- `backend/templates/get_templates.py` - Unchanged
- `backend/quiz/submit_quiz.py` - Modified to remove user_id requirement
- `backend/quiz/take_quiz.py` - Modified to remove authentication
- `backend/shared/db_models.py` - Simplified to remove User model

**Frontend:**
- `frontend/src/components/dashboard/` - Repurposed as main landing page
- `frontend/src/components/quiz/` - Quiz taking interface
- `frontend/src/services/api.js` - Simplified API client

## Components and Interfaces

### Backend Components

#### 1. Template Management

**create_template Lambda**
```python
def lambda_handler(event, context):
    """
    Create a new quiz template
    
    Input:
        {
            "title": str,
            "subject": str,
            "course": str,
            "questions": [
                {
                    "question_text": str,
                    "options": [str],
                    "correct_answer": int  # index of correct option
                }
            ]
        }
    
    Output:
        {
            "statusCode": 200,
            "body": {
                "template_id": str,
                "message": "Template created successfully"
            }
        }
    """
```

**get_templates Lambda**
```python
def lambda_handler(event, context):
    """
    Retrieve all templates or filter by subject/course
    
    Input (query parameters):
        {
            "subject": str (optional),
            "course": str (optional)
        }
    
    Output:
        {
            "statusCode": 200,
            "body": {
                "templates": [
                    {
                        "template_id": str,
                        "title": str,
                        "subject": str,
                        "course": str,
                        "question_count": int,
                        "created_at": str
                    }
                ]
            }
        }
    """
```

**get_template_by_id Lambda (New)**
```python
def lambda_handler(event, context):
    """
    Retrieve a specific template with all questions
    
    Input (path parameter):
        template_id: str
    
    Output:
        {
            "statusCode": 200,
            "body": {
                "template_id": str,
                "title": str,
                "subject": str,
                "course": str,
                "questions": [
                    {
                        "question_text": str,
                        "options": [str],
                        "correct_answer": int
                    }
                ]
            }
        }
    """
```

#### 2. Quiz Management

**submit_quiz Lambda**
```python
def lambda_handler(event, context):
    """
    Submit quiz answers and calculate score
    
    Input:
        {
            "template_id": str,
            "session_id": str (optional, generated if not provided),
            "answers": [
                {
                    "question_index": int,
                    "selected_answer": int
                }
            ]
        }
    
    Output:
        {
            "statusCode": 200,
            "body": {
                "result_id": str,
                "total_score": float,  # percentage
                "correct_count": int,
                "total_questions": int,
                "detailed_results": [
                    {
                        "question_index": int,
                        "is_correct": bool,
                        "selected_answer": int,
                        "correct_answer": int
                    }
                ]
            }
        }
    """
```

### Frontend Components

#### 1. Landing Page (Repurposed Dashboard)

The main entry point showing two primary actions:
- Create a new template
- Browse and take quizzes

#### 2. Template Creator

Form interface for creating templates:
- Template metadata (title, subject, course)
- Dynamic question builder
- Add/remove questions
- Add/remove answer options
- Mark correct answer

#### 3. Template Browser

List view of available templates:
- Display template cards with metadata
- Filter by subject/course
- Click to start quiz

#### 4. Quiz Taking Interface

Quiz session interface:
- Display questions with answer options
- Track selected answers
- Submit button
- Results display with score and correct answers

## Data Models

### Templates Table

```python
{
    "template_id": str,          # Primary key (UUID)
    "title": str,                # Template title
    "subject": str,              # Subject area
    "course": str,               # Course name
    "questions": [               # List of questions
        {
            "question_text": str,
            "options": [str],    # List of answer options
            "correct_answer": int # Index of correct option (0-based)
        }
    ],
    "is_active": bool,           # Soft delete flag
    "created_at": str,           # ISO timestamp
    "updated_at": str            # ISO timestamp
}
```

### QuizResults Table

```python
{
    "result_id": str,            # Primary key (UUID)
    "template_id": str,          # Reference to template
    "session_id": str,           # Session identifier (UUID)
    "answers": [                 # User's answers
        {
            "question_index": int,
            "selected_answer": int
        }
    ],
    "total_score": float,        # Percentage score
    "correct_count": int,        # Number of correct answers
    "total_questions": int,      # Total number of questions
    "completed_at": str,         # ISO timestamp
    "created_at": str,           # ISO timestamp
    "updated_at": str            # ISO timestamp
}
```

### Removed Fields

From Templates:
- `created_by` (user_id reference)

From QuizResults:
- `user_id` (user reference)
- `student_name` (no longer needed)
- `student_id` (no longer needed)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Question Validation

*For any* question being added to a template, the system should reject questions with fewer than 2 answer options or without a designated correct answer.

**Validates: Requirements 1.3**

### Property 2: Template Persistence Round-Trip

*For any* valid template, saving it to the database then retrieving it should produce an equivalent template with a unique template_id assigned.

**Validates: Requirements 1.4**

### Property 3: Template Field Validation

*For any* template submission with empty title, subject, or course fields, the system should reject the template and return a validation error.

**Validates: Requirements 1.5**

### Property 4: Template Display Completeness

*For any* template in the system, when rendered for display, the output should contain the template's title, subject, and course information.

**Validates: Requirements 2.2**

### Property 5: Template Filtering Correctness

*For any* subject or course filter applied to template retrieval, all returned templates should match the specified filter criteria.

**Validates: Requirements 2.3**

### Property 6: Question Display Concealment

*For any* question displayed during quiz taking, the rendered output should not reveal which answer option is correct.

**Validates: Requirements 3.2**

### Property 7: Score Calculation Accuracy

*For any* set of quiz answers and corresponding template, the calculated score should equal the percentage of questions answered correctly (correct_count / total_questions * 100).

**Validates: Requirements 3.4**

### Property 8: Complete Answer Validation

*For any* quiz submission where not all questions have been answered, the system should reject the submission and return a validation error.

**Validates: Requirements 3.5**

### Property 9: Score Range Validity

*For any* calculated quiz score, the value should be between 0 and 100 inclusive.

**Validates: Requirements 4.1**

### Property 10: Result Completeness

*For any* quiz result display, the output should indicate correctness status for each question and include the correct answer for each question.

**Validates: Requirements 4.2, 4.3**

### Property 11: Quiz Result Persistence Round-Trip

*For any* quiz result, saving it to the database then retrieving it should produce an equivalent result with a unique result_id and completed_at timestamp.

**Validates: Requirements 4.4**

### Property 12: Template Timestamp Presence

*For any* template stored in the database, it should have both created_at and updated_at timestamp fields with valid ISO format timestamps.

**Validates: Requirements 5.3**

### Property 13: Quiz Result Timestamp Presence

*For any* quiz result stored in the database, it should have a completed_at timestamp field with a valid ISO format timestamp.

**Validates: Requirements 5.4**

### Property 14: Session Identifier Presence

*For any* quiz result stored in the database, it should have a session_id field containing a valid UUID.

**Validates: Requirements 9.4**

## Error Handling

### Input Validation Errors

**Template Creation:**
- Empty or missing required fields (title, subject, course)
- Questions with fewer than 2 options
- Questions without a correct answer designation
- Invalid data types

**Response:**
```json
{
    "statusCode": 400,
    "body": {
        "error": "Validation Error",
        "message": "Specific validation failure message"
    }
}
```

### Quiz Submission Errors

**Invalid Submissions:**
- Missing template_id
- Incomplete answers (not all questions answered)
- Invalid answer indices
- Template not found

**Response:**
```json
{
    "statusCode": 400,
    "body": {
        "error": "Invalid Submission",
        "message": "Specific error message"
    }
}
```

### Database Errors

**DynamoDB Failures:**
- Connection errors
- Table not found
- Write/read failures

**Response:**
```json
{
    "statusCode": 500,
    "body": {
        "error": "Internal Server Error",
        "message": "Unable to process request"
    }
}
```

### Not Found Errors

**Resource Not Found:**
- Template ID doesn't exist
- Result ID doesn't exist

**Response:**
```json
{
    "statusCode": 404,
    "body": {
        "error": "Not Found",
        "message": "Resource not found"
    }
}
```

## Testing Strategy

### Dual Testing Approach

The testing strategy employs both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of valid and invalid inputs
- Edge cases (empty lists, boundary values)
- Error conditions and error message formatting
- Integration between Lambda functions and DynamoDB
- API Gateway integration and CORS configuration

**Property-Based Tests** focus on:
- Universal properties that hold across all valid inputs
- Input validation rules across randomly generated data
- Round-trip properties for data persistence
- Score calculation correctness across various quiz scenarios
- Data structure invariants

### Property-Based Testing Configuration

**Framework:** We will use **Hypothesis** for Python (backend Lambda functions)

**Configuration:**
- Minimum 100 iterations per property test
- Each test tagged with: `# Feature: simplify-quiz-app, Property N: [property description]`
- Custom generators for templates, questions, and quiz answers

**Example Test Structure:**
```python
from hypothesis import given, strategies as st

@given(st.builds(generate_template))
def test_template_persistence_roundtrip(template):
    """
    Feature: simplify-quiz-app, Property 2: Template Persistence Round-Trip
    """
    # Save template
    saved = create_template(template)
    
    # Retrieve template
    retrieved = get_template_by_id(saved['template_id'])
    
    # Assert equivalence
    assert_templates_equivalent(template, retrieved)
```

### Unit Test Coverage

**Backend Lambda Functions:**
- `create_template.py`: Test valid creation, validation errors, database errors
- `get_templates.py`: Test retrieval, filtering, empty results
- `get_template_by_id.py`: Test retrieval, not found errors
- `submit_quiz.py`: Test score calculation, validation, result storage

**Frontend Components:**
- Template Creator: Test form validation, question management
- Template Browser: Test filtering, template selection
- Quiz Taking: Test answer selection, submission
- Results Display: Test score display, answer review

### Integration Testing

**API Integration:**
- Test complete flow: create template → retrieve template → submit quiz → view results
- Test CORS configuration
- Test error responses from API Gateway

**Database Integration:**
- Test DynamoDB table operations
- Test data persistence and retrieval
- Test query and scan operations with filters

### Migration Testing

**Data Migration:**
- Test that existing templates remain accessible
- Test that existing quiz results remain accessible
- Verify removed fields don't break existing data retrieval

## Implementation Notes

### Migration Steps

1. **Backend Cleanup:**
   - Delete `backend/admin/`, `backend/auth/`, `backend/profile/`, `backend/reports/`
   - Remove `backend/shared/auth_utils.py`
   - Update `backend/shared/db_models.py` to remove User model
   - Modify `create_template.py` to remove created_by field
   - Modify `submit_quiz.py` to use session_id instead of user_id
   - Create new `get_template_by_id.py` Lambda function

2. **Frontend Cleanup:**
   - Delete `frontend/src/components/admin/`
   - Delete `frontend/src/components/auth/`
   - Delete `frontend/src/components/profile/`
   - Delete `frontend/src/components/reports/`
   - Delete `frontend/src/services/auth.js`
   - Repurpose `Dashboard.js` as main landing page
   - Update `api.js` to remove authentication headers
   - Update routing to remove auth-protected routes

3. **API Gateway Updates:**
   - Remove endpoints for auth, profile, admin, reports
   - Remove authorizers from remaining endpoints
   - Update CORS configuration if needed

4. **Database Updates:**
   - Keep existing Templates and QuizResults tables
   - No schema migration needed (DynamoDB is schemaless)
   - Existing data remains compatible

### Deployment Considerations

- Deploy backend changes first
- Update API Gateway configuration
- Deploy frontend changes
- Test end-to-end flow
- Monitor for errors in CloudWatch logs

### Backward Compatibility

- Existing templates with `created_by` field will still work (field simply ignored)
- Existing quiz results with `user_id` field will still work (field simply ignored)
- No data migration required
