"""
GPU Control API - Fixed with correct RunPod GraphQL API
"""

from fastapi import APIRouter, HTTPException
import httpx
import os

router = APIRouter()

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")
RUNPOD_GRAPHQL_URL = "https://api.runpod.io/graphql"

async def gql(query: str, variables: dict = None):
    """Execute GraphQL query with proper error logging"""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            RUNPOD_GRAPHQL_URL,
            headers={
                "Authorization": f"Bearer {RUNPOD_API_KEY}",
                "Content-Type": "application/json"
            },
            json={"query": query, "variables": variables or {}}
        )
        
        if response.status_code != 200:
            raise HTTPException(500, f"RunPod API error {response.status_code}: {response.text}")
        
        data = response.json()
        if "errors" in data:
            raise HTTPException(500, f"RunPod GraphQL errors: {data['errors']}")
        
        return data["data"]

async def get_endpoint(endpoint_id: str):
    """Fetch endpoint with all required fields"""
    query = """
    query {
      myself {
        endpoints {
          id
          gpuIds
          name
          templateId
          workersMin
          workersMax
        }
      }
    }
    """
    
    data = await gql(query)
    endpoints = data["myself"]["endpoints"]
    ep = next((e for e in endpoints if e["id"] == endpoint_id), None)
    
    if not ep:
        raise HTTPException(404, f"Endpoint not found: {endpoint_id}")
    
    return ep

async def set_workers_min(endpoint_id: str, workers_min: int):
    """Update workers using saveEndpoint with all required fields"""
    ep = await get_endpoint(endpoint_id)
    
    mutation = """
    mutation($input: SaveEndpointInput!) {
      saveEndpoint(input: $input) {
        id
        workersMin
        workersMax
      }
    }
    """
    
    variables = {
        "input": {
            "id": ep["id"],
            "gpuIds": ep["gpuIds"],
            "name": ep["name"],
            "templateId": ep["templateId"],
            "workersMax": ep["workersMax"],
            "workersMin": workers_min
        }
    }
    
    return await gql(mutation, variables)

@router.post("/gpu/off")
async def gpu_off():
    """Turn GPU OFF - Set workersMin to 0"""
    result = await set_workers_min(RUNPOD_ENDPOINT_ID, 0)
    return {
        "status": "off",
        "workers_min": result["saveEndpoint"]["workersMin"],
        "workers_max": result["saveEndpoint"]["workersMax"],
        "message": "GPU disabled - no idle costs"
    }

@router.post("/gpu/on")
async def gpu_on():
    """Turn GPU ON - Set workersMin to 1"""
    result = await set_workers_min(RUNPOD_ENDPOINT_ID, 1)
    return {
        "status": "on",
        "workers_min": result["saveEndpoint"]["workersMin"],
        "workers_max": result["saveEndpoint"]["workersMax"],
        "message": "GPU enabled - ready for inference"
    }

@router.get("/gpu/status")
async def gpu_status():
    """Get current GPU status"""
    ep = await get_endpoint(RUNPOD_ENDPOINT_ID)
    return {
        "status": "on" if ep["workersMin"] > 0 else "off",
        "workers_min": ep["workersMin"],
        "workers_max": ep["workersMax"]
    }

@router.post("/gpu/emergency-off")
async def emergency_off():
    """Emergency shutdown - Force workers to 0"""
    try:
        result = await set_workers_min(RUNPOD_ENDPOINT_ID, 0)
        return {
            "status": "emergency_off",
            "workers_min": result["saveEndpoint"]["workersMin"],
            "message": "Emergency shutdown complete"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Emergency shutdown failed: {str(e)}",
            "action_required": "Manually disable endpoint in RunPod dashboard"
        }
