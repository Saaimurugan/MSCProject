# MSC Evaluate - Serverless Architecture

## Project Structure
```
msc-evaluate/
├── frontend/                    # React app (S3 hosted)
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/           # Login, Signup, ForgotPassword
│   │   │   ├── dashboard/      # Dashboard with cards
│   │   │   ├── quiz/           # Quiz taking interface
│   │   │   ├── template/       # Template creation/editing
│   │   │   ├── profile/        # User profile
│   │   │   └── reports/        # Reports and analytics
│   │   ├── services/           # API calls, auth service
│   │   ├── utils/              # Helpers, constants
│   │   └── App.js
│   └── package.json
├── backend/                     # Lambda functions
│   ├── auth/                   # Authentication functions
│   ├── users/                  # User management
│   ├── templates/              # Template CRUD
│   ├── quiz/                   # Quiz taking and scoring
│   ├── reports/                # Analytics and reports
│   └── shared/                 # Common utilities
├── infrastructure/             # AWS CDK/CloudFormation
└── database/                   # DynamoDB table schemas
```

## User Roles & Permissions
- **Student**: Take quizzes, view results, manage profile
- **Tutor**: Create/edit templates, view student reports
- **Admin**: Full access, user management, system configuration