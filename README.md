# Blue/Green Deployment with Observability & Alerts

## Overview
Production-grade Blue/Green deployment system with automatic failover, real-time monitoring, and Slack alerting.

## Architecture
```
User → Nginx (Port 8080) → Blue (Port 8081) [Primary]
                         → Green (Port 8082) [Backup]
                         
Alert Watcher → Monitors Nginx Logs → Slack Alerts
```

## Features
- ✅ Zero-downtime deployments
- ✅ Automatic failover (< 3 seconds)
- ✅ Real-time log monitoring
- ✅ Slack alerts for failovers and errors
- ✅ Enhanced Nginx logging with pool/release tracking
- ✅ Configurable error rate thresholds
- ✅ Alert cooldown to prevent spam

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Slack workspace with incoming webhook

### 1. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/blue-green-deployment.git
cd blue-green-deployment
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your Slack webhook URL
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Verify Deployment
```bash
# Check containers
docker-compose ps

# Test endpoint
curl -i http://localhost:8080/version
# Should show: X-App-Pool: blue
```

## Testing Failover

### Trigger Chaos on Blue
```bash
curl -X POST http://localhost:8081/chaos/start?mode=error
```

### Verify Automatic Failover
```bash
curl -i http://localhost:8080/version
# Should now show: X-App-Pool: green
```

**Expected:** Slack alert notification within 30 seconds

### Stop Chaos
```bash
curl -X POST http://localhost:8081/chaos/stop
```

### Verify Recovery
```bash
# Wait 5 seconds
sleep 5

curl -i http://localhost:8080/version
# Should return to: X-App-Pool: blue
```

## Slack Alerts

The system sends alerts for:

1. **Failover Events** - When traffic switches between pools
2. **High Error Rates** - When 5xx errors exceed threshold (default 2%)

### Alert Examples

**Failover Alert:**
```
🚨 HNG DevOps Alert 🚨

*Failover Detected!*
- Previous Pool: blue
- Current Pool: green  
- Time: 2025-10-30 14:23:45 UTC
- Action: Check health of blue container
```

**Error Rate Alert:**
```
🚨 HNG DevOps Alert 🚨

*High Error Rate Alert!*
- Error Rate: 5.50%
- Threshold: 2%
- Errors: 11/200 requests
- Time: 2025-10-30 14:25:10 UTC
- Action: Inspect upstream logs immediately
```

## Configuration

### Environment Variables (.env)
```bash
# Docker Images
BLUE_IMAGE=yimikaade/wonderful:devops-stage-two
GREEN_IMAGE=yimikaade/wonderful:devops-stage-two

# Pool Configuration
ACTIVE_POOL=blue
RELEASE_ID_BLUE=v1.0.0-blue
RELEASE_ID_GREEN=v1.0.0-green

# Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Alert Thresholds
ERROR_RATE_THRESHOLD=2          # Percentage
WINDOW_SIZE=200                  # Request window size
ALERT_COOLDOWN_SEC=300          # 5 minutes between alerts
```

## Nginx Logging

Enhanced access log format captures:
- `pool` - Which pool served the request (blue/green)
- `release` - Release ID from upstream
- `upstream_status` - HTTP status from upstream
- `upstream` - Upstream server address
- `request_time` - Total request time
- `upstream_time` - Upstream response time

### View Logs
```bash
docker exec nginx_proxy tail -f /var/log/nginx/access.log
```

Example log line:
```
172.17.0.1 - - [30/Oct/2025:14:20:15 +0000] "GET /version HTTP/1.1" 200 58 
pool=blue release=v1.0.0-blue upstream_status=200 upstream=172.17.0.2:3000 
request_time=0.015 upstream_time=0.012
```

## Monitoring

### Container Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f alert_watcher
docker-compose logs -f nginx
```

### Check Current Pool
```bash
curl -i http://localhost:8080/version | grep X-App-Pool
```

## Operations

See [runbook.md](runbook.md) for detailed operational procedures including:
- Alert response procedures
- Troubleshooting guide
- Manual failover steps
- Maintenance mode
- Testing procedures

## Architecture Details

### Components

1. **app_blue** - Primary application instance
2. **app_green** - Backup application instance
3. **nginx** - Reverse proxy with failover logic
4. **alert_watcher** - Python service monitoring logs

### Failover Mechanism

- Nginx marks blue as down after 1 failed request
- `fail_timeout=1s` allows quick recovery
- Green has `backup` directive (only used when blue fails)
- Automatic retry on errors/timeouts/5xx responses

### Alert Watcher

- Tails Nginx access logs in real-time
- Detects pool changes (failover events)
- Calculates rolling error rate over sliding window
- Posts to Slack with cooldown to prevent spam

## Troubleshooting

### No Slack Alerts

1. Verify webhook URL in `.env`
2. Test webhook manually:
```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test"}' \
     YOUR_WEBHOOK_URL
```
3. Check alert_watcher logs:
```bash
   docker-compose logs alert_watcher
```

### Failover Not Working

1. Check Nginx configuration:
```bash
   docker exec nginx_proxy nginx -t
```
2. Verify both apps are healthy:
```bash
   curl http://localhost:8081/healthz
   curl http://localhost:8082/healthz
```

### Alert Watcher Crashed
```bash
docker-compose restart alert_watcher
docker-compose logs alert_watcher
```

## Production Considerations

- Add SSL/TLS termination
- Implement Prometheus metrics
- Set up log aggregation (ELK stack)
- Use managed Slack app (not webhook)
- Add circuit breaker patterns
- Implement gradual rollout
- Set up multi-region deployment

## License
MIT

## Author
HNG DevOps Stage 3
