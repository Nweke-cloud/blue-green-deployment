# Blue/Green Deployment - Operations Runbook

## Alert Types and Response Actions

### 1. Failover Detected Alert

**Alert Message:**
```
🚨 Failover Detected!
- Previous Pool: blue
- Current Pool: green
- Time: [timestamp]
- Action: Check health of blue container
```

**What It Means:**
Traffic has automatically switched from the primary (blue) pool to the backup (green) pool due to failures detected in the primary.

**Operator Actions:**
1. **Investigate Primary Container:**
```bash
   docker logs app_blue --tail=50
   docker exec app_blue wget -qO- http://localhost:3000/healthz
```

2. **Check Container Status:**
```bash
   docker-compose ps
```

3. **Review Nginx Error Logs:**
```bash
   docker exec nginx_proxy cat /var/log/nginx/error.log | tail -20
```

4. **If Primary is Unhealthy:**
   - Restart the container: `docker-compose restart app_blue`
   - Check application logs for errors
   - Verify dependencies (database, external services)

5. **Recovery Verification:**
   - Wait 5 seconds after fixing
   - Test: `curl -i http://localhost:8080/version`
   - Should show `X-App-Pool: blue` when recovered

**Expected Duration:** 1-5 minutes for automatic recovery

---

### 2. High Error Rate Alert

**Alert Message:**
```
🚨 High Error Rate Alert!
- Error Rate: X.XX%
- Threshold: 2%
- Errors: X/200 requests
- Time: [timestamp]
- Action: Inspect upstream logs immediately
```

**What It Means:**
The upstream applications (blue/green) are returning 5xx errors at a rate exceeding the configured threshold (default 2%).

**Operator Actions:**
1. **Check Both Containers:**
```bash
   docker-compose logs app_blue --tail=30
   docker-compose logs app_green --tail=30
```

2. **Verify Container Health:**
```bash
   curl http://localhost:8081/healthz  # Blue
   curl http://localhost:8082/healthz  # Green
```

3. **Check Resource Usage:**
```bash
   docker stats --no-stream
```

4. **Identify Root Cause:**
   - Database connection issues?
   - External service outage?
   - Resource exhaustion (CPU/Memory)?
   - Application bugs?

5. **Mitigation Steps:**
   - If one pool is healthy: Force failover to healthy pool
   - If both unhealthy: Investigate shared dependencies
   - Scale up resources if needed
   - Roll back recent deployments

**Expected Duration:** 5-15 minutes to diagnose and resolve

---

### 3. Recovery Alert

**Alert Message:**
```
✅ Recovery Detected
- Pool: blue
- Status: Active
- Time: [timestamp]
```

**What It Means:**
The primary pool has recovered and is serving traffic again.

**Operator Actions:**
1. **Verify Stability:**
   - Monitor for 10 minutes
   - Check error rates remain low
   - Verify no repeat failovers

2. **Document Incident:**
   - Record time of failure
   - Document root cause
   - Note resolution steps

3. **No immediate action required** if metrics remain stable

---

## Alert Configuration

### Environment Variables

Located in `.env`:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
ERROR_RATE_THRESHOLD=2          # Percentage (2%)
WINDOW_SIZE=200                  # Number of requests to track
ALERT_COOLDOWN_SEC=300          # Minimum seconds between alerts (5 min)
```

### Adjusting Thresholds

**Increase Threshold** (fewer alerts, higher tolerance):
```bash
ERROR_RATE_THRESHOLD=5  # 5% error rate
```

**Decrease Cooldown** (more frequent alerts):
```bash
ALERT_COOLDOWN_SEC=60  # 1 minute
```

**Larger Window** (smoother error rate calculation):
```bash
WINDOW_SIZE=500  # Last 500 requests
```

---

## Maintenance Mode

### Suppress Alerts During Planned Maintenance

**Option 1: Stop Alert Watcher**
```bash
docker-compose stop alert_watcher
# Perform maintenance
docker-compose start alert_watcher
```

**Option 2: Increase Cooldown Temporarily**
```bash
# Edit .env
ALERT_COOLDOWN_SEC=3600  # 1 hour

# Restart watcher
docker-compose restart alert_watcher
```

---

## Manual Failover (Planned)

To manually switch active pools:

1. **Edit .env:**
```bash
   ACTIVE_POOL=green  # Switch to green
```

2. **Update Nginx Config:**
```bash
   # Swap backup directive in nginx.conf
   # Make green primary, blue backup
```

3. **Reload Nginx:**
```bash
   docker exec nginx_proxy nginx -s reload
```

4. **Verify:**
```bash
   curl -i http://localhost:8080/version
   # Should show X-App-Pool: green
```

---

## Testing Alerts

### Test Failover Alert
```bash
# Trigger chaos on blue
curl -X POST http://localhost:8081/chaos/start?mode=error

# Generate traffic
for i in {1..10}; do 
  curl -s http://localhost:8080/version
  sleep 1
done

# Expected: Failover alert in Slack within 30 seconds
```

### Test Error Rate Alert
```bash
# Trigger chaos on active pool
curl -X POST http://localhost:8081/chaos/start?mode=error

# Generate high volume traffic
for i in {1..100}; do 
  curl -s http://localhost:8080/version
done

# Expected: Error rate alert in Slack
```

### Stop Chaos
```bash
curl -X POST http://localhost:8081/chaos/stop
curl -X POST http://localhost:8082/chaos/stop
```

---

## Troubleshooting

### Alert Watcher Not Running
```bash
# Check status
docker-compose ps alert_watcher

# View logs
docker-compose logs alert_watcher

# Restart
docker-compose restart alert_watcher
```

### No Alerts in Slack

**Check Webhook URL:**
```bash
# Verify in .env
cat .env | grep SLACK_WEBHOOK_URL

# Test manually
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test Alert"}' \
  YOUR_WEBHOOK_URL
```

**Check Cooldown:**
- Alerts are rate-limited (default 5 minutes)
- Wait for cooldown period to elapse

### False Positive Alerts

**Adjust Thresholds:**
- Increase `ERROR_RATE_THRESHOLD` for less sensitive alerting
- Increase `WINDOW_SIZE` for more stable calculations
- Increase `ALERT_COOLDOWN_SEC` to reduce alert frequency

---

## Emergency Contacts

**On-Call Engineer:** [Your contact info]
**Slack Channel:** #hng-alerts
**Escalation:** [Manager contact]

---

## Monitoring Dashboard

**Check Real-Time Status:**
```bash
# Container health
docker-compose ps

# Recent logs
docker-compose logs --tail=50

# Current active pool
curl -i http://localhost:8080/version | grep X-App-Pool

# Error logs
docker-compose logs nginx | grep error
```

---

## Post-Incident Review

After resolving an incident:

1. Document in incident log
2. Identify root cause
3. Implement preventive measures
4. Update runbook if needed
5. Share learnings with team
