import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="CloseApp API", description="AI-style helpers to craft deal-closing replies and multi-platform outreach copy for small brands and startups.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CloseResponseRequest(BaseModel):
    customer_message: str = Field(..., description="Raw message from the customer/prospect")
    brand_name: Optional[str] = Field(None, description="Brand or business name")
    offer: Optional[str] = Field(None, description="What you sell: product/service and key value")
    tone: Optional[str] = Field("friendly", description="Tone such as friendly, confident, professional, casual")
    language: Optional[str] = Field("en", description="Output language code like en, es, fr")

class CloseResponseVariant(BaseModel):
    label: str
    text: str

class CloseResponseResult(BaseModel):
    brand_name: Optional[str]
    tone: str
    language: str
    variants: List[CloseResponseVariant]


class OutreachRequest(BaseModel):
    platform: str = Field(..., description="Platform like instagram, linkedin, twitter, email, tiktok")
    brand_name: Optional[str] = None
    offer: str = Field(..., description="What you offer")
    target_audience: str = Field(..., description="Who you want to reach")
    goal: str = Field("book a call", description="Desired action: e.g., visit site, reply, book a call, purchase")
    tone: str = Field("friendly", description="Tone of voice")
    language: str = Field("en", description="Language code")

class OutreachResult(BaseModel):
    platform: str
    tone: str
    language: str
    variations: List[str]
    tips: List[str]


def _apply_language(text: str, language: str) -> str:
    # Lightweight, non-ML language switch for demo purposes
    # If language is English or unsupported, return as-is
    if language.lower() in ["en", "english", ""]:  # default
        return text
    # Very simple placeholders for a few languages to signal intent
    translations = {
        "es": "[ES] ",
        "fr": "[FR] ",
        "de": "[DE] ",
        "pt": "[PT] ",
    }
    prefix = translations.get(language.lower(), f"[{language.upper()}] ")
    return prefix + text


def _tone_prefix(tone: str) -> str:
    t = (tone or "friendly").lower()
    mapping = {
        "friendly": "Friendly",
        "confident": "Confident",
        "professional": "Professional",
        "casual": "Casual",
        "warm": "Warm",
        "persuasive": "Persuasive",
    }
    return mapping.get(t, t.capitalize())


@app.get("/")
def root():
    return {"message": "CloseApp Backend is running"}


@app.post("/api/close-response", response_model=CloseResponseResult)
def generate_close_response(payload: CloseResponseRequest):
    if not payload.customer_message.strip():
        raise HTTPException(status_code=400, detail="customer_message is required")

    brand = payload.brand_name or "Our brand"
    offer = payload.offer or "our solution"
    tone = payload.tone or "friendly"
    lang = payload.language or "en"

    # Simple template-based variants
    base_variants = [
        ("Direct Close", f"Thanks for reaching out! Based on what you shared, {offer} is a great fit. If it works for you, I can reserve a spot and get you started today. Should I send the quick checkout link or a calendar to pick a time?"),
        ("Value-First", f"Appreciate your message! To make this easy: {offer} helps you get results fast with minimal setup. We can lock in pricing and onboard you in minutes. Would you prefer a short call or to receive the sign-up link?"),
        ("Objection-Ready", f"Totally understand your questions. Most clients like you chose {offer} because it’s simple and proven. Let me remove any roadblocks—what would help you decide today? I can share a quick demo or send the sign-up link.")
    ]

    variants: List[CloseResponseVariant] = []
    for label, txt in base_variants:
        text = f"{_tone_prefix(tone)} • {brand}: " + txt
        text = _apply_language(text, lang)
        variants.append(CloseResponseVariant(label=label, text=text))

    return CloseResponseResult(brand_name=payload.brand_name, tone=tone, language=lang, variants=variants)


@app.post("/api/outreach", response_model=OutreachResult)
def generate_outreach(payload: OutreachRequest):
    platform = payload.platform.lower()
    tone = payload.tone
    lang = payload.language
    brand = payload.brand_name or "We"
    offer = payload.offer
    audience = payload.target_audience
    goal = payload.goal

    if platform not in {"instagram", "linkedin", "twitter", "x", "email", "tiktok"}:
        raise HTTPException(status_code=400, detail="Unsupported platform. Use instagram, linkedin, twitter/x, email, tiktok")

    def wrap(text: str) -> str:
        return _apply_language(f"{_tone_prefix(tone)} • {text}", lang)

    variations: List[str] = []
    tips: List[str] = []

    if platform == "instagram":
        variations = [
            wrap(f"Hey {audience}! {brand} helps you with {offer}. Want a quick before/after and how it works? Drop a 🔥 and I’ll DM details. {goal.title()} in 2 clicks."),
            wrap(f"Creators/Founders: struggling with {audience}? We’re helping teams with {offer}. Comment ‘GO’ and I’ll send a 20-sec overview and {goal} link."),
        ]
        tips = ["Keep it short, use an emoji hook", "Call to comment or DM for next step", "Use carousel to show quick proof"]

    elif platform == "linkedin":
        variations = [
            wrap(f"Hi {audience}, I noticed you’re exploring ways to improve {offer}. We recently helped a team like yours and I’d be glad to share a 2-min summary. Open to a brief chat to {goal}?"),
            wrap(f"{brand} helps {audience} achieve results with {offer}. If streamlining this is on your roadmap, I can share a concise one-pager and a link to {goal}."),
        ]
        tips = ["Personalize with their role/company", "Lead with outcomes, not features", "End with a soft ask"]

    elif platform in {"twitter", "x"}:
        variations = [
            wrap(f"{audience}, quick win: {offer}. DMs open—happy to share a 60-sec rundown and a link to {goal}."),
            wrap(f"We’re shipping tools for {audience}: {offer}. Reply ‘info’ and I’ll send the breakdown + {goal} link."),
        ]
        tips = ["One clear benefit", "Invite replies/DMs", "Keep < 280 chars"]

    elif platform == "email":
        variations = [
            wrap(f"Subject: Quick idea for {audience}\n\nHi there — Noticed you’re working on {offer}. We helped similar teams see fast results. If helpful, I can share a 2-min summary and a link to {goal}. Open to it?"),
            wrap(f"Subject: {offer} in a week\n\nHi — We built a simple way for {audience} to get results from {offer}. Happy to send a one-pager and next steps to {goal}. Interested?"),
        ]
        tips = ["Clear subject line", "Keep body 3–5 sentences", "One simple ask"]

    elif platform == "tiktok":
        variations = [
            wrap(f"Hook: Struggling with {audience}?\n\nShow: 3 quick cuts of {offer} results\nCTA: Comment ‘GO’ and I’ll DM how to {goal}."),
            wrap(f"POV: You need {offer}.\nB-Roll + captions → Outcome\nCTA: Link in bio to {goal}."),
        ]
        tips = ["Lead with a strong hook in first 2s", "Use captions and on-screen text", "Clear CTA to comment or link in bio"]

    return OutreachResult(platform=platform, tone=tone, language=lang, variations=variations, tips=tips)


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
