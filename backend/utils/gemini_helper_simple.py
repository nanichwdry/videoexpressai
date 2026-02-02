"""
Simple prompt enhancement without external APIs
"""

async def enhance_prompt(user_prompt: str, style=None) -> dict:
    """Enhance prompt with basic cinematic keywords"""
    
    # Add cinematic keywords
    enhancements = [
        "cinematic",
        "4K quality",
        "professional lighting",
        "detailed",
        "high quality"
    ]
    
    if style:
        enhancements.append(f"{style} style")
    
    enhanced = f"{user_prompt}, {', '.join(enhancements)}"
    
    return {
        "enhanced_prompt": enhanced,
        "original_prompt": user_prompt,
        "used_gemini": False
    }

async def generate_script(topic: str, duration: int = 60) -> dict:
    return {
        "title": topic,
        "scenes": [],
        "used_gemini": False
    }

async def improve_prompt_for_style(prompt: str, target_style: str) -> dict:
    return {
        "improved_prompt": f"{prompt}, {target_style} style",
        "used_gemini": False
    }
