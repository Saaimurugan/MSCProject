# Implementation Plan: Simplify Quiz Application

## Overview

This implementation plan outlines the steps to simplify the quiz application by removing authentication, user management, admin, and reporting functionality. The work is organized into backend cleanup, database model updates, Lambda function modifications, frontend cleanup, and integration testing.

## Tasks

- [x] 1. Remove backend modules and update shared utilities
  - [x] 1.1 Delete unused backend modules
    - Delete `backend/admin/` directory and all files
    - Delete `backend/auth/` directory and all files
    - Delete `backend/profile/` directory and all files
    - Delete `backend/reports/` directory and all files
    - Delete `backend/shared/auth_utils.py`
    - _Requirements: 6.5_
  
  - [x] 1.2 Update database models to remove User model
    - Modify `backend/shared/db_models.py` to remove User class
    - Remove user-related imports and methods
    - Update Template model to remove created_by references
    - Update QuizResult model to replace user_id with session_id
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [x] 1.3 Write property test for database models
    - **Property 12: Template Timestamp Presence**
    - **Property 14: Session Identifier Presence**
    - **Validates: Requirements 5.3, 9.4**

- [x] 2. Modify template Lambda functions
  - [x] 2.1 Update create_template Lambda function
    - Remove authentication/authorization checks
    - Remove created_by field from template creation
    - Add validation for non-empty title, subject, course
    - Add validation for questions (min 2 options, correct answer required)
    - Update error responses with appropriate status codes
    - _Requirements: 1.1, 1.3, 1.4, 1.5_
  
  - [x] 2.2 Write property tests for template creation
    - **Property 1: Question Validation**
    - **Property 3: Template Field Validation**
    - **Validates: Requirements 1.3, 1.5**
  
  - [x] 2.3 Write property test for template persistence
    - **Property 2: Template Persistence Round-Trip**
    - **Validates: Requirements 1.4**
  
  - [x] 2.4 Create get_template_by_id Lambda function
    - Create new file `backend/templates/get_template_by_id.py`
    - Implement function to retrieve template by ID with all questions
    - Handle template not found errors (404)
    - Return template with all question details
    - _Requirements: 7.3_
  
  - [x] 2.5 Write unit tests for get_template_by_id
    - Test successful retrieval
    - Test not found error
    - Test invalid template_id format
    - _Requirements: 7.3_
  
  - [x] 2.6 Update get_templates Lambda function
    - Remove authentication checks
    - Ensure filtering by subject/course works correctly
    - Update response format to include question_count
    - _Requirements: 2.1, 2.3, 7.2_
  
  - [x] 2.7 Write property test for template filtering
    - **Property 5: Template Filtering Correctness**
    - **Validates: Requirements 2.3**

- [x] 3. Checkpoint - Ensure template functions work correctly
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Modify quiz Lambda functions
  - [x] 4.1 Update take_quiz Lambda function
    - Remove authentication checks
    - Ensure questions don't reveal correct answers in response
    - Update response format
    - _Requirements: 3.2, 7.3_
  
  - [x] 4.2 Write property test for question display
    - **Property 6: Question Display Concealment**
    - **Validates: Requirements 3.2**
  
  - [x] 4.3 Update submit_quiz Lambda function
    - Remove authentication and user_id requirements
    - Generate session_id if not provided
    - Validate all questions are answered
    - Calculate score correctly (percentage)
    - Store result with session_id instead of user_id
    - Include completed_at timestamp
    - Return detailed results with correctness per question
    - _Requirements: 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 5.4, 9.4_
  
  - [x] 4.4 Write property tests for quiz submission
    - **Property 7: Score Calculation Accuracy**
    - **Property 8: Complete Answer Validation**
    - **Property 9: Score Range Validity**
    - **Validates: Requirements 3.4, 3.5, 4.1**
  
  - [x] 4.5 Write property test for result persistence
    - **Property 11: Quiz Result Persistence Round-Trip**
    - **Property 13: Quiz Result Timestamp Presence**
    - **Validates: Requirements 4.4, 5.4**
  
  - [x] 4.6 Write unit tests for submit_quiz edge cases
    - Test incomplete answers rejection
    - Test invalid template_id
    - Test invalid answer indices
    - Test database error handling
    - _Requirements: 3.5, 7.5_

