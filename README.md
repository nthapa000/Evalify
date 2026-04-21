# Evalify — Automated Handwritten Answer Sheet Evaluation System

A web-based platform that automates evaluation of handwritten exam answer sheets using computer vision, OCR, and LLM models.

## 🎯 Project Overview

Evalify enables teachers to create digital exam papers and automatically evaluate handwritten answer sheets submitted by students. The system supports three paper types:

- **Type 1**: MCQ only (OMR-based or vision model)
- **Type 2**: MCQ + Numerical (vision model + tolerance-based grading)
- **Type 3**: MCQ + Numerical + Subjective (vision model + LLM rubric grading)

**Roles:**
- **Teachers**: Create papers, upload answer keys, set rubrics, view results
- **Students**: Login, view available exams, upload answer sheets, view scores

---

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Hardware**: 
  - NVIDIA GPU (V100 or better, 16GB+ VRAM recommended for Ollama)
  - 8GB+ RAM
  - 20GB+ free disk space
- **CUDA**: 11.8+ (if using GPU)

### Software Requirements
- **Python**: 3.11
- **Node.js**: 16+ and npm 8+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Ollama**: 0.1.26+ (for vision-based OCR and LLM grading)

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
cd /home/m25csa019
git clone <repository-url> Evalify
cd Evalify
```

### 2. Start MongoDB & MLflow (Docker)
```bash
docker compose -f docker-compose.dev.yml up -d
```

This starts:
- **MongoDB**: `localhost:27017` (database)
- **MLflow**: `http://localhost:5005` (experiment tracking)

Verify services are running:
```bash
docker ps
```

### 3. Setup & Start Backend (FastAPI)
```bash
cd backend

# Create virtual environment (one-time setup)
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
bash start.sh
```

The backend will:
- Start FastAPI on `http://localhost:47823`
- Attempt to start Ollama (if installed)
- Connect to MongoDB and MLflow
- Load seed users into the database

**Check if backend is running:**
- API Docs: `http://localhost:47823/docs`
- API ReDoc: `http://localhost:47823/redoc`

### 4. Setup & Start Frontend (React)
```bash
cd frontend

# Install dependencies (one-time setup)
npm install

# Start dev server
npm run dev
```

The frontend will start on `http://localhost:5173`

---

## 📍 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:5173 | React UI (teacher/student dashboards) |
| **Backend API** | http://localhost:47823 | FastAPI REST endpoints |
| **API Docs** | http://localhost:47823/docs | Swagger UI (interactive) |
| **API ReDoc** | http://localhost:47823/redoc | Alternative API documentation |
| **MLflow UI** | http://localhost:5005 | Model tracking & experiments |
| **MongoDB** | localhost:27017 | Document database |

---

## 🔐 Default Credentials

### Teacher Login
```
Email:    teacher@evalify.local
Password: Teacher@123
```

### Student Login
```
Roll No:  CS2025001
Password: Student@123
```

**⚠️ Change these credentials before deploying to production!**
- Edit `teacher_credentials.env`
- Edit `student_credentials.env`
- Restart the backend

---

## 📁 Project Structure

