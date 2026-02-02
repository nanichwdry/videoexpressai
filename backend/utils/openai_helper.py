"""
OpenAI script generator (alternative to Gemini)
Add OPENAI_API_KEY to .env to use
"""

import os
import httpx
from typing import Optional

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def generate_script_openai(topic: str, duration: int = 60) -> dict:
    """Generate video script using OpenAI GPT-4"""
    
    if not OPENAI_API_KEY:
        return {
            "error": "OPENAI_API_KEY not configured",
            "scenes": []
        }
    
    num_scenes = max(3, duration // 10)
    
    prompt = f"""Generate a {duration}-second video script about: {topic}

Create {num_scenes} scenes. For each scene provide:
1. Scene number
2. Duration in seconds
3. Visual prompt (detailed description for AI video generation)
4. Narration text (voice-over)

Format as JSON:
{{
  "title": "Video title",
  "scenes": [
    {{
      "scene_number": 1,
      "duration": 10,
      "visual_prompt": "Detailed visual description",
      "narration": "Voice-over text"
    }}
  ]
}}

Return ONLY valid JSON, no markdown."""
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",  # Cheaper, faster
                    "messages": [
                        {"role": "system", "content": "You are a professional video scriptwriter. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                }
            )
            
            if response.status_code != 200:
                return {"error": f"OpenAI API error: {response.status_code}", "scenes": []}
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Clean JSON if wrapped in markdown
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            import json
            script = json.loads(content)
            
            return {
                "title": script.get("title", topic),
                "scenes": script.get("scenes", []),
                "used_openai": True
            }
            
    except Exception as e:
        return {"error": str(e), "scenes": []}
