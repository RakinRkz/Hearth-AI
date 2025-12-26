"""Web search service using DuckDuckGo."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """A web search result."""
    title: str
    url: str
    snippet: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
        }


class SearchService:
    """Service for web search using DuckDuckGo."""
    
    def __init__(self, max_results: int = 5):
        self.max_results = max_results
        self._ddgs = None
    
    def _ensure_initialized(self) -> None:
        """Ensure DuckDuckGo search is initialized."""
        if self._ddgs is None:
            try:
                # Try the new ddgs package first
                from ddgs import DDGS
                self._ddgs = DDGS()
                print("[DEBUG] Using new ddgs package")
            except ImportError:
                try:
                    # Fall back to old package
                    from duckduckgo_search import DDGS
                    self._ddgs = DDGS()
                    print("[DEBUG] Using old duckduckgo_search package")
                except ImportError:
                    raise ImportError(
                        "ddgs is required. Install with: pip install ddgs"
                    )
    
    def search(
        self, 
        query: str, 
        max_results: Optional[int] = None
    ) -> List[SearchResult]:
        """Perform a web search."""
        self._ensure_initialized()
        
        num_results = max_results or self.max_results
        
        try:
            print(f"[DEBUG] Searching for: {query}")
            results = list(self._ddgs.text(
                query, 
                max_results=num_results,
            ))
            print(f"[DEBUG] Raw results: {len(results)}")
            
            search_results = [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", r.get("link", "")),
                    snippet=r.get("body", r.get("snippet", "")),
                )
                for r in results
            ]
            return search_results
        except Exception as e:
            print(f"[DEBUG] Search error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_context_for_query(
        self, 
        query: str, 
        max_results: Optional[int] = None,
        max_context_chars: int = 2000
    ) -> tuple[str, List[Dict[str, Any]]]:
        """Get formatted context and sources from web search.
        
        Args:
            query: Search query
            max_results: Max number of results
            max_context_chars: Max total characters for context (default 2000)
        """
        results = self.search(query, max_results)
        
        if not results:
            return "", []
        
        context_parts = []
        sources = []
        total_chars = 0
        
        for i, result in enumerate(results, 1):
            # Truncate snippet if needed
            snippet = result.snippet[:300] if len(result.snippet) > 300 else result.snippet
            entry = f"[{i}] {result.title}\n{snippet}"
            
            # Check if adding this would exceed limit
            if total_chars + len(entry) > max_context_chars:
                break
                
            context_parts.append(entry)
            total_chars += len(entry) + 2  # +2 for newlines
            sources.append({
                "title": result.title,
                "url": result.url,
                "content": snippet,
            })
        
        context = "\n\n".join(context_parts)
        print(f"[DEBUG] Context truncated to {len(context)} chars, {len(sources)} sources")
        return context, sources
