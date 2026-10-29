# Operational Runbook

## Apex Operations API - Production Operations Guide

---

## Table of Contents

1. [Deployment Procedures](#deployment-procedures)
2. [Rollback Procedures](#rollback-procedures)
3. [Incident Response](#incident-response)
4. [Scaling Guidelines](#scaling-guidelines)
5. [Monitoring & Alerting](#monitoring--alerting)
6. [Troubleshooting](#troubleshooting)
7. [Health Checks](#health-checks)
8. [Maintenance](#maintenance)

---

## Deployment Procedures

### Manual Deployment (if needed)

#### Step 1: Prepare the Environment
```bash
# SSH into the Huawei Cloud ECS instance
ssh -i KeyPair-one-meristem-app.pem root@203.123.83.136

# Navigate to the application directory
cd /home/github-runner/apex-devops-assessment

# Verify current branch
git branch
git status
```

#### Step 2: Backup Current State
```bash
# Backup the current docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)

# Backup the current .env file (if exists)
[ -f .env ] && cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# List backups to verify
ls -lh docker-compose.yml.backup.*
```

#### Step 3: Update Code
```bash
# Fetch latest changes from dev_env branch
git fetch origin dev_env

# Merge changes
git merge origin/dev_env

# Verify no conflicts
git status
```

#### Step 4: Stop Current Services
```bash
# Stop all running containers
docker-compose down

# Verify containers are stopped
docker-compose ps
```

#### Step 5: Build and Start Services
```bash
# Build new Docker image and start services
docker-compose up -d --build

# Monitor startup (wait ~15 seconds)
sleep 15

# Verify all containers are running
docker-compose ps
```

#### Step 6: Health Verification
```bash
# Check liveness probe
curl -s http://localhost:8000/health | jq .

# Check readiness probe
curl -s http://localhost:8000/readiness | jq .

# Test API endpoint
curl -s http://localhost:8000/docs | head -20

# View application logs
docker-compose logs apex_api --tail=50
```

#### Step 7: Verification Complete
```bash
# If all health checks pass:
echo "✅ Deployment successful"

# If any check fails:
echo "❌ Deployment failed - triggering rollback"
# See Rollback Procedures below
```

### Automated Deployment (GitHub Actions)

Deployments are automated when code is pushed to `dev_env` branch:

1. **CI Pipeline Runs** (4 jobs)
   - Lint checks
   - Security scanning
   - Unit tests
   - Docker build

2. **CD Pipeline Runs** (if CI passes)
   - Backup current state
   - Git pull latest code
   - Stop containers
   - Start new containers
   - Run health checks
   - Rollback on failure

**View Deployment Status:**
```bash
# GitHub Actions URL
https://github.com/Lugardesosa/apex-devops-assessment/actions
```

---

## Rollback Procedures

### Automatic Rollback (via GitHub Actions)

The CD pipeline automatically rolls back if health checks fail:

1. Docker-compose stops all containers
2. Backup docker-compose.yml is restored
3. Old containers are restarted
4. Health checks verified again
5. Alert is sent (logs in GitHub Actions)

**Check rollback in logs:**
```
GitHub Actions → CD Job → Rollback on failure section
```

### Manual Rollback

If you need to manually rollback:

#### Step 1: Stop Current Services
```bash
cd /home/github-runner/apex-devops-assessment

# Stop all containers
docker-compose down

# Remove failed containers
docker-compose rm -f
```

#### Step 2: Restore from Backup
```bash
# List available backups
ls -lh docker-compose.yml.backup.*

# Restore the most recent backup
BACKUP=$(ls -t docker-compose.yml.backup.* | head -1)
cp "$BACKUP" docker-compose.yml

# Verify restoration
cat docker-compose.yml | head -20
```

#### Step 3: Revert Code Changes
```bash
# Show commit history
git log --oneline -5

# Revert to previous commit (if needed)
git revert HEAD --no-edit

# Or checkout previous version
git checkout HEAD~1 -- . 
```

#### Step 4: Restart Services
```bash
# Start services with backup configuration
docker-compose up -d

# Wait for startup
sleep 15

# Verify containers
docker-compose ps
```

#### Step 5: Health Check
```bash
# Verify services are healthy
curl http://localhost:8000/health
curl http://localhost:8000/readiness

# Check logs
docker-compose logs apex_api --tail=20
```

#### Step 6: Notify Team
```bash
# Update git with rollback info
git log --oneline -1 > /tmp/rollback_info.txt

# Record in logs
echo "Rolled back to previous version at $(date)" >> /tmp/rollback_log.txt
```

---

## Incident Response

### Incident Response Team

**On-Call Schedule:**
- Contact: DevOps Team Lead
- Escalation: Engineering Manager
- Backup: Cloud Platform Admin

### Incident Classification

| Severity | Impact | Response Time | Example |
|----------|--------|----------------|---------|
| **Critical** | Service down | Immediate (15 min) | API not responding, database down |
| **High** | Degraded performance | 30 minutes | Slow responses, partial outages |
| **Medium** | Non-critical issues | 1-2 hours | Memory warnings, log rotation |
| **Low** | Cosmetic/documentation | 4-8 hours | Typos, UI glitches |

### Critical Incident Response (Service Down)

#### Immediate Actions (0-5 minutes)
```bash
1. Acknowledge the incident
2. Access the Huawei Cloud ECS instance
3. Check service status: docker-compose ps
4. Check logs: docker-compose logs --tail=100
5. Determine if it's infrastructure or application issue
```

#### Diagnosis (5-15 minutes)
```bash
# Check if containers are running
docker ps -a | grep apex

# Check error logs
docker-compose logs apex_api
docker-compose logs apex_db

# Check system resources
docker stats

# Check database connectivity
docker-compose exec apex_db pg_isready -U user

# Check network connectivity
docker network ls
docker network inspect apex-devops-assessment_default
```

#### Recovery (15-30 minutes)

**If Application Issue:**
```bash
# View latest logs for errors
docker-compose logs apex_api -f

# Check if code is corrupted
git status
git log --oneline -5

# If code issue, rollback
./rollback.sh  # Or manual steps above
```

**If Database Issue:**
```bash
# Check database status
docker-compose logs apex_db

# If database won't start
docker-compose down
docker volume ls | grep apex
docker volume rm apex-devops-assessment_postgres_data  # WARNING: Data loss!

# Restart services (will recreate database)
docker-compose up -d
```

**If Resource Issue:**
```bash
# Check disk space
df -h

# Check memory
free -h

# Clean up old images/containers
docker system prune -f

# Increase volume size (if needed)
# Contact Huawei Cloud support
```

#### Post-Incident (30+ minutes)

```bash
1. Document incident in /tmp/incident_log.txt
2. Record start time, duration, root cause
3. Notify stakeholders
4. Schedule post-mortem meeting
5. Update runbook if needed
```

**Incident Log Template:**
```
Incident: [Description]
Date: [YYYY-MM-DD HH:MM]
Duration: [Minutes]
Root Cause: [What happened]
Resolution: [How it was fixed]
Impact: [How many users affected]
Post-Mortem: [Scheduled for YYYY-MM-DD]
```

### High-Priority Incident Response

#### Response Time: 30 minutes

```bash
# 1. Assess the situation
docker-compose ps
curl http://localhost:8000/health

# 2. Check recent changes
git log --oneline -10

# 3. Monitor metrics
docker stats --no-stream

# 4. Implement fix
# - Deploy hotfix or
# - Rollback recent change

# 5. Verify recovery
curl http://localhost:8000/health
curl http://localhost:8000/readiness

# 6. Document in logs
```

---

## Scaling Guidelines

### Vertical Scaling (Increase container resources)

#### For FastAPI Container

```bash
# Edit docker-compose.yml
nano docker-compose.yml

# Update deploy resources section:
# deploy:
#   resources:
#     limits:
#       cpus: '2.0'           # Increase from 1.0
#       memory: 2G            # Increase from 1G
#     reservations:
#       cpus: '1.0'
#       memory: 512M

# Restart services
docker-compose down
docker-compose up -d

# Verify new resources
docker stats
```

#### For PostgreSQL Container

```bash
# Update docker-compose.yml PostgreSQL section:
# environment:
#   - shared_buffers=512MB        # Increase from 256MB
#   - effective_cache_size=1GB    # Increase from 512MB

# Restart database
docker-compose restart apex_db

# Verify settings
docker-compose exec apex_db psql -U user -d apex_db -c "SHOW shared_buffers;"
```

### Horizontal Scaling (Load balancing)

Currently single instance. For horizontal scaling:

```
1. Deploy second instance on Huawei Cloud
2. Configure load balancer (Huawei Cloud)
3. Add instance to DNS records
4. Configure database replication (if needed)
5. Set up health check monitoring
```

### Performance Tuning

```bash
# Monitor current performance
docker stats --no-stream

# Check slow queries
docker-compose exec apex_db psql -U user -d apex_db -c "\dt"

# Optimize database
docker-compose exec apex_db vacuumdb -U user -d apex_db

# Check application metrics
curl http://localhost:8000/health
```

---

## Monitoring & Alerting

### Health Check Endpoints

#### Liveness Probe: `/health`
```bash
# Command
curl -s http://203.123.83.136:8000/health | jq .

# Expected Response
{
  "status": "healthy"
}

# Frequency: Every 30 seconds
# Timeout: 3 seconds
# Retries: 3
```

#### Readiness Probe: `/readiness`
```bash
# Command
curl -s http://203.123.83.136:8000/readiness | jq .

# Expected Response
{
  "status": "ready"
}

# Frequency: Every 10 seconds
# Timeout: 5 seconds
# Retries: 5
```

### Monitoring Checklist

**Daily Checks:**
```bash
# 1. Container status
docker-compose ps

# 2. Resource usage
docker stats --no-stream

# 3. Disk space
df -h

# 4. Recent logs
docker-compose logs --tail=100

# 5. API health
curl http://localhost:8000/health
curl http://localhost:8000/readiness
```

**Weekly Checks:**
```bash
# 1. Database size
docker-compose exec apex_db du -sh /var/lib/postgresql/data

# 2. Database integrity
docker-compose exec apex_db pg_dump -U user -d apex_db --schema-only | head -20

# 3. Network connectivity
docker network inspect apex-devops-assessment_default

# 4. Backup status
ls -lh docker-compose.yml.backup.*
```

**Monthly Checks:**
```bash
# 1. Update dependencies
grep -r "python:3" Dockerfile  # Check Python version

# 2. Review security scans
# Check GitHub Actions security logs

# 3. Disaster recovery drill
# Test rollback procedure

# 4. Capacity planning
docker stats --no-stream
# Are we approaching limits?
```

### Alert Triggers

| Alert | Condition | Action |
|-------|-----------|--------|
| **Service Down** | Health check fails for 3 consecutive probes | Trigger incident response |
| **High Memory** | Memory usage > 80% | Scale up or investigate leak |
| **Disk Full** | Disk usage > 90% | Clean up old logs/data |
| **Slow Responses** | API latency > 1 second | Check database, scale resources |
| **Database Error** | Connection pool exhausted | Restart services, check app |
| **Failed Deploy** | CI/CD job fails | Check logs, fix code, re-push |

### Logging

**View Logs:**
```bash
# Current logs
docker-compose logs -f apex_api

# Last N lines
docker-compose logs apex_api --tail=50

# Since timestamp
docker-compose logs apex_api --since 2026-10-30T00:00:00

# Specific service
docker-compose logs apex_db
```

**Log Format:**
```json
{
  "timestamp": "2026-10-30T00:00:00.000000",
  "level": "INFO",
  "message": "Request processed",
  "module": "main"
}
```

---

## Troubleshooting

### Common Issues & Solutions

#### Issue 1: Containers Won't Start

**Symptoms:**
```
docker-compose ps shows "Exited" status
```

**Diagnosis:**
```bash
docker-compose logs apex_api
docker-compose logs apex_db
```

**Solutions:**
```bash
# Option 1: Remove and restart
docker-compose down -v
docker-compose up -d

# Option 2: Check disk space
df -h

# Option 3: Check port availability
netstat -tuln | grep 8000
netstat -tuln | grep 5432

# Option 4: Check Docker daemon
docker ps
docker info
```

#### Issue 2: Database Connection Failed

**Symptoms:**
```
curl: (7) Failed to connect to localhost port 5432
```

**Diagnosis:**
```bash
docker-compose ps | grep apex_db
docker-compose logs apex_db
```

**Solutions:**
```bash
# Restart database
docker-compose restart apex_db

# Check health
docker-compose exec apex_db pg_isready -U user

# Verify credentials
echo "DATABASE_URL=postgresql://user:password@db:5432/apex_db" | grep -o "user:password"
```

#### Issue 3: Out of Memory

**Symptoms:**
```
OOMKilled containers
High memory usage
```

**Solutions:**
```bash
# Check memory usage
docker stats

# Clean up
docker system prune -f

# Restart with limits
docker-compose down
docker-compose up -d

# Increase memory in docker-compose.yml
```

#### Issue 4: Slow API Responses

**Symptoms:**
```
Latency > 1 second
Slow health checks
```

**Solutions:**
```bash
# Check resource usage
docker stats

# Check logs for errors
docker-compose logs apex_api

# Check database performance
docker-compose exec apex_db psql -U user -d apex_db -c "SELECT count(*) FROM users;"

# Restart if needed
docker-compose restart
```

#### Issue 5: Deployment Stuck

**Symptoms:**
```
CI/CD job not completing
Health checks timing out
```

**Solutions:**
```bash
# Manually stop
docker-compose down

# Clear state
docker system prune -f

# Restart
docker-compose up -d

# Check logs
docker-compose logs --tail=100
```

---

## Health Checks

### Container Health Status

```bash
# Check all container health
docker-compose ps

# Expected output:
# NAME       STATUS
# apex_api   Up
# apex_db    Up (healthy)
```

### API Health Endpoints

**Check Liveness (Container Alive):**
```bash
curl -X GET http://203.123.83.136:8000/health

# Success: HTTP 200
# Response: {"status":"healthy"}
```

**Check Readiness (Ready for Traffic):**
```bash
curl -X GET http://203.123.83.136:8000/readiness

# Success: HTTP 200
# Response: {"status":"ready"}
```

**Full Health Check Script:**
```bash
#!/bin/bash

echo "=== Apex Operations API Health Check ==="
echo

# Check containers
echo "1. Container Status:"
docker-compose ps | grep -E "apex_api|apex_db|NAME"
echo

# Check liveness
echo "2. Liveness Probe:"
curl -s http://localhost:8000/health | jq .
echo

# Check readiness
echo "3. Readiness Probe:"
curl -s http://localhost:8000/readiness | jq .
echo

# Check database
echo "4. Database Connection:"
docker-compose exec -T apex_db pg_isready -U user
echo

# Check resources
echo "5. Resource Usage:"
docker stats --no-stream
```

---

## Maintenance

### Regular Maintenance Tasks

**Daily (Automated via CI/CD):**
- Run security scans
- Run unit tests
- Build Docker images
- Deploy if all checks pass

**Weekly (Manual):**
```bash
# Clean up old backups
find . -name "docker-compose.yml.backup.*" -mtime +7 -delete

# Check for unused resources
docker image prune -f
docker volume prune -f

# Review logs
docker-compose logs --tail=200 | grep -i error
```

**Monthly (Manual):**
```bash
# Update dependencies
pip list --outdated

# Update Docker base images
docker pull postgres:15-alpine
docker pull python:3.11-slim

# Security audit
safety check
bandit -r app/

# Backup database
docker-compose exec apex_db pg_dump -U user -d apex_db > backup_$(date +%Y%m%d).sql
```

### Backup & Recovery

**Create Backup:**
```bash
# Full system backup
tar -czf apex-backup-$(date +%Y%m%d_%H%M%S).tar.gz \
  docker-compose.yml \
  Dockerfile \
  requirements.txt \
  app/ \
  tests/

# Database backup
docker-compose exec apex_db pg_dump -U user -d apex_db > database_$(date +%Y%m%d_%H%M%S).sql
```

**Restore from Backup:**
```bash
# Extract system backup
tar -xzf apex-backup-*.tar.gz

# Restore database
docker-compose exec -T apex_db psql -U user -d apex_db < database_*.sql
```

---

## Runbook Version & Updates

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-10-30 | Initial runbook creation |

**Next Review Date:** 2026-11-30

---

**Last Updated:** October 30, 2026  
**Maintained By:** DevOps Team  
**On-Call:** Check rotation schedule