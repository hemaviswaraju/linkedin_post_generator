import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY not found in .env file. Using fallback generator.")
else:
    genai.configure(api_key=API_KEY)

# Try to find any working Gemini model
model = None
if API_KEY:
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                model = genai.GenerativeModel(m.name)
                print(f"✅ Using Gemini model: {m.name}")
                break
    except Exception as e:
        print(f"⚠️ Error listing models: {e}. Gemini will not be used.")
        model = None

if model is None:
    print("❌ No working Gemini model. The app will use a fallback template generator.")

app = FastAPI(title="LinkedIn Post Generator")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/style.css")
async def get_css():
    return FileResponse("style.css", media_type="text/css")

@app.get("/script.js")
async def get_js():
    return FileResponse("script.js", media_type="application/javascript")

class PostRequest(BaseModel):
    topic: str
    user_type: str
    tone: Optional[str] = "professional"
    length: Optional[str] = "medium"
    language: Optional[str] = "english"

class PostResponse(BaseModel):
    generated_post: str
    status: str

# ---------- FALLBACK TEMPLATE (works without Gemini) ----------
def fallback_generate(request: PostRequest) -> str:
    topic = request.topic
    utype = request.user_type
    tone = request.tone
    length = request.length
    lang = request.language

    hooks = {
        "professional": "I've been thinking deeply about",
        "casual": "So here's something I realised about",
        "inspiring": "✨ There's something truly transformative about",
        "educational": "Here's a powerful lesson I learned about",
        "funny": "😂 You won't believe what I discovered about"
    }
    hook = hooks.get(tone, hooks["professional"])

    if utype == "student":
        main_para = f"As a student exploring {topic}, I've learned that consistency beats intensity. Small daily steps compound into amazing results.\n\n🎓 What worked for me: stay curious, ask questions, and embrace failure as feedback."
        extra = f"\n\n📚 One practical tip: spend 30 minutes each day learning something new about {topic}. Join communities, attend webinars, and don't hesitate to reach out to experts. Growth happens outside your comfort zone."
    else:
        main_para = f"In my professional journey with {topic}, I've seen that the best teams prioritise psychological safety over perfection. When people feel safe to speak up, innovation flows naturally.\n\n💼 My advice: lead with empathy, communicate clearly, and celebrate progress over perfection."
        extra = f"\n\n🔍 A proven approach: start with a small pilot, gather data, then iterate. {topic} isn't about giant leaps; it's about consistent, thoughtful adjustments that build up over time."

    long_extra = f"\n\n💡 The key insight: most people overestimate what they can do in a month and underestimate what they can achieve in a year with {topic}. Focus on the process, break down goals into weekly actions, review progress, and celebrate small wins. This builds momentum and keeps you motivated."

    cta_map = {
        "professional": "What strategies have worked for you? Let's share insights. 👇",
        "casual": "Would love to hear your take on this! Drop a comment. 💬",
        "inspiring": "Tag someone who needs to see this today! 🔥",
        "educational": "Save this for later and share with your network. 📌",
        "funny": "Tell me I'm not the only one who thinks this! 😂"
    }
    cta = cta_map.get(tone, "Let's discuss in the comments!")

    topic_hashtag = "#" + ''.join(word.capitalize() for word in topic.split()[:2]) if topic.split() else "#Growth"
    hashtags = f"{topic_hashtag} #StudentSuccess #LearningEveryday" if utype == "student" else f"{topic_hashtag} #LeadershipMindset #CareerGrowth"

    if length == "short":
        post = f"{hook} {topic}.\n\n{main_para.split('.')[0]}.\n\n{cta}\n\n{hashtags}"
    elif length == "long":
        post = f"{hook} {topic}.\n\n{main_para}{extra}{long_extra}\n\n{cta}\n\n{hashtags}"
    else:
        post = f"{hook} {topic}.\n\n{main_para}\n\n{cta}\n\n{hashtags}"

    emoji = {"professional":"📊","casual":"😊","inspiring":"⚡","educational":"📚","funny":"🤣"}.get(tone,"💡")
    post = f"{emoji} {post}"

    if lang == "telugu":
        post = post.replace("What strategies", "మీ వ్యూహాలు ఏమిటి?").replace("Would love to hear", "మీ అభిప్రాయం తెలుసుకోవడానికి ఆసక్తిగా ఉంది").replace("Let's discuss", "చర్చిద్దాం")
    elif lang == "hindi":
        post = post.replace("What strategies", "आपकी क्या रणनीतियाँ हैं?").replace("Would love to hear", "आपकी राय जानना अच्छा होगा").replace("Let's discuss", "चर्चा करते हैं")
    return post

# ---------- GEMINI GENERATION (if model is available) ----------
async def gemini_generate(request: PostRequest) -> str:
    if model is None:
        raise Exception("Gemini model not available")

    length_map = {"short": "100-150 words", "medium": "200-300 words", "long": "400-600 words"}
    length_desc = length_map.get(request.length, "200-300 words")

    user_instruction = {
        "student": "Write from a student's perspective – share learning experiences, challenges, and excitement. Use a relatable, enthusiastic tone.",
        "professional": "Write from a working professional's perspective – focus on actionable insights, industry trends, and career growth. Use a confident, authoritative tone."
    }.get(request.user_type, "")

    lang_instruction = {
        "english": "Write the entire post in English.",
        "telugu": "Write the entire post in Telugu language (Telugu script). Use natural Telugu expressions.",
        "hindi": "Write the entire post in Hindi language (Devanagari script). Use natural Hindi expressions."
    }.get(request.language, "Write in English.")

    prompt = f"""
You are an expert LinkedIn content creator. Generate a high‑quality, engaging LinkedIn post.

{lang_instruction}

Audience: {request.user_type.upper()} – {user_instruction}

Topic: {request.topic}
Tone: {request.tone}
Length: {length_desc}

Requirements:
- Start with a strong hook (question, surprising fact, or bold statement).
- Use emojis naturally (1-3 per paragraph) to make the post friendly.
- Use line breaks (double newline) between short paragraphs.
- End with 2-4 relevant hashtags.
- Write in plain text – no markdown, no asterisks.
- Be authentic and valuable.

Now write the post:
"""
    response = model.generate_content(prompt)
    if not response.text:
        raise Exception("Empty response from Gemini")
    return response.text.strip()

@app.post("/generate-post", response_model=PostResponse)
async def create_post(request: PostRequest):
    try:
        # Try Gemini if available
        if model is not None:
            generated = await gemini_generate(request)
            return PostResponse(generated_post=generated, status="success")
        else:
            # Use fallback
            fallback_post = fallback_generate(request)
            return PostResponse(generated_post=fallback_post + "\n\n✨ (Powered by template – Gemini not available)", status="fallback")
    except Exception as e:
        print(f"Generation error: {e}")
        # Fallback on any error
        fallback_post = fallback_generate(request)
        return PostResponse(generated_post=fallback_post + f"\n\n✨ (Fallback: {str(e)[:100]})", status="fallback")