# Gemini AI Integration Guide

## Overview

VideoExpress AI uses **Gemini AI as an optional paid API** for:
- ✨ Prompt enhancement (basic → cinematic)
- 📝 Script generation (topic → full video script)
- 🎨 Style adaptation (prompt → styled prompt)

**Philosophy**: Open-source models by default, paid APIs only for creative assistance.

---

## Setup

### 1. Get Gemini API Key

1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### 2. Configure Backend

Edit `backend/.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Test Integration

```bash
# Start backend
start-backend.bat

# Test prompt enhancement
curl -X POST http://localhost:8000/ai/enhance-prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt":"sunset over city","style":"cinematic"}'
```

---

## Features

### 1. Prompt Enhancement

**Transforms basic prompts into detailed cinematic descriptions.**

#### API Endpoint
```
POST /ai/enhance-prompt
```

#### Request
```json
{
  "prompt": "sunset over city",
  "style": "cinematic"  // optional
}
```

#### Response
```json
{
  "enhanced_prompt": "A breathtaking cinematic drone shot soaring over a sprawling metropolis during golden hour, the setting sun casting long dramatic shadows between towering skyscrapers, warm amber light reflecting off glass facades, volumetric god rays piercing through scattered clouds, 4K, cinematic color grading, establishing shot",
  "original_prompt": "sunset over city",
  "used_gemini": true
}
```

#### Frontend Usage
```typescript
import { enhancePrompt } from './api/client';

const result = await enhancePrompt('sunset over city', 'cinematic');
console.log(result.enhanced_prompt);
```

#### UI Integration
- Click "✨ AI Enhance" button in WanControlPanel
- Prompt is automatically enhanced
- Works even without Gemini (returns original prompt)

---

### 2. Script Generation

**Generates complete video scripts with scene breakdowns.**

#### API Endpoint
```
POST /ai/generate-script
```

#### Request
```json
{
  "topic": "The future of AI",
  "duration": 60
}
```

#### Response
```json
{
  "title": "The Future of AI: A New Era",
  "scenes": [
    {
      "scene_number": 1,
      "duration": 10,
      "visual_prompt": "A futuristic cityscape with holographic displays and flying vehicles, neon lights reflecting on wet streets, cyberpunk aesthetic, 4K cinematic",
      "narration": "In the year 2030, artificial intelligence has transformed every aspect of our lives."
    },
    {
      "scene_number": 2,
      "duration": 10,
      "visual_prompt": "Close-up of a humanoid robot's face with glowing blue eyes, intricate mechanical details, dramatic lighting",
      "narration": "Machines now think, learn, and create alongside humans."
    }
  ],
  "used_gemini": true
}
```

#### Frontend Usage
```typescript
import { generateScript } from './api/client';

const script = await generateScript('The future of AI', 60);

// Generate video for each scene
for (const scene of script.scenes) {
  await createJob('RENDER', {
    prompt: scene.visual_prompt,
    duration: scene.duration
  });
}
```

---

### 3. Style Adaptation

**Adapts prompts to specific visual styles.**

#### API Endpoint
```
POST /ai/style-prompt?prompt={prompt}&style={style}
```

#### Request
```
POST /ai/style-prompt?prompt=sunset%20over%20city&style=anime
```

#### Response
```json
{
  "improved_prompt": "Anime-style sunset over a vibrant city, cel-shaded buildings with bold outlines, dramatic sky with pink and orange gradients, Studio Ghibli aesthetic, soft lighting, hand-drawn clouds, warm color palette",
  "used_gemini": true
}
```

#### Supported Styles
- `cinematic` - Hollywood film aesthetic
- `anime` - Japanese animation style
- `realistic` - Photorealistic rendering
- `3d` - 3D rendered look
- `oil_painting` - Classical art style
- `cyberpunk` - Neon-lit futuristic
- `fantasy` - Magical/ethereal

---

## Cost Considerations

### Gemini API Pricing (as of 2024)
- **Free tier**: 60 requests/minute
- **Paid tier**: $0.00025 per 1K characters

### Typical Usage
- Prompt enhancement: ~200 characters → $0.00005
- Script generation: ~2000 characters → $0.0005
- **Cost per video**: ~$0.001 (negligible)

### Monthly Estimate
- 100 videos/month with AI enhancement: ~$0.10
- **Essentially free for solo use**

---

## Fallback Behavior

### Without Gemini API Key

All endpoints work without Gemini:

```json
{
  "enhanced_prompt": "sunset over city",  // Returns original
  "original_prompt": "sunset over city",
  "used_gemini": false,
  "error": "Gemini API key not configured"
}
```

### UI Behavior
- "✨ AI Enhance" button still works
- Returns original prompt if Gemini unavailable
- No errors shown to user
- Seamless degradation

---

## Implementation Details

### Backend (`backend/utils/gemini_helper.py`)

```python
async def enhance_prompt(user_prompt: str, style: Optional[str] = None) -> dict:
    """Enhance prompt using Gemini Pro"""
    if not GEMINI_API_KEY:
        return {
            "enhanced_prompt": user_prompt,
            "used_gemini": False
        }
    
    # Call Gemini API
    response = await client.post(
        f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
        json={...}
    )
    
    return {
        "enhanced_prompt": enhanced_text,
        "used_gemini": True
    }
```

### Frontend (`src/api/client.ts`)

```typescript
export async function enhancePrompt(prompt: string, style?: string) {
  const res = await fetch(`${API_BASE}/ai/enhance-prompt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, style })
  });
  return res.json();
}
```

---

## Testing

### Test Prompt Enhancement
```bash
curl -X POST http://localhost:8000/ai/enhance-prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt":"a cat playing piano"}'
```

### Test Script Generation
```bash
curl -X POST http://localhost:8000/ai/generate-script \
  -H "Content-Type: application/json" \
  -d '{"topic":"space exploration","duration":30}'
```

### Test Style Adaptation
```bash
curl -X POST "http://localhost:8000/ai/style-prompt?prompt=forest&style=anime"
```

---

## Future Enhancements

### Phase 2
- [ ] Voice-over script optimization for TTS
- [ ] Storyboard generation
- [ ] Multi-language support

### Phase 3
- [ ] Character consistency prompts
- [ ] Scene transition suggestions
- [ ] Music/sound effect recommendations

---

## Troubleshooting

### "Gemini API key not configured"
```bash
# Check .env file
cat backend/.env | grep GEMINI

# Should show:
GEMINI_API_KEY=your_key_here
```

### "API quota exceeded"
- Free tier: 60 requests/minute
- Wait 1 minute or upgrade to paid tier
- Fallback: Returns original prompt

### "Invalid API key"
- Verify key at https://aistudio.google.com/app/apikey
- Check for extra spaces in .env
- Restart backend after changing .env

---

## Best Practices

### When to Use AI Enhancement
✅ Basic prompts ("sunset", "city at night")  
✅ Need cinematic quality  
✅ Exploring creative directions  

❌ Already detailed prompts  
❌ Batch processing (use templates)  
❌ Testing/debugging  

### Prompt Engineering Tips
- Start simple, let AI add details
- Specify style for better results
- Review enhanced prompts before generating
- Save good prompts for reuse

---

## Summary

- ✅ **Optional**: Works without Gemini
- ✅ **Cheap**: ~$0.001 per video
- ✅ **Fast**: <2 seconds response
- ✅ **Seamless**: Fallback to original prompt
- ✅ **Powerful**: Transforms basic → cinematic

**Perfect for solo creators who want professional-quality prompts without manual prompt engineering.**
