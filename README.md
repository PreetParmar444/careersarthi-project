![Python](https://img.shields.io/badge/Python-3.11-blue)
![Google ADK](https://img.shields.io/badge/Google-ADK-green)
![Gemini](https://img.shields.io/badge/Gemini-AI-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![License](https://img.shields.io/badge/License-MIT-yellow)


# 🚀 CareerSarthi - AI Multi-Agent Career Copilot

> **Track Applications • Analyze Skills • Prepare Interviews • Protect Privacy**

CareerSarthi is an AI-powered **Multi-Agent Career Assistant** built using **Google Agent Development Kit (ADK)**. It helps students and professionals streamline their job search by automatically tracking job applications, analyzing resumes, identifying skill gaps, managing deadlines, and generating personalized interview preparation—all while ensuring user privacy.

---

## 🎥 Project Demo

📺 **YouTube Demo:**  
https://youtu.be/GOeW46ksvaw

---

## 📌 Problem Statement

Managing multiple job applications is challenging. Job seekers often:

- Forget application deadlines
- Lose track of interview invitations
- Don't know which skills they need to improve
- Prepare generic interview questions
- Share sensitive personal information with AI tools

CareerSarthi solves these problems through a collaborative AI Multi-Agent system.

---

# ✨ Features

### 📩 Inbox Tracker Agent

- Secure Gmail Integration
- Tracks job application emails
- Extracts:
  - Company Name
  - Job Role
  - Application Status
  - Deadlines

---

### 📄 ATS Resume Analyzer

- Resume Parsing
- ATS Score Generation
- Resume Feedback
- Improvement Suggestions

---

### 🎯 Skill Gap Analyzer

- Compares resume against job descriptions
- Identifies missing technical skills
- Personalized learning recommendations

---

### 📅 Deadline Guardian

- Tracks upcoming interviews
- Monitors application deadlines
- Calendar integration
- Priority alerts

---

### 🎤 Interview Preparation Agent

- Company-specific interview questions
- Technical preparation
- HR interview questions
- Personalized practice

---

### 🔒 Privacy Guardian

Protects sensitive user information by automatically masking:

- Email Addresses
- Phone Numbers
- Aadhaar Numbers
- PAN Numbers
- Salary Information
- Addresses

before sending data to AI models.

---

# 🏗 Multi-Agent Architecture

CareerSarthi uses **Google Agent Development Kit (ADK)** to coordinate multiple specialized AI agents.

```
                        User
                          │
                          ▼
                 ADK Orchestrator Agent
                          │
     ┌──────────────┬──────────────┬──────────────┐
     ▼              ▼              ▼
 Inbox Agent     ATS Agent     Skill Gap Agent
     │              │              │
     └──────────────┼──────────────┘
                    ▼
          Deadline Guardian
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
 Interview Agent        Privacy Guardian
```

Each agent has a dedicated responsibility, making the system modular, scalable, and efficient.

---

# 🛠 Tech Stack

## AI & Agents

- Google Agent Development Kit (ADK)
- Gemini API

## Backend

- Python
- FastAPI
- MCP Server

## Frontend

- Streamlit

## Database

- SQLite

## APIs

- Gmail API
- Google Calendar API

## Security

- OAuth 2.0
- PII Redaction
- Encrypted Local Storage

---

# 📸 Screenshots

## Landing Page

_Add Screenshot_

---

## ATS Resume Analysis

_Add Screenshot_

---

## Skill Gap Analysis

_Add Screenshot_

---

## Job Application Tracker

_Add Screenshot_

---

## Deadline Guardian

_Add Screenshot_

---

## Interview Preparation

_Add Screenshot_

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/<username>/CareerSarthi.git
```

```bash
cd CareerSarthi
```

---

## Create Virtual Environment

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

Create a `.env` file.

Example:

```env
GOOGLE_API_KEY=YOUR_API_KEY
GMAIL_CLIENT_ID=YOUR_CLIENT_ID
GMAIL_CLIENT_SECRET=YOUR_CLIENT_SECRET
```

---

## Run the Application

```bash
streamlit run frontend/main.py
```

---

# 💡 Future Improvements

- LinkedIn Integration
- AI Resume Rewriter
- Mock Voice Interviews
- Recruiter Dashboard
- Salary Prediction
- Mobile Application
- Job Recommendation Engine

---

# 👨‍💻 Author

**Preet Parmar**

B.Tech Computer Engineering  
Pandit Deendayal Energy University (PDEU)

GitHub: https://github.com/<YOUR_USERNAME>

LinkedIn: https://linkedin.com/in/<YOUR_LINKEDIN>

---

# 📄 License

This project was developed as part of the **Google Agent Development Kit (ADK) Hackathon** and is intended for educational and demonstration purposes.
