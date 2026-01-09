# fuch/web.py
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def extract_date_from_text(text: str):
    patterns = [
        r"(\d{4}-\d{2}-\d{2})",
        r"(\w+ \d{1,2}, \d{4})",
        r"(\d{1,2} \w+ \d{4})",
    ]

    for p in patterns:
        match = re.search(p, text)
        if match:
            try:
                return datetime.fromisoformat(match.group(1))
            except Exception:
                continue

    return None




HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def search_duckduckgo(query, max_results=5):
    url = "https://duckduckgo.com/html/"
    params = {"q": query}

    r = requests.post(url, data=params, headers=HEADERS, timeout=15)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    results = []

    for result in soup.select(".result__a", limit=max_results):
        title = result.get_text()
        link = result["href"]
        results.append({"title": title, "link": link})

    return results


HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_page(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Try to get published date from meta tags
    date = None
    for prop in ["article:published_time", "og:published_time", "pubdate"]:
        tag = soup.find("meta", {"property": prop}) or soup.find("meta", {"name": prop})
        if tag and tag.get("content"):
            try:
                date = datetime.fromisoformat(tag["content"].replace("Z", ""))
                break
            except Exception:
                pass

    # Also try <time datetime="">
    if not date:
        time_tag = soup.find("time")
        if time_tag and time_tag.get("datetime"):
            try:
                date = datetime.fromisoformat(time_tag["datetime"].replace("Z", ""))
            except Exception:
                pass

    # Extract text
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = " ".join(soup.stripped_strings)
    return text[:4000], date

