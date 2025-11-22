Chemical Equipment Parameter Visualizer

This project implements a complete end-to-end chemical equipment analytics system consisting of:

Django REST Backend

React Web Dashboard

PyQt5 Desktop Application (.exe supported)

Automated CSV parsing + analytics

Professional charts and reporting

PDF Report Generator

It allows users to upload equipment CSV datasets and instantly view:

Equipment type distribution

Average flowrate, pressure, temperature

Total equipment count

Upload history


Downloadable PDF report



 1. Features

🔹 Backend (Django REST Framework)

CSV Upload API
Cleans and parses equipment CSV
Computes:
Total count
Avg Flowrate
Avg Pressure
Avg Temperature
Type distribution (Pump, Valve, Compressor, Reactor, etc.)
Stores upload history
PDF report generation endpoint
Fully documented REST endpoints

🔹 Web App (React + Material UI + Chart.js)

Modern professional dashboard
Large KPI cards
Interactive Pie-chart
Clean bar chart
Upload history viewer
File upload with progress

🔹 Desktop App (PyQt5 + Matplotlib)


Larger KPI cards with bold dark values
Stunning donut chart
Clear bar chart with dynamic scaling
Upload CSV button
Auto-refresh summary/history
Export PDF report feature
Packaged as Windows .exe (PyInstaller)


📂 2. Project Folder Structure
ChemicalVisualizer/
│── backend/                 # Django REST API
│   ├── equipment_api/
│   ├── media/uploads/
│   ├── manage.py
│   ├── requirements.txt
│
│── web-frontend/            # React Dashboard
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── README.md
│
│── desktop-app/             # PyQt5 Desktop App
│   ├── desktop_app.py
│   ├── dist/                # .exe output here
│   ├── build/
│   ├── venv/
│
└── README.md                # Main readme


 3. System Architecture
               ┌─────────────────────────┐
               │     React Frontend      │
               │ (Charts + Dashboard UI) │
               └─────────────▲───────────┘
                             │ REST API
               ┌─────────────┴───────────┐
               │    Django Backend API    │
               │  Upload ➜ Process ➜ DB   │
               └─────────────▲───────────┘
                             │ JSON
               ┌─────────────┴───────────┐
               │   PyQt5 Desktop App      │
               │  (Charts + PDF Export)   │
               └──────────────────────────┘


 4. Installation Guide
 A. Backend Setup
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

Server runs at:
http://127.0.0.1:8000/


 B. React Frontend Setup
cd web-frontend
npm install
npm start

Runs at:
http://localhost:3000/


 C. Desktop App Setup
cd desktop-app
pip install PyQt5 matplotlib requests
python desktop_app.py


 Build Desktop EXE
pyinstaller desktop_app.spec

Generated EXE:
desktop-app/dist/ChemicalVisualizerDesktop.exe


 5. API Endpoints
    
1️⃣ Upload CSV
POST /api/upload/
file: <csv>

2️⃣ Latest Summary
GET /api/summary/latest/

Response example
{
  "total_count": 15,
  "averages": {
    "Flowrate": 119.8,
    "Pressure": 120.01,
    "Temperature": 119.79
  },
  "type_distribution": {
    "Pump": 5,
    "Valve": 4,
    "Compressor": 2,
    "Condenser": 2,
    "Reactor": 1
  }
}

3️⃣ Upload History
GET /api/history/

4️⃣ Download PDF Report
GET /api/report/<id>/


🎨 6. Technologies Used
ComponentTechnologyBackendDjango, DRFFrontendReact, Material UI, Chart.jsDesktop AppPyQt5, MatplotlibDatabaseSQLitePackagingPyInstallerVersion ControlGit + GitHub

🎬 7. Demo Video Script (Use for submission)
Intro:
“My name is Sujay Devadiga. This is my IIT-Bombay Winter Internship project — a hybrid Chemical Equipment Parameter Visualizer.”
