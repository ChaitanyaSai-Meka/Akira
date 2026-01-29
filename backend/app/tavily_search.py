import os
import logging
from tavily import TavilyClient
from typing import Optional

logger = logging.getLogger(__name__)


class TavilySearch:
    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            logger.warning("TAVILY_API_KEY not found in environment variables")
            self.client = None
        else:
            self.client = TavilyClient(api_key=api_key)

    def search(self, query: str, max_results: int = 3) -> Optional[str]:
        if not self.client:
            logger.error("Tavily client not initialized. Missing API key.")
            return None

        if not query or not query.strip():
            logger.warning("Tavily search called with blank or whitespace-only query")
            return None

        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="basic",
                include_answer=True,
                include_raw_content=False
            )

            if not response:
                return None

            search_results = []
            
            if response.get("answer"):
                search_results.append(f"Answer: {response['answer']}")
            
            if response.get("results"):
                for idx, result in enumerate(response["results"][:max_results], 1):
                    title = result.get("title", "")
                    content = result.get("content", "")
                    if title or content:
                        search_results.append(f"{idx}. {title}: {content}")

            return "\n\n".join(search_results) if search_results else None

        except Exception as e:
            logger.error(f"Tavily search error: {e}", exc_info=True)
            return None