- [x] 5. Checkpoint - Ensure quiz functions work correctly
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Remove frontend components and services
  - [x] 6.1 Delete unused frontend components
    - Delete `frontend/src/components/admin/` directory
    - Delete `frontend/src/components/auth/` directory
    - Delete `frontend/src/components/profile/` directory
    - Delete `frontend/src/components/reports/` directory
    - Delete `frontend/src/services/auth.js`
    - _Requirements: 6.6_
  
  - [x] 6.2 Update API service
    - Modify `frontend/src/services/api.js` to remove authentication headers
    - Remove token management code
    - Update API endpoints to match new backend structure
    - Add endpoint for get_template_by_id
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 7. Repurpose and update frontend components
  - [x] 7.1 Repurpose Dashboard as landing page
    - Modify `frontend/src/components/dashboard/Dashboard.js`
    - Remove user-specific content
    - Add navigation to template creation and quiz taking
    - Display available templates
    - _Requirements: 8.1, 8.2_
  
  - [-] 7.2 Update template creation interface
    - Ensure form validates title, subject, course as non-empty
    - Ensure question builder validates min 2 options per question
    - Ensure correct answer must be designated
    - Add visual feedback for validation errors
    - _Requirements: 1.1, 1.2, 1.3, 1.5_
  
  - [~] 7.3 Update quiz taking interface
    - Remove authentication requirements
    - Ensure questions don't show correct answers during quiz
    - Validate all questions answered before submission
    - Display results with score percentage and detailed feedback
    - Show correct answers in results view
    - _Requirements: 3.1, 3.2, 3.3, 3.5, 4.1, 4.2, 4.3_
  
  - [~] 7.4 Update App.js routing
    - Remove authentication-protected routes
    - Remove login/signup routes
    - Update navigation to simplified structure
    - Set landing page as default route
    - _Requirements: 8.1, 8.2_

- [ ] 8. Update API Gateway configuration
  - [~] 8.1 Remove unused API endpoints
    - Remove all auth endpoints (login, signup)
    - Remove all profile endpoints
    - Remove all admin endpoints
    - Remove all reports endpoints
    - _Requirements: 6.5_
  
  - [~] 8.2 Update remaining endpoints
    - Remove authorizers from template endpoints
    - Remove authorizers from quiz endpoints
    - Add new get_template_by_id endpoint
    - Update CORS configuration if needed
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 9. Integration testing and deployment
  - [~] 9.1 Write integration tests for complete flows
    - Test create template → retrieve template flow
    - Test retrieve templates → take quiz → submit quiz → view results flow
    - Test template filtering
    - Test error scenarios end-to-end
    - _Requirements: 1.4, 2.3, 3.4, 4.4_
  
  - [~] 9.2 Update deployment scripts
    - Update `deploy-api.ps1` to remove unused Lambda functions
    - Update `deploy-frontend.ps1` if needed
    - Update `create-dynamodb-tables.ps1` to remove Users table creation
    - _Requirements: 9.1_
  
  - [~] 9.3 Test backward compatibility
    - Verify existing templates with created_by field still work
    - Verify existing quiz results with user_id field still work
    - Ensure no data migration is required
    - _Requirements: 9.5_

- [ ] 10. Final checkpoint - Complete system validation
  - Ensure all tests pass, ask the user if questions arise.
  - Verify all removed modules are deleted
  - Verify all API endpoints work without authentication
  - Verify frontend loads without login requirement

## Notes

- Tasks marked with `*` are optional and can be skipped for faster implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties using Hypothesis framework
- Unit tests validate specific examples and edge cases
- Integration tests verify end-to-end flows work correctly
- Backward compatibility is maintained - no data migration required
