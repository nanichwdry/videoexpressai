"""
Extended API endpoints for production desktop app
Add to existing backend/main.py or import as module
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import os
import subprocess
import json
from supabase import create_client, Client
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment="production" if not os.getenv("DEV") else "development",
)

router = APIRouter()

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

class OAuthCallback(BaseModel):
    code: str

class SocialUpload(BaseModel):
    video_url: str
    title: str
    description: str
    tags: Optional[list[str]] = []

class LipsyncRequest(BaseModel):
    avatar_url: str
    audio_url: str

class TrainTwinRequest(BaseModel):
    images: list[str]
    name: str

@router.get("/health")
async def extended_health():
    """Extended health check with all services"""
    return {
        "backend": True,
        "runpod": bool(os.getenv("RUNPOD_ENDPOINT")),
        "supabase": supabase is not None,
        "r2": bool(os.getenv("R2_PUBLIC_BASE_URL")),
        "sentry": bool(os.getenv("SENTRY_DSN")),
    }

@router.post("/oauth/youtube/callback")
async def youtube_oauth_callback(data: OAuthCallback):
    """Exchange YouTube OAuth code for tokens and store in Supabase"""
    try:
        from google_auth_oauthlib.flow import Flow
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "redirect_uris": ["http://localhost:8000/oauth/youtube/callback"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=["https://www.googleapis.com/auth/youtube.upload"],
        )
        flow.redirect_uri = "http://localhost:8000/oauth/youtube/callback"
        
        flow.fetch_token(code=data.code)
        credentials = flow.credentials
        
        # Store in Supabase (encrypted at rest)
        if supabase:
            # Get current user (solo-user: use first user or create)
            users = supabase.table("users").select("id").limit(1).execute()
            if not users.data:
                user = supabase.table("users").insert({"email": "solo@videoexpress.ai"}).execute()
                user_id = user.data[0]["id"]
            else:
                user_id = users.data[0]["id"]
            
            supabase.table("social_tokens").upsert({
                "user_id": user_id,
                "provider": "youtube",
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
                "scope": " ".join(credentials.scopes) if credentials.scopes else None,
            }).execute()
        
        return {"success": True, "provider": "youtube"}
    
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(500, f"OAuth failed: {str(e)}")

@router.post("/oauth/instagram/callback")
async def instagram_oauth_callback(data: OAuthCallback):
    """Exchange Instagram OAuth code for tokens and store in Supabase"""
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.instagram.com/oauth/access_token",
                data={
                    "client_id": os.getenv("INSTAGRAM_CLIENT_ID"),
                    "client_secret": os.getenv("INSTAGRAM_CLIENT_SECRET"),
                    "grant_type": "authorization_code",
                    "redirect_uri": "http://localhost:8000/oauth/instagram/callback",
                    "code": data.code,
                },
            )
            
            if resp.status_code != 200:
                raise HTTPException(400, "Instagram token exchange failed")
            
            token_data = resp.json()
            
            # Store in Supabase
            if supabase:
                users = supabase.table("users").select("id").limit(1).execute()
                if not users.data:
                    user = supabase.table("users").insert({"email": "solo@videoexpress.ai"}).execute()
                    user_id = user.data[0]["id"]
                else:
                    user_id = users.data[0]["id"]
                
                supabase.table("social_tokens").upsert({
                    "user_id": user_id,
                    "provider": "instagram",
                    "access_token": token_data["access_token"],
                    "expires_at": None,  # Long-lived tokens don't expire
                }).execute()
            
            return {"success": True, "provider": "instagram"}
    
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(500, f"OAuth failed: {str(e)}")

@router.post("/social/youtube/upload")
async def upload_to_youtube(data: SocialUpload):
    """Upload video to YouTube using stored tokens"""
    try:
        if not supabase:
            raise HTTPException(500, "Supabase not configured")
        
        # Get tokens
        users = supabase.table("users").select("id").limit(1).execute()
        user_id = users.data[0]["id"]
        
        tokens = supabase.table("social_tokens").select("*").eq("user_id", user_id).eq("provider", "youtube").execute()
        if not tokens.data:
            raise HTTPException(401, "YouTube not connected")
        
        token_data = tokens.data[0]
        
        credentials = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        )
        
        youtube = build("youtube", "v3", credentials=credentials)
        
        # Download video from R2
        import httpx
        import tempfile
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(data.video_url)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(resp.content)
                tmp_path = tmp.name
        
        # Upload to YouTube
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": data.title,
                    "description": data.description,
                    "tags": data.tags,
                    "categoryId": "22",  # People & Blogs
                },
                "status": {
                    "privacyStatus": "public",
                },
            },
            media_body=MediaFileUpload(tmp_path, chunksize=-1, resumable=True),
        )
        
        response = request.execute()
        
        os.unlink(tmp_path)
        
        return {
            "success": True,
            "video_id": response["id"],
            "url": f"https://youtube.com/watch?v={response['id']}",
        }
    
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(500, f"Upload failed: {str(e)}")

@router.post("/social/instagram/upload")
async def upload_to_instagram(data: SocialUpload):
    """Upload video to Instagram using stored tokens"""
    try:
        if not supabase:
            raise HTTPException(500, "Supabase not configured")
        
        users = supabase.table("users").select("id").limit(1).execute()
        user_id = users.data[0]["id"]
        
        tokens = supabase.table("social_tokens").select("*").eq("user_id", user_id).eq("provider", "instagram").execute()
        if not tokens.data:
            raise HTTPException(401, "Instagram not connected")
        
        token_data = tokens.data[0]
        access_token = token_data["access_token"]
        
        # Instagram Graph API upload (simplified)
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Create media container
            resp = await client.post(
                f"https://graph.instagram.com/v18.0/me/media",
                params={
                    "video_url": data.video_url,
                    "caption": f"{data.title}\n\n{data.description}",
                    "access_token": access_token,
                },
            )
            
            if resp.status_code != 200:
                raise HTTPException(400, "Instagram media creation failed")
            
            container_id = resp.json()["id"]
            
            # Publish media
            resp = await client.post(
                f"https://graph.instagram.com/v18.0/me/media_publish",
                params={
                    "creation_id": container_id,
                    "access_token": access_token,
                },
            )
            
            if resp.status_code != 200:
                raise HTTPException(400, "Instagram publish failed")
            
            media_id = resp.json()["id"]
            
            return {
                "success": True,
                "media_id": media_id,
            }
    
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(500, f"Upload failed: {str(e)}")

@router.post("/avatar/lipsync")
async def create_lipsync(data: LipsyncRequest):
    """Queue ACTalker lipsync job"""
    # Placeholder: integrate with RunPod ACTalker worker
    return {"job_id": "placeholder", "status": "QUEUED", "message": "ACTalker integration pending"}

@router.post("/avatar/train-twin")
async def train_digital_twin(data: TrainTwinRequest):
    """Queue LoRA training job for digital twin"""
    # Placeholder: integrate with RunPod training worker
    return {"job_id": "placeholder", "status": "QUEUED", "message": "Training integration pending"}

def validate_video(file_path: str) -> bool:
    """Validate MP4 integrity using ffprobe"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", "-show_streams", file_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False
