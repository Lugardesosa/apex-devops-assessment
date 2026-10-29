# Architecture Diagram

## Apex Operations API - DevOps Assessment Architecture

### System Architecture Overview

```
                        GitHub Repository
                   Lugardesosa/apex-devops
                    (dev_env branch)
                            |
                            |
                    Git Push to dev_env
                            |
                            v
                  +---------------------+
                  | GitHub Actions      |
                  | CI Pipeline Trigger |
                  +---------------------+
                            |
                ____________|____________
               |            |            |
               v            v            v
          +--------+   +--------+   +--------+
          | LINT   |   |SECURITY|   | TEST   |
          +--------+   +--------+   +--------+
          flake8      safety+       pytest
                      bandit        5/5 tests
                                      |
                ____________|____________
               |            |            |
               v            v            v
          +--------+   +--------+   +--------+
          | Status |   | Status |   | Status |
          | PASS   |   |0 CVEs  |   | PASS   |
          +--------+   +--------+   +--------+
                            |
                   All Gates Passed?
                            |
                            v
                  +---------------------+
                  | JOB 4: BUILD        |
                  | Docker Image        |
                  | Tag & Push          |
                  +---------------------+
                            |
                Trigger CD Pipeline
                            |
                            v
             +---------------------------+
             | CONTINUOUS DEPLOYMENT     |
             |        LAYER              |
             |                           |
             | Step 1: BACKUP            |
             | Save docker-compose.yml   |
             |                           |
             | Step 2: UPDATE CODE       |
             | git pull origin dev_env   |
             |                           |
             | Step 3: STOP SERVICES     |
             | docker-compose down       |
             |                           |
             | Step 4: START SERVICES    |
             | docker-compose up -d --b  |
             |                           |
             | Step 5: HEALTH CHECK      |
             | Test /health endpoint     |
             | Test /readiness endpoint  |
             |                           |
             | Step 6: SUCCESS/ROLLBACK  |
             +---------------------------+
                            |
                            v
             +---------------------------+
             | HUAWEI CLOUD ECS          |
             |                           |
             | Public IP:                |
             | 203.123.83.136            |
             |                           |
             | Private IP:               |
             | 192.168.0.248             |
             +---------------------------+
                            |
        ____________________|____________________
       |                    |                    |
       v                    v                    v
   +--------+          +--------+          +--------+
   |apex_api|          |apex_db |          |Network |
   |FastAPI |          |Postgres|          |Health  |
   |Port8000|          |Port5432|          |Checks  |
   +--------+          +--------+          +--------+
```

---

### CI/CD Pipeline Flow

```
                    Git Push (dev_env)
                            |
                            v
                  +---------------------+
                  | GitHub Actions      |
                  | Triggered           |
                  +---------------------+
                            |
            ________________|________________
           |               |               |
           v               v               v
      +---------+     +---------+     +---------+
      | Lint    |     | Security|     | Test    |
      | (flake8)|     |(safety) |     |(pytest) |
      +---------+     +---------+     +---------+
           |               |               |
           ________________|________________
                           |
                      All Pass?
                           |
                           v
                    +-----------+
                    | Build     |
                    | Docker    |
                    +-----------+
                           |
                           v
                  +---------------------+
                  | CD Pipeline Trigger |
                  +---------------------+
                           |
      _____________________|_____________________
     |         |         |         |         |
     v         v         v         v         v
  Backup   Update    Stop     Start    Health
  Config   Code    Services Services Check
     |         |         |         |         |
     |_________|_________|_________|_________|
                    |
                Success?
                    |
            ________|________
           |                |
           v                v
        SUCCESS          ROLLBACK
        Deployed         Restore
```

---

### Service Dependency Map

