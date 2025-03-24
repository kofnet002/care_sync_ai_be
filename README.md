# CareSyncAI - Hospital Management System API

CareSyncAI is a Django REST Framework-based API for managing hospital operations, focusing on patient-doctor relationships, reminders, and actionable health plans.

## Features

- **User Management**
  - Patient & Doctor registration
  - JWT authentication
  - Role-based access control

- **Patient-Doctor Management**
  - Doctor selection by patients
  - Doctor view of assigned patients
  - Secure note sharing

- **Reminder System**
  - Automated medication reminders
  - Check-in tracking
  - Dynamic scheduling with missed dose handling

- **Action Plans**
  - AI-generated health plans
  - Customizable schedules
  - End-to-end encrypted notes

## Basic Setup

1. Clone the repository
    ```bash
    https://github.com/kofnet002/care_sync_ai_be
    ```
    
```You need to be an admin before see your endpoints```

## Approach 1 of accessing application

1. Create virtual environment:
    ```bash
    python3 -m venv venv
    ```
2. Activate virtual environment:
    ```bash
    . venv/bin/activate
    ```
3. Create an `.env` file in the root folder and copy the `keys` from `.env.example` file and add the necessary `values`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run migrations:
   ```bash
   python3 manage.py migrate
   ```
6. Start development server:
   ```bash
   python3 manage.py runserver
   ```
7. Create superuser to access the admin dashboard
    ```bash
    python3 manage.py createsuperuser
    ```
8. Access project and admin dashboard using the following links respectively
  `localhost:8000` & `localhost:8000/admin/`


## Apporoach 2 (Docker Approach)


1. Running using docker approach
    ```bash
    sudo docker compose -f docker-compose.yml up -d --build
    ```
2. Make migrations
    ```bash
    sudo docker compose -f docker-compose.yml exec web python manage.py migrate
    ```
3. Create superuser
    ```bash
    sudo docker compose -f docker-compose.yml exec web python manage.py createsuperuser
    ```
4. Then access app on `localhost`

5. View logs
    ```bash
    sudo docker compose -f docker-compose.yml logs -f
    ```




## API Documentation

Access the interactive API docs at:
- Swagger UI: `/`
<!-- - ReDoc: `/api/schema/redoc/` -->

## Key Endpoints

- **Authentication**
  - POST `/api/v1/auth/register/` - User registration
  - POST `/api/v1/auth/login/` - User login
  - POST `/api/v1/auth/superuser/register/` - Create superuser
  - POST `/api/v1/auth/refresh/` - Refresh JWT token


- **Patient-Doctor**
  - GET `/api/v1/doctors/` - List available doctors
  - POST `/api/v1/doctors/assign/` - Assign doctor to patient
  - GET `/api/v1/doctors/my-patients/` - Get doctor's patients

- **Reminders**
  - POST `/api/v1/reminders/{id}/checkin/` - Check-in for reminder
  - GET `/api/v1/reminders/` - List reminders

## Technology Stack

- Django REST Framework
- PostgreSQL
- Redis & Celery
- JWT Authentication
- DRF Spectacular (API docs)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## Documentation & Justification

### Authentication
- **JWT Authentication** was chosen for:
  - Stateless server architecture
  - Scalability
  - Secure token-based authentication
  - Easy integration with frontend frameworks

### Encryption
- **End-to-End Encryption** implemented using:
  - RSA for key management (2048-bit)
  - Fernet (AES) for content encryption
  - Separate encryption for doctor and patient
  - Ensures only authorized parties can access notes

### Scheduling Strategy
- **Dynamic Reminder System** designed to:
  - Handle missed check-ins gracefully
  - Maintain proper medication spacing
  - Automatically extend plans for missed doses
  - Send persistent reminders until check-in
  - Use Celery for background task scheduling

### Data Storage
- **PostgreSQL** selected because:
  - ACID compliance
  - Robust data integrity
  - Excellent support for complex queries
  - JSON field support for flexible data storage

### API Design
- **RESTful Architecture** implemented with:
  - Resource-based endpoints
  - Standard HTTP methods
  - JSON payloads
  - Versioned API (v1)
  - Comprehensive documentation using OpenAPI

### Task Management
- **Celery with Redis** used for:
  - Asynchronous task execution
  - Periodic task scheduling
  - Reliable message queuing
  - Scalable background processing

### Security Measures
- **Best Practices** implemented:
  - Password hashing with PBKDF2
  - Secure JWT token handling
  - Role-based access control
  - Input validation and sanitization
  - Rate limiting for API endpoints