```
Evalify/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── config.py          # Configuration & environment variables
│   │   ├── db/
│   │   │   ├── mongodb.py     # MongoDB connection
│   │   │   ├── seed.py        # Seed default users
│   │   │   └── mlflow_logger.py
│   │   ├── models/            # Pydantic data models
│   │   ├── routers/           # API endpoints
│   │   │   ├── auth.py        # Login/register
│   │   │   ├── papers.py      # Create/view papers
│   │   │   ├── submissions.py # Upload answer sheets
│   │   │   └── results.py     # View evaluation results
│   │   ├── services/          # Business logic
│   │   │   ├── evaluator.py   # Main evaluation orchestrator
│   │   │   ├── ollama_engine.py
│   │   │   ├── omr_engine.py  # OMR/bubble detection
│   │   │   ├── pdf_extractor.py
│   │   │   └── subjective_grader.py
│   │   └── prompts/           # LLM prompt templates
│   ├── requirements.txt       # Python dependencies
│   ├── start.sh              # Backend startup script
│   ├── Dockerfile            # Docker image definition
│   └── venv/                 # Python virtual environment (created locally)
│
├── frontend/                  # React + Vite frontend
│   ├── src/
│   │   ├── main.jsx          # React entry point
│   │   ├── App.jsx           # Root component
│   │   ├── components/       # Reusable React components
│   │   ├── pages/            # Page components (auth, dashboards)
│   │   ├── hooks/            # Custom React hooks
│   │   ├── services/         # API client (axios)
│   │   └── store/            # State management (Zustand)
│   ├── package.json          # Node dependencies
│   ├── vite.config.js        # Vite configuration
│   └── Dockerfile            # Docker image definition
│
├── ml/                        # ML microservices
│   ├── llm_service/          # LLM grading service
│   ├── omr_service/          # OMR service
│   └── trocr_service/        # TrOCR service
│
├── k8s/                       # Kubernetes manifests (optional)
├── docker-compose.dev.yml    # Development Docker setup
├── EVALIFY_PLAN.md          # Detailed project plan
└── README.md                 # This file
```

---

## 🛠️ Development Workflow

### Backend Development
```bash
cd backend
source venv/bin/activate

# Run backend with auto-reload
bash start.sh

# Run tests
pytest tests/

# Check Python version
python --version
```

### Frontend Development
```bash
cd frontend

# Start dev server (auto-reload on file changes)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Database & Monitoring
```bash
# View MongoDB logs
docker logs evalify-mongo

# View MLflow logs
docker logs evalify-mlflow

# Access MongoDB shell
docker exec -it evalify-mongo mongosh -u evalify -p evalify_dev_pass --authenticationDatabase admin

# View running services
docker ps
```

---

## 🔧 Configuration

### Backend Configuration
Edit `backend/app/config.py` to customize:
- MongoDB connection settings
- JWT token expiration times
- MLflow tracking server URI
- Ollama engine settings

### Environment Variables
Create or edit credential files:
- `student_credentials.env` - Student JWT secret & defaults
- `teacher_credentials.env` - Teacher JWT secret & defaults

Example:
```dotenv
TEACHER_DEFAULT_EMAIL=teacher@evalify.local
TEACHER_DEFAULT_PASSWORD=Teacher@123
TEACHER_JWT_SECRET=your_secret_key_here_minimum_32_characters_long
TEACHER_JWT_EXPIRE_MINUTES=480
```

---

## 📦 Dependencies

### Backend (Python 3.11)
- **Web Framework**: FastAPI 0.111.0, Uvicorn
- **Database**: MongoDB (via Motor + PyMongo)
- **ML/CV**: 
  - Ollama (vision model + LLM)
  - OpenCV (OMR detection)
  - EasyOCR (handwriting recognition)
  - Transformers, Torch
- **Utilities**: PDFPlumber, PyMuPDF, Pillow
- **MLOps**: MLflow 2.13.0
- **Auth**: JWT, bcrypt, passlib
- **Testing**: pytest, httpx, pytest-asyncio

### Frontend (Node.js)
- **Framework**: React 18, Vite 5.2
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **State Management**: Zustand
- **Styling**: TailwindCSS 3.4
- **API Queries**: React Query 3.39

---

## 🐳 Docker Deployment

### Development with Docker Compose
```bash
# Start all services
docker compose -f docker-compose.dev.yml up -d

# View logs
docker compose -f docker-compose.dev.yml logs -f

# Stop services
docker compose -f docker-compose.dev.yml down

# Remove volumes (careful—deletes data!)
docker compose -f docker-compose.dev.yml down -v
```

### Manual Docker Build
```bash
# Build backend image
cd backend
docker build -t evalify-backend:latest .

