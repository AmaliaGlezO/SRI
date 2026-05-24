"""Fetch full content from URLs for web search results."""

import asyncio
from typing import List
from urllib.parse import urlparse
import requests
#import cloudscraper
from bs4 import BeautifulSoup

from src.utils.logger import get_logger
from src.config import DEFAULT_TIMEOUT 
logger = get_logger("ContentFetcher")

class ContentFetcher:
    """Fetch and extract main content from web pages."""

 

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        #self.scraper = cloudscraper.create_scraper()

    def _get(self, url: str) -> requests.Response:
        response = self.session.get(url, timeout=self.timeout)
        if response.status_code == 403:
            logger.info(f"Got 403 for {url}, retrying with cloudscraper")
            #response = self.scraper.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response

    def fetch(self, url: str) -> str:
        """Fetch content from a single URL."""
        try:
            response = self._get(url)
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            domain = urlparse(url).netloc
            
            # Brave Search: extract LLM snippet content
            if "search.brave.com" in domain:
                llm_snippet = soup.select_one("#llm-snippet .chatllm-content")
                if llm_snippet:
                    text = llm_snippet.get_text(separator="\n", strip=True)
                    lines = [line.strip() for line in text.split("\n")]
                    text = "\n".join(line for line in lines if line)
                    if text:
                        logger.info(f"Extracted LLM snippet from Brave page {url}")
                        return text
                logger.info(f"No LLM snippet found on Brave page, falling back to standard extraction")
            
            # Yandex: extract result links and fetch their content
            if "yandex" in domain:
                links = []
                for a in soup.find_all("a", class_="b-serp-item__title-link"):
                    href = a.get("href")
                    if href and "youtube.com" not in href and "youtu.be" not in href:
                        links.append(href)
                        if len(links) == 3:
                            break
                
                if links:
                    logger.info(f"Extracted {len(links)} links from Yandex page {url}")
                    contents = []
                    for link in links:
                        content = self.fetch(link)
                        if content:
                            contents.append(content)
                    return "\n\n---\n\n".join(contents) if contents else ""
            
            # Remove scripts and styles
            for tag in soup(["script", "style", "nav", "header", "footer"]):
                tag.decompose()
            
            # Get text
            text = soup.get_text(separator="\n", strip=True)
            
            lines = [line.strip() for line in text.split("\n")]
            text = "\n".join(line for line in lines if line)
            
            return text
            
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return ""

    def fetch_all(self, urls: List[str], max_workers: int = 3) -> List[str]:
        """Fetch multiple URLs in parallel."""
        if not urls:
            return []
        
        results = []
        for url in urls:
            content = self.fetch(url)
            results.append(content)
        
        return results


def fetch_content_from_urls(urls: List[str], timeout: int = DEFAULT_TIMEOUT) -> List[str]:
    """Convenience function to fetch content from URLs."""
    fetcher = ContentFetcher(timeout=timeout)
    return fetcher.fetch_all(urls) 