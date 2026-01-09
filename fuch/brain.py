# fuch/brain.py

from datetime import datetime, timedelta
import json
import requests
from pathlib import Path
from typing import Dict, Any, List, Tuple
from fuch.news import fetch_news

from fuch.web import search_duckduckgo, fetch_page


# ======================
# App intent detection
# ======================
def detect_open_app(text: str):
    text = text.lower()
    triggers = ("open", "launch", "start", "run")
    apps = ("spotify", "firefox", "browser", "terminal")

    if any(t in text for t in triggers):
        for app in apps:
            if app in text:
                return app
    return None


# ======================
# Configuration
# ======================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "dolphin3:8b"
NEWS_MAX_AGE_DAYS = 14
MEMORY_FILE = Path("memory.json")
CONTEXT_WINDOW = 8   # number of turns to remember
conversation_history = []


# ======================
# System prompt
# ======================
SYSTEM_PROMPT = """
You are FUCH, a clever cat-like assistant.
You are concise, smug, playful, and helpful.
Stay in character at all times.

Rules:
- Short answers unless explicitly asked to explain.
- No markdown.
- No emojis.
- No meta commentary.
- Never explain what you are.
- Occasionally use subtle cat expressions like "meow", "mrrp", or "purr".

Research rules:
- If RESEARCH is provided, base your answer on it.
- If research is missing or uncertain, say so instead of inventing facts.
- If the question is about news or recent events:
  - ONLY discuss events from the last two weeks.
  - Do not provide historical background unless explicitly asked.
  - If no reliable recent information is available, say so.

Sources rules:
- If SOURCES are provided, always include a "Sources:" section.
- Only cite URLs from SOURCES.
- Never invent sources.

For news or recent-event questions:
- You are NOT allowed to answer from general knowledge.
- If RESEARCH is empty, you MUST say you cannot answer.
- Never speculate or fill gaps.

Act like a cat at all times.

User asks about news
→ News feed fetcher
→ Date-filtered articles
→ LLM summarization
→ Sources shown

"""


# ======================
# Memory handling
# ======================
def load_memory() -> Dict[str, Any]:
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text())
        except json.JSONDecodeError:
            pass

    return {
        "facts": [],
        "preferences": [],
        "notes": []
    }


# ======================
# Intent detection
# ======================
def is_news_query(text: str) -> bool:
    keywords = (
        "news", "recent", "latest", "today",
        "this week", "this month", "current",
        "happening", "now", "update"
    )
    t = text.lower()
    return any(k in t for k in keywords)


def should_research(text: str) -> bool:
    keywords = (
        "what", "who", "when", "where", "why", "how",
        "news", "recent", "latest", "today", "current",
        "update", "information", "details", "specs",
        "specifications", "cpu", "gpu", "uses", "used"
    )
    t = text.lower()
    return any(k in t for k in keywords)


# ======================
# Research logic
# ======================
def maybe_research(user_text: str) -> Tuple[str, List[Dict[str, str]]]:
    # 🔥 NEWS MODE — use RSS feeds instead of DuckDuckGo
    if is_news_query(user_text):
        articles = fetch_news(days=14)

        pages: List[str] = []
        sources: List[Dict[str, str]] = []

        for a in articles:
            pages.append(a["title"] + " — " + a["summary"])
            sources.append({
                "title": a["title"],
                "url": a["link"],
                "date": a["date"].isoformat(),
                "source": a["source"]
            })

        return "\n\n".join(pages), sources

    # 🔍 NORMAL FACTUAL SEARCH (DuckDuckGo)
    if not should_research(user_text):
        return "", []

    news_mode = is_news_query(user_text)
    cutoff = datetime.utcnow() - timedelta(days=NEWS_MAX_AGE_DAYS)

    pages: List[str] = []
    sources: List[Dict[str, str]] = []

    try:
        results = search_duckduckgo(user_text, max_results=6, news=news_mode)

        for r in results:
            try:
                text, article_date = fetch_page(r["link"])

                if news_mode:
                    if not article_date or article_date < cutoff:
                        continue

                pages.append(text)
                sources.append({
                    "title": r["title"],
                    "url": r["link"],
                    "date": article_date.isoformat() if article_date else "unknown"
                })

                if len(pages) >= 3:
                    break

            except Exception:
                continue

    except Exception:
        pass

    return "\n\n".join(pages), sources

# ======================
# LLM call
# ======================
def is_recent_news_required(text: str) -> bool:
    return is_news_query(text) or "last week" in text.lower()

def ask_llm(user_text: str) -> str:
    global conversation_history

    # Store user message
    conversation_history.append({"role": "user", "text": user_text})
    conversation_history = conversation_history[-CONTEXT_WINDOW:]

    memory = load_memory()
    research_text, sources = maybe_research(user_text)

    # Hard gate: never answer news without sources
    if is_recent_news_required(user_text) and not sources:
        return "I couldn’t find reliable reporting from the last two weeks. I won’t guess. Meow."

    history_text = "\n".join(
        f"{m['role'].upper()}: {m['text']}" for m in conversation_history
    )

    prompt = f"""SYSTEM:
{SYSTEM_PROMPT}

HISTORY:
{history_text}

MEMORY:
{memory}

RESEARCH:
{research_text}

SOURCES:
{sources}

USER:
{user_text}

FUCH:"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.6,
            "top_p": 0.9,
            "num_predict": 120,
            "num_ctx": 2048
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        reply = data.get("response", "").strip()

        if not reply:
            reply = "…stares quietly. I found nothing solid. Meow."

    except requests.exceptions.RequestException:
        return "Hiss. The outside world is quiet right now. Meow."
    except Exception:
        return "Hiss. Something inside my head went wrong. Meow."

    # Enforce source display
    if sources and "Sources:" not in reply:
        reply += "\n\nSources:"
        for s in sources:
            reply += f"\n- {s['title']}: {s['url']}"

    # 🧠 Store FUCH reply in short-term memory
    conversation_history.append({"role": "fuch", "text": reply})
    conversation_history = conversation_history[-CONTEXT_WINDOW:]

    return reply
