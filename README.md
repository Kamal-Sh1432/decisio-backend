# Deciso – Backend API

## The Deciso backend powers the decision-support engine by delivering secure APIs, KPI computation logic, predictive scoring, 
## and structured data services to the frontend dashboards.

This backend is designed as a scalable analytics service layer, combining business rule enforcement, 
SQL-driven validation, and AI-based intelligence.

🚀 Tech Stack

Python 3.x

FastAPI / Flask

Neon DB (Serverless PostgreSQL)

SQLAlchemy / Psycopg2

Pandas / NumPy

Scikit-learn (Predictive Modeling)

JWT Authentication

Gunicorn / Uvicorn (Production Server)

🗄 Database – Neon DB (Serverless PostgreSQL)

Deciso uses Neon DB, a serverless PostgreSQL platform, for scalable, cloud-native database operations.

Why Neon DB?

Serverless architecture (auto-scaling compute)

Branching support for safe experimentation

Built-in high availability

Separation of compute and storage

Optimized for modern cloud deployments

Connection Configuration

Environment variable setup:

DATABASE_URL=postgresql+psycopg2://user:password@ep-xxxxxx.neon.tech/deciso?sslmode=require

⚠ SSL mode is required for Neon connections.

🏗 Architecture Overview
backend/
│
├── app/
│   ├── routes/
│   ├── services/
│   ├── models/
│   ├── schemas/
│   ├── utils/
│   ├── config/
│   └── __init__.py
│
├── migrations/
├── requirements.txt
├── run.py
└── README.md
Layer Responsibilities

Routes Layer

Exposes REST APIs

Validates request payloads

Returns structured JSON responses

Service Layer

KPI computation logic

Business rule enforcement

Predictive scoring integration

Revenue and utilization calculations

Model Layer

PostgreSQL table definitions

ORM mappings

Utility Layer

Logging

Error handling

Response standardization

⚙️ Setup Instructions
1️⃣ Create Virtual Environment
python -m venv venv
source venv/bin/activate     # Mac/Linux
venv\Scripts\activate        # Windows
2️⃣ Install Dependencies
pip install -r requirements.txt
3️⃣ Configure Environment Variables

Create a .env file:

SECRET_KEY=your_secret_key
DATABASE_URL=postgresql+psycopg2://user:password@ep-xxxxxx.neon.tech/deciso?sslmode=require
JWT_SECRET=your_jwt_secret
MODEL_PATH=models/no_show_model.pkl
▶️ Run Development Server

For Flask:

python run.py

For FastAPI:

uvicorn app.main:app --reload

Default URL:

http://localhost:8000
📊 Core Functional Modules
1️⃣ Authentication Module

JWT-based authentication

Role-based API access

Token validation middleware

2️⃣ KPI Engine

The KPI engine performs:

No-show rate calculation

Revenue leakage estimation

Doctor utilization %

Capacity analysis

Appointment-level aggregation

All metrics are computed at granular levels before aggregation to avoid distortion.

3️⃣ Predictive Analytics Engine

Loads trained ML model

Scores appointment-level no-show probability

Outputs risk score (0–1)

Categorizes into risk buckets

Stores prediction output in Neon DB

Exposes APIs for dashboard consumption

4️⃣ Decision Rule Engine

Transforms prediction into action signals:

Examples:

Risk > 0.7 → Trigger reminder intervention

Medium risk + high revenue slot → Priority follow-up

Overutilized doctor + high-risk slot → Suggest rescheduling

This ensures analytics drives operational impact.

🔄 Sample API Endpoints
Authentication
POST /api/auth/login
Executive KPIs
GET /api/kpis/executive-overview
Revenue Leakage
GET /api/kpis/revenue-leakage
Doctor Utilization
GET /api/kpis/doctor-utilization
AI Prediction
POST /api/predict/no-show
🧪 Data Validation & Integrity

Before exposing metrics to dashboards:

Null value checks

Referential integrity validation

Duplicate appointment checks

Revenue reconciliation

Slot-level aggregation verification

This ensures executive dashboards reflect validated business reality.

📈 Performance Optimization

Indexed frequently filtered columns

Optimized SQL joins

Query-level caching

Connection pooling

Neon auto-scaling compute optimization

🔐 Security Considerations

SSL-enforced database connections

JWT authentication

Role-based authorization

Environment-based configuration

Sanitized error responses

📊 Logging & Monitoring

Structured application logging

API latency tracking

Database query performance monitoring

Error classification and alert readiness

🧠 Scalability Roadmap

Planned enhancements:

Multi-tenant architecture

Async background tasks (Celery / Redis)

Automated model retraining pipeline

Feature engineering pipeline

Real-time event processing

👨‍💻 Author

Kamal Sharma
Senior Business Analyst | Analytics Consultant

The Deciso backend reflects enterprise-grade analytics delivery, combining business logic, serverless PostgreSQL architecture (Neon DB), 
and predictive intelligence to enable structured decision-making.
