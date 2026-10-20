# PennyPilot

PennyPilot is a full-stack personal finance management platform that helps users track expenses, manage budgets, monitor accounts, and gain insights into their financial health.

## Live Demo

Frontend:
https://pennypilot-a7f4rhcfl-team1-f388.vercel.app

Backend Health:
https://pennypilot-8qgd.onrender.com/health

## Features

- User Authentication
- Expense Tracking
- Account Management
- Budget Planning
- Financial Analytics
- CSV Import/Export
- Multi-category Expense Classification
- Dashboard & Reports

## Tech Stack

Frontend
- React
- TypeScript
- Vite

Backend
- FastAPI
- SQLAlchemy
- Pydantic

Database
- PostgreSQL (Neon)

Deployment
- Vercel (Frontend)
- Render (Backend)
- Neon (Database)

## Architecture

Frontend (Vercel)
↓
FastAPI Backend (Render)
↓
PostgreSQL Database (Neon)

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload