# GPU Control System - Integration Guide

## Why This Design Prevents Runaway Costs

### The Problem
- RunPod Serverless bills per-second of GPU usage
- Idle workers (activeWorkers > 0) = GPUs allocated = billing continues
- Forgetting to scale down = $$$$ wasted on idle GPUs

### The Solution
- **OFF state**: `workersMin = 0` → No GPUs allocated → $0 idle cost
- **ON state**: `workersMin = 1` → 1 GPU ready → Billed only when jobs run
- **Server-side only**: API key never exposed to frontend
- **Safety fallback**: Emergency shutdown + error handling forces workers to 0

### Cost Comparison
| State | Workers | Idle Cost | Job Cost |
|-------|---------|-----------|----------|
| OFF   | 0       | $0/hour   | N/A (cold start required) |
| ON    | 1       | $0/hour*  | $0.30/min when running |

*Serverless only bills when jobs are actively running, not when idle

---

## Backend Integration

### 1. Add to main.py

```python
from api_gpu_control import router as gpu_router

app.include_router(gpu_router)
```

### 2. Update .env

```bash
RUNPOD_API_KEY=your_api_key
RUNPOD_ENDPOINT_ID=your_endpoint_id
```

### 3. Test Endpoints

```bash
# Turn GPU ON
curl -X POST http://localhost:8000/gpu/on

# Turn GPU OFF
curl -X POST http://localhost:8000/gpu/off

# Check status
curl http://localhost:8000/gpu/status

# Emergency shutdown
curl -X POST http://localhost:8000/gpu/emergency-off
```

---

## Frontend Integration

### 1. Add to Dashboard

```tsx
import { GPUToggle } from './components/GPUToggle';

function Dashboard() {
  return (
    <div>
      <GPUToggle />
      {/* Rest of your dashboard */}
    </div>
  );
}
```

### 2. Update API Client

```typescript
// src/api/client.ts
export async function toggleGPU(on: boolean) {
  const endpoint = on ? '/gpu/on' : '/gpu/off';
  const res = await fetch(`http://localhost:8000${endpoint}`, {
    method: 'POST',
  });
  return res.json();
}

export async function getGPUStatus() {
  const res = await fetch('http://localhost:8000/gpu/status');
  return res.json();
}
```

---

## GraphQL Mutations Used

### Update Workers (Primary)

```graphql
mutation UpdateEndpointWorkers($input: UpdateEndpointInput!) {
  updateEndpoint(input: $input) {
    id
    name
    workersMin
    workersMax
  }
}
```

**Variables:**
```json
{
  "input": {
    "id": "your_endpoint_id",
    "workersMin": 0,  // 0 = OFF, 1 = ON
    "workersMax": 3   // Allow scaling when ON
  }
}
```

### Get Status (Query)

```graphql
query GetEndpoint($id: String!) {
  endpoint(id: $id) {
    id
    name
    workersMin
    workersMax
  }
}
```

---

## Safety Features

### 1. Error Fallback
If any error occurs while turning ON, automatically attempts to force workers to 0:

```python
except Exception as e:
    if count > 0:
        try:
            await set_active_workers(0)
        except:
            pass
    raise
```

### 2. Emergency Shutdown
Frontend button + backend endpoint to force workers to 0:

```python
@router.post("/gpu/emergency-off")
async def emergency_off():
    # Force workers to 0, even if other operations fail
```

### 3. Server-Side Only
- API key stored in backend .env
- Frontend never sees credentials
- All RunPod API calls proxied through backend

### 4. Status Polling
Frontend checks status on mount to sync with actual state:

```typescript
useEffect(() => {
  checkStatus();
}, []);
```

---

## Production Checklist

- [ ] Add RUNPOD_API_KEY to backend .env
- [ ] Add RUNPOD_ENDPOINT_ID to backend .env
- [ ] Test /gpu/on endpoint
- [ ] Test /gpu/off endpoint
- [ ] Test emergency shutdown
- [ ] Verify workers=0 in RunPod dashboard when OFF
- [ ] Set up monitoring/alerts for unexpected worker counts
- [ ] Document cold start delay for team (~10-30s)
- [ ] Add toggle to main dashboard
- [ ] Train team to turn OFF when not in use

---

## Cost Monitoring

### Daily Check
```bash
# Check current status
curl http://localhost:8000/gpu/status

# Expected when not in use:
# {"status": "off", "workers_min": 0, "workers_max": 0}
```

### RunPod Dashboard
1. Go to Serverless → Your Endpoint
2. Check "Active Workers" metric
3. Should be 0 when toggle is OFF
4. If > 0 when OFF → Use emergency shutdown

---

## Troubleshooting

### Toggle doesn't work
1. Check backend logs for GraphQL errors
2. Verify RUNPOD_API_KEY has correct permissions
3. Verify RUNPOD_ENDPOINT_ID is correct
4. Try emergency shutdown

### Workers stuck at > 0
1. Click "Emergency OFF" in UI
2. If that fails, manually set in RunPod dashboard:
   - Go to endpoint settings
   - Set Min Workers = 0
   - Save

### Cold start too slow
- Keep toggle ON during active work sessions
- Only turn OFF during breaks/overnight
- Cold start is ~10-30s (acceptable trade-off for $0 idle cost)

---

## Why NOT Pods?

Pods are always-on VMs:
- ❌ Billed 24/7 even when idle
- ❌ Must manually stop/start
- ❌ No auto-scaling

Serverless with this toggle:
- ✅ $0 idle cost when OFF
- ✅ Auto-scales when ON
- ✅ Billed per-second of actual usage
- ✅ One-click ON/OFF

---

## Summary

**This design prevents runaway costs by:**

1. **Zero idle billing**: OFF = 0 workers = $0
2. **Server-side control**: API key never exposed
3. **Safety fallbacks**: Errors force workers to 0
4. **Emergency shutdown**: Manual override if needed
5. **Status visibility**: Always know current state

**Trade-off:**
- Cold start delay (~10-30s) when turning ON
- Acceptable for cost savings vs always-on GPUs
