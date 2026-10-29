# Architecture Diagram

## Apex Operations API - DevOps Assessment

GitHub (dev_env) → CI Pipeline → CD Pipeline → Huawei Cloud ECS
                   (lint,sec,test,build)  (backup,deploy,health-check)

ECS: 203.123.83.136:8000
- FastAPI App (apex_api)
  - GET  /health
  - GET  /readiness  
  - GET  /docs
  - POST /users
  - GET  /users/{id}

- PostgreSQL (apex_db) Port 5432

## Features
- CI Gates: Lint → Security → Test → Build (all passing)
- CD Gates: Backup → Deploy → Health Check → Rollback
- Security: Safety + Bandit = 0 vulnerabilities
- Reliability: Automatic rollback with backup restoration
- Monitoring: Structured JSON logging, health checks

Status: ✅ Live on Huawei Cloud
Updated: October 30, 2026
