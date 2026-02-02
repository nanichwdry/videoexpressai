"""
Gemini AI integration for prompt enhancement and script generation
Optional paid API - only used when user explicitly requests it
"""

import os
import httpx
import google.generativeai as genai
from typing import Optional

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

if GEMINI_API_KEY and GEMINI_API_KEY != "PLACEHOLDER_API_KEY":
    genai.configure(api_key=GEMINI_API_KEY)

async def enhance_prompt(user_prompt: str, style: Optional[str] = None) -> dict:
    """
    Enhance user's basic prompt into a detailed cinematic prompt
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "PLACEHOLDER_API_KEY":
        return {
            "enhanced_prompt": user_prompt,
            "original_prompt": user_prompt,
            "used_gemini": False,
            "error": "Gemini API key not configured"
        }
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        instruction = f"""Transform this basic idea into a detailed, cinematic video prompt optimized for AI video generation.

Guidelines:
- Add camera movements (drone shot, tracking shot, etc.)
- Specify lighting (golden hour, dramatic lighting, etc.)
- Add atmosphere and mood
- Include technical details (4K, cinematic, etc.)
- Keep it under 200 words
- Make it vivid and specific
{f'- Style: {style}' if style else ''}

Return ONLY the enhanced prompt, no explanations.

User's idea: {user_prompt}"""
        
        response = model.generate_content(instruction)
        enhanced = response.text.strip()
        
        return {
            "enhanced_prompt": enhanced,
            "original_prompt": user_prompt,
            "used_gemini": True
        }
            
    except Exception as e:
        return {
            "enhanced_prompt": user_prompt,
            "original_prompt": user_prompt,
            "used_gemini": False,
            "error": str(e)
        }

async def generate_script(topic: str, duration: int = 60) -> dict:
    """Generate a video script with scene descriptions"""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "PLACEHOLDER_API_KEY":
        return {
            "script": "",
            "scenes": [],
            "used_gemini": False,
            "error": "Gemini API key not configured"
        }
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        num_scenes = max(3, duration // 10)
        
        instruction = f"""Create a {duration}-second video script about: {topic}

Format as JSON:
{{
  "title": "Video title",
  "scenes": [
    {{
      "scene_number": 1,
      "duration": 10,
      "visual_prompt": "Detailed visual description for AI video generation",
      "narration": "Voice-over text"
    }}
  ]
}}

Create {num_scenes} scenes. Return ONLY valid JSON, no markdown."""
        
        response = model.generate_content(instruction)
        script_json = response.text.strip()
        
        # Clean JSON if wrapped in markdown
        if script_json.startswith("```"):
            script_json = script_json.split("```")[1]
            if script_json.startswith("json"):
                script_json = script_json[4:]
        
        import json
        script_data = json.loads(script_json)
        
        return {
            "title": script_data.get("title", topic),
            "scenes": script_data.get("scenes", []),
            "used_gemini": True
        }
            
    except Exception as e:
        return {
            "script": "",
            "scenes": [],
            "used_gemini": False,
            "error": str(e)
        }

async def improve_prompt_for_style(prompt: str, target_style: str) -> dict:
    """Adapt a prompt to match a specific visual style"""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "PLACEHOLDER_API_KEY":
        return {
            "improved_prompt": f"{prompt}, {target_style} style",
            "used_gemini": False
        }
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        instruction = f"""Adapt this video prompt to {target_style} style.
Add style-specific keywords and descriptions.
Keep the core concept but enhance for {target_style} aesthetic.

Original: {prompt}

Return ONLY the improved prompt."""
        
        response = model.generate_content(instruction)
        improved = response.text.strip()
        
        return {"improved_prompt": improved, "used_gemini": True}
            
    except Exception as e:
        return {"improved_prompt": f"{prompt}, {target_style} style", "used_gemini": False, "error": str(e)}
