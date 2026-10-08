# Mentor Book

A comprehensive web-based Mentorship and Student Performance Tracking System built with **Flask**, **SQLAlchemy**, and **PostgreSQL**.

---

## 🚀 Features

- **Mentor Authentication**: Secure login, password reset, and OTP verification via email.
- **Student Profile Management**: View student personal records, demographic details, contact information, and academic program.
- **Semester & Marks Tracking**: Detailed semester-wise subject grades, internal assessments (CIA), and semester end exams (SEE).
- **Parent-Teacher Meetings**: Record and track meeting schedules, discussion agendas, and remarks.
- **Role-based Access & Dashboards**: Dedicated mentor dashboard with student search and performance summaries.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, Flask
- **Database ORM**: Flask-SQLAlchemy, SQLAlchemy, Alembic (Flask-Migrate)
- **Database Engine**: PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript, Jinja2 Templates
- **Email Service**: SMTP (e.g., Gmail TLS)

---

## 📋 Prerequisites

- Python 3.10 or higher
- Git
- PostgreSQL database instance

---

## ⚙️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/<your-username>/mentor_book.git
   cd mentor_book
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and fill in your configuration:
   ```bash
   cp .env.example .env
   ```

   Configure your database and mail credentials inside `.env`:
   ```env
   SECRET_KEY=your_secret_key_here
   DATABASE_URL=postgresql://username:password@localhost:5432/mentor_book_db
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_app_password
   ```

5. **Run Database Migrations (if applicable)**:
   ```bash
   flask db upgrade
   ```

6. **Start the Application**:
   ```bash
   python app.py
   ```
   Open your browser and navigate to `http://127.0.0.1:5000/`.

---

## 📁 Project Structure

```
mentor_book/
├── app.py              # Application entry point & route definitions
├── config.py           # Configuration loader from environment variables
├── mentor.py           # Mentor blueprint with view controllers and business logic
├── models.py           # SQLAlchemy database schema models
├── migrations/         # Alembic database migration scripts
├── static/             # Static assets (CSS, JS, images)
├── templates/          # Jinja2 HTML templates
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
└── README.md           # Project documentation
```

---

## 🔒 Security Note

Never commit your `.env` file or sensitive credentials into Git. The `.gitignore` file is pre-configured to exclude sensitive credentials and cache files.
