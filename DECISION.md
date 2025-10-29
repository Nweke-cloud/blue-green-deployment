# Implementation Decisions

## Key Technical Choices

### 1. Nginx Backup Directive
Used `backup` on Green service - ensures Green only receives traffic when Blue is down.

**Why:** Simplest, most reliable pattern for primary/backup model required by task.

### 2. Tight Timeouts (3 seconds)
```nginx
proxy_connect_timeout 3s;
proxy_read_timeout 3s;
```

**Why:** Fast failure detection enables quick failover with minimal user impact.

### 3. Immediate Failover (max_fails=1)
```nginx
server app_blue:3000 max_fails=1 fail_timeout=10s;
```

**Why:** Task requires immediate switch after failure. 10s recovery prevents flapping.

### 4. Comprehensive Retry Policy
```nginx
proxy_next_upstream error timeout http_500 http_502 http_503 http_504;
```

**Why:** Covers all failure scenarios (network errors, timeouts, server errors). Ensures zero failed client requests.

### 5. Explicit Header Forwarding
```nginx
proxy_pass_header X-App-Pool;
proxy_pass_header X-Release-Id;
```

**Why:** Task requires these headers for verification. Nginx can drop non-standard headers without explicit config.

## Architecture Decisions

### Same Image for Both Services
Used identical `yimikaade/wonderful:devops-stage-two` for Blue and Green.

**Why:** 
- Task provides single image
- Differentiation via APP_POOL environment variable
- Realistic production pattern

### Docker Compose Health Checks
Implemented health checks with 10s interval, 5s timeout, 3 retries.

**Why:** 
- Visibility into service health
- Helps debugging
- Production-ready practice

### Reused Existing EC2 Instance
Started stopped instance from previous task instead of creating new one.

**Why:**
- Cost-effective
- Docker pre-installed
- Faster setup
- Environmental consideration

## Trade-offs

### Optimized For:
✅ Zero failed client requests  
✅ Fast failover (<10s)  
✅ Simple configuration  
✅ Easy verification  

### Sacrificed (for demo):
❌ SSL/TLS  
❌ Advanced monitoring  
❌ Logging aggregation  
❌ Circuit breakers  

**Justification:** Task focuses on failover mechanics, not production features.

## Production Improvements

If deploying to production, would add:
1. SSL/TLS termination
2. Prometheus + Grafana monitoring
3. ELK stack logging
4. AWS ALB instead of single Nginx
5. Auto-scaling groups
6. Canary deployments
7. Feature flags

## Lessons Learned

✅ **Worked Well:**
- Backup directive simplifies config
- Short timeouts enable fast detection
- Docker Compose is portable (local → cloud)

⚠️ **Challenges:**
- Header forwarding needs explicit config
- Timeout tuning requires testing
- EC2 IP changes on restart

## Conclusion

Implementation achieves:
- ✅ Automatic failover with zero client failures
- ✅ Fast detection (<3s) and recovery (<10s)
- ✅ Simple, maintainable architecture
- ✅ Production-ready patterns