# Build frontend image
cd ../frontend
docker build -t evalify-frontend:latest .

# Run containers
docker run -d -p 47823:47823 evalify-backend:latest
docker run -d -p 5173:5173 evalify-frontend:latest
```

---

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
source venv/bin/activate

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app
```

### Test Files
- `test_auth.py` - Authentication endpoints
- `test_papers.py` - Paper creation & management
- `test_papers.py` - Submission handling
- `verify_phase3.py` - Phase 3 functionality validation

---

## 🐛 Troubleshooting

### MongoDB Connection Error
```
Error: Connection to MongoDB failed
```
**Solution:**
```bash
docker ps | grep mongo
# If not running, start with:
docker compose -f docker-compose.dev.yml up -d
```

### Backend Fails to Start
```
Error: venv not found
```
**Solution:**
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
bash start.sh
```

### Ollama Not Available
```
⚠️ Ollama: did not start — handwritten OCR will run in STUB mode
```
**Solution:** Install Ollama from https://ollama.ai or disable GPU features in config.

### CUDA/GPU Issues
```bash
# Check GPU availability
nvidia-smi

# Set CUDA paths
export CUDA_HOME=/usr/local/cuda
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
```

### Port Already in Use
```bash
# Find process using port 5173
lsof -i :5173

# Kill process
kill -9 <PID>
```

---

## 📊 API Overview

### Authentication
```
POST /api/auth/teacher/login      - Teacher login
POST /api/auth/student/login      - Student login
POST /api/auth/logout             - Logout
```

### Papers (Teacher)
```
POST /api/papers                   - Create new paper
GET /api/papers                    - List all papers
GET /api/papers/{paper_id}         - Get paper details
PUT /api/papers/{paper_id}         - Update paper
DELETE /api/papers/{paper_id}      - Delete paper
```

### Submissions (Student)
```
POST /api/submissions              - Upload answer sheet
GET /api/submissions               - List submissions
GET /api/submissions/{submission_id} - Get submission details
```

### Results
```
GET /api/results                   - View evaluation results
GET /api/results/{result_id}       - Get result details
```

For full API documentation, visit:
- Interactive Docs: `http://localhost:47823/docs`
- Alternative Docs: `http://localhost:47823/redoc`

---

## 🚀 Deployment Checklist

Before deploying to production:

- [ ] Change default credentials in `teacher_credentials.env` and `student_credentials.env`
- [ ] Update JWT secrets (minimum 32 characters, use secure random values)
- [ ] Configure MongoDB with strong credentials
- [ ] Enable MongoDB SSL/TLS connections
- [ ] Set up CORS properly (restrict to your domain)
- [ ] Enable HTTPS/SSL on backend & frontend
- [ ] Configure MLflow for persistent artifact storage
- [ ] Set up log aggregation (ELK, Datadog, etc.)
- [ ] Configure backups for MongoDB
- [ ] Load test the evaluation pipeline
- [ ] Set up monitoring & alerts

---

## 📝 Development Notes

### Key Concepts
- **OMR**: Optical Mark Recognition (bubble detection for MCQ)
- **Vision Model**: Ollama llama3.2-vision for handwritten text extraction
- **LLM Grading**: Using same LLM to grade subjective answers against rubrics
- **MLflow**: Tracks model versions, evaluation metrics, and experiment results

### Performance Optimization
- Frontend uses Vite for fast HMR during development
- Backend uses async/await (Motor, FastAPI) for concurrent request handling
- Ollama runs in a separate process to isolate GPU usage
- MongoDB indexes are created on frequently queried fields

---

## 📞 Support & Contact

**Project Team:**
- m25csa019 (Nishant Thapa)
- m25csa021 (Pranav)

**Subject:** MLOps / DLOps  
**Date:** April 2026

---

## 📄 License

[Your License Here]

---

## 🔗 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [MLflow Documentation](https://mlflow.org/docs/)
- [Docker Documentation](https://docs.docker.com/)