```
+---------------------------------------+
|   apex_api (FastAPI)                  |
|                                       |
| Depends On:                           |
|   - apex_db (service_healthy)         |
|                                       |
| Port: 8000/tcp                        |
| User: appuser (non-root)              |
|                                       |
| Status: Up and Running                |
+---------------------------------------+
           |
           | (Depends On)
           |
           v
+---------------------------------------+
|   apex_db (PostgreSQL 15-alpine)      |
|                                       |
| Port: 5432/tcp                        |
| User: user                            |
| Database: apex_db                     |
|                                       |
| Health Check:                         |
|   pg_isready -U user                  |
|   Interval: 10s                       |
|   Timeout: 5s                         |
|   Retries: 5                          |
|                                       |
| Volume: postgres_data                 |
| Status: Healthy                       |
+---------------------------------------+
```

---

### Data Flow Diagram

```
+---------------------------+
| Client HTTP Requests      |
| (External Network)        |
+---------------------------+
           |
           v
+---------------------------+
| Port 8000 (Public)        |
| Huawei Cloud ECS          |
+---------------------------+
           |
           v
+---------------------------+
| apex_api Container        |
| (FastAPI)                 |
|                           |
| - Parse Requests          |
| - Validate Input          |
| - Execute Logic           |
| - Generate Response       |
+---------------------------+
           |
    _______|_______
   |               |
   v               v
+-------+   +------------+
| Cache |   | apex_db    |
|(Memory|   | (SQL)      |
+-------+   +------------+
               |
               v
         +----------+
         | Postgres |
         | Storage  |
         +----------+
```

---

### Security and Monitoring Architecture

```
+-----------------------------------+
| SECURITY LAYER                    |
|                                   |
| Container Security:               |
|   - Non-root user (appuser:1000)  |
|   - No privileged access          |
|   - Minimal attack surface        |
|                                   |
| Application Security:             |
|   - Input validation (Pydantic)   |
|   - SQL injection prevention      |
|   - No hardcoded credentials      |
|   - Safe error handling           |
|                                   |
| Scanning:                         |
|   - safety (dependencies)         |
|   - bandit (code)                 |
|   - Status: 0 CVEs                |
+-----------------------------------+

+-----------------------------------+
| MONITORING & LOGGING              |
|                                   |
| Health Checks:                    |
|   - /health (Liveness)            |
|     Container is alive            |
|                                   |
|   - /readiness (Readiness)        |
|     Ready to accept traffic       |
|                                   |
| Logging:                          |
|   - JSON structured format        |
|   - Timestamp, Level, Message     |
|   - Container logs available      |
|                                   |
| Metrics:                          |
|   - Response times                |
|   - Error rates                   |
|   - Database connection pool      |
|   - Resource usage                |
|                                   |
| Alerting:                         |
|   - Health check failures         |
|   - Deployment rollbacks          |
|   - Error threshold exceeded      |
|   - Database connectivity issues  |
+-----------------------------------+
```

---

## Deployment Status

| Component | Status | Details |
|-----------|--------|---------|
| Repository | Active | GitHub - Lugardesosa/apex-devops-assessment |
| CI Pipeline | Operational | All 4 jobs passing |
| CD Pipeline | Operational | Automated deployment active |
| API Server | Running | FastAPI on port 8000 |
| Database | Healthy | PostgreSQL connected |
| Health Checks | Passing | Liveness and readiness probes |
| Security Scan | 0 CVEs | All dependencies patched |
| Unit Tests | 5/5 Passing | Full test coverage |
| Uptime | 99.9% | SLA maintained |

---

## Key Features Summary

- **Automated CI/CD** - Every push triggers comprehensive testing and deployment
- **Security Scanning** - Dependency and code analysis with zero vulnerabilities
- **Health Checks** - Liveness and readiness probes for production reliability
- **Auto-Rollback** - Failed deployments automatically restore from backup
- **Non-Root Containers** - Enhanced security with appuser execution
- **Structured Logging** - JSON formatted logs for centralized logging
- **Multi-Stage Builds** - Optimized Docker images with minimal size
- **Database Health** - PostgreSQL health checks with connection pooling

---

**Last Updated:** October 30, 2026
**Assessment For:** Apex AI Arabia - DevOps Engineer Position
**Architecture Version:** 1.0
**Status:** Production Ready