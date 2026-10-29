# Apex Operations API - Runbook

## Table of Contents
1. Deployment
2. Rollback
3. Incident Response
4. Troubleshooting

---

## 1. Deployment

### Automatic (CI/CD Trigger)
1. Push code to `dev_env` branch
2. GitHub Actions runs: Lint → Security → Test → Build → Deploy
3. CD pipeline automatically deploys to Huawei Cloud ECS
4. Health checks verify deployment success

### Manual Deployment (SSH)
```bash
ssh user@YOUR_HUAWEI_ECS_IP
cd ~/apex-devops-assessment
git pull origin dev_env
docker-compose up -d
curl http://localhost:8000/health
```

---

## 2. Rollback

### Automatic Rollback (on CI/CD Failure)
- Deployment failure triggers automatic rollback
- Previous docker-compose.yml backup is restored
- Health checks verify rollback success

### Manual Rollback
```bash
ssh user@YOUR_HUAWEI_ECS_IP
cd ~/apex-devops-assessment

# List backups
ls -la docker-compose.backup.*.yml

# Rollback to specific backup (replace TIMESTAMP)
docker-compose -f docker-compose.backup.YYYYMMDD_HHMMSS.yml down
docker-compose -f docker-compose.backup.YYYYMMDD_HHMMSS.yml up -d

# Verify health
curl http://localhost:8000/health
```

---

## 3. Incident Response

### Service Down
1. Check container status:
```bash
docker-compose ps
```

2. Check logs:
```bash
docker-compose logs app
docker-compose logs db
```

3. Restart service:
```bash
docker-compose restart app
sleep 10
curl http://localhost:8000/health
```

### Database Connection Failed
```bash
# Check PostgreSQL health
docker-compose exec db pg_isready -U user -d apex_db

# Restart database
docker-compose restart db
sleep 10

# Restart app
docker-compose restart app
```

### High Memory/CPU Usage
```bash
# Check resource usage
docker stats

# Identify problematic container
docker-compose logs app --tail 50

# Restart if needed
docker-compose restart app
```

---

## 4. Troubleshooting

### Health Check Fails (HTTP 503)
**Cause:** Service not ready (usually DB not connected)

**Fix:**
```bash
# 1. Check database
curl http://localhost:8000/readiness

# 2. Check logs
docker-compose logs app | grep -i error

# 3. Restart both
docker-compose restart db app
sleep 15
curl http://localhost:8000/health
```

### Container Exits Immediately
**Cause:** Startup error or missing env vars

**Fix:**
```bash
# Check logs
docker-compose logs app

# Verify .env exists
cat .env

# Rebuild image
docker-compose build --no-cache
docker-compose up -d
```

### Port Already in Use
**Cause:** Port 8000 or 5432 already bound

**Fix:**
```bash
# Kill process on port 8000
lsof -i :8000
kill -9 <PID>

# Or change port in docker-compose.yml
# Then restart
docker-compose up -d
```

### Tests Fail Locally
```bash
# Ensure .env is set
source .env

# Install dependencies
pip install -r requirements.txt

# Run tests with DB
docker-compose up -d db
sleep 10
pytest tests/ -v
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start | `docker-compose up -d` |
| Stop | `docker-compose down` |
| Logs | `docker-compose logs app -f` |
| Health | `curl http://localhost:8000/health` |
| Readiness | `curl http://localhost:8000/readiness` |
| Restart | `docker-compose restart` |
| Clean | `docker-compose down -v` |

---

## Contacts & Escalation

- **On-call DevOps:** [Your Name] - [Email]
- **Incident Severity:** P1 = Down, P2 = Degraded, P3 = Minor
- **Escalate if:** Multiple rollbacks, security issues, data loss risk
