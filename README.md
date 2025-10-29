# Blue/Green Deployment with Nginx Auto-Failover

## Overview
This project implements a Blue/Green deployment strategy using Nginx as a reverse proxy with automatic failover capabilities. When the primary (Blue) service fails, traffic automatically switches to the backup (Green) service with zero downtime.

## Live Deployment
- **Public IP**: 98.80.9.210
- **Nginx Gateway**: http://98.80.9.210:8080
- **Blue Service**: http://98.80.9.210:8081
- **Green Service**: http://98.80.9.210:8082

## Architecture
```
Client → Nginx (8080) → Blue (8081) [Primary]
                      → Green (8082) [Backup]
```

## Quick Start

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd blue-green-deployment
cp .env.example .env
```

### 2. Start Services
```bash
docker-compose up -d
```

### 3. Verify
```bash
curl -i http://localhost:8080/version
# Expected: X-App-Pool: blue
```

## Testing Failover

### Trigger Failure
```bash
curl -X POST http://localhost:8081/chaos/start?mode=error
```

### Verify Automatic Switch
```bash
curl -i http://localhost:8080/version
# Now shows: X-App-Pool: green
```

### Stop Chaos
```bash
curl -X POST http://localhost:8081/chaos/stop
```

## Configuration

### Nginx Failover Settings
- **max_fails**: 1 (immediate failover)
- **fail_timeout**: 10s (recovery period)
- **Proxy timeouts**: 3s (fast detection)
- **Backup directive**: Green only active when Blue fails

## How It Works

1. **Normal**: All traffic → Blue
2. **Failure**: Blue fails/timeout (>3s)
3. **Failover**: Request retries to Green (same request!)
4. **Result**: Client gets 200 from Green
5. **Recovery**: After 10s, Blue is available again

## Monitoring
```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Test continuous requests
for i in {1..20}; do 
  curl -s -o /dev/null -w "Request $i: %{http_code}\n" http://localhost:8080/version
done
```

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /version` | App version and pool info |
| `GET /healthz` | Health check |
| `POST /chaos/start?mode=error` | Simulate 500 errors |
| `POST /chaos/stop` | Stop simulation |

## Tech Stack
- Docker & Docker Compose
- Nginx (Alpine)
- Node.js application (yimikaade/wonderful:devops-stage-two)

## Author
HNG DevOps Stage 2 Task
