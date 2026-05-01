import logging
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("psc_agent.scraper.html")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def fetch_article(url: str, max_retries: int = 1) -> str:
    headers = {
        "User-Agent": USER_AGENTS[0],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                import random
                headers["User-Agent"] = random.choice(USER_AGENTS)
                logger.info(f"Retry {attempt} for {url} with different User-Agent")

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text

        except requests.exceptions.HTTPError as e:
            if response.status_code == 403 and attempt < max_retries:
                continue
            logger.error(f"HTTP error fetching {url}: {e}")
            return ""
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return ""

    return ""


def extract_article_text(html: str) -> str:
    if not html:
        return ""

    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
        tag.decompose()

    paragraphs = soup.find_all("p")
    text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

    if not text:
        text = soup.get_text(separator="\n", strip=True)

    return text[:5000]


def extract_image(html: str, base_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return og["content"]

    img = soup.find("img", src=True)
    if img:
        src = img["src"]
        if src.startswith("http"):
            return src
        return urljoin(base_url, src)

    return None
