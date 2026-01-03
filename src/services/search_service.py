"""Web search service using DuckDuckGo with content fetching."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import re


@dataclass
class SearchResult:
    """A web search result."""
    title: str
    url: str
    snippet: str
    content: str = ""  # Full content fetched from the page
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "content": self.content,
        }


class SearchService:
    """Service for web search using DuckDuckGo with content fetching."""
    
    def __init__(self, max_results: int = 5, fetch_content: bool = True):
        self.max_results = max_results
        self.fetch_content = fetch_content
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
    
    def _fetch_page_content(self, url: str, timeout: int = 10) -> str:
        """Fetch and extract main text content from a webpage."""
        try:
            import urllib.request
            import urllib.error
            from html.parser import HTMLParser
            
            # Simple HTML text extractor
            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text_parts = []
                    self.skip_tags = {'script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript', 'iframe'}
                    self.current_tag = None
                    self.skip_depth = 0
                
                def handle_starttag(self, tag, attrs):
                    self.current_tag = tag.lower()
                    if self.current_tag in self.skip_tags:
                        self.skip_depth += 1
                
                def handle_endtag(self, tag):
                    if tag.lower() in self.skip_tags and self.skip_depth > 0:
                        self.skip_depth -= 1
                    self.current_tag = None
                
                def handle_data(self, data):
                    if self.skip_depth == 0:
                        text = data.strip()
                        if text and len(text) > 2:
                            self.text_parts.append(text)
                
                def get_text(self) -> str:
                    return ' '.join(self.text_parts)
            
            # Create request with headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' not in content_type.lower():
                    return ""
                
                # Read and decode content
                raw_content = response.read()
                
                # Try to detect encoding
                encoding = 'utf-8'
                if 'charset=' in content_type:
                    encoding = content_type.split('charset=')[-1].split(';')[0].strip()
                
                try:
                    html_content = raw_content.decode(encoding)
                except (UnicodeDecodeError, LookupError):
                    html_content = raw_content.decode('utf-8', errors='ignore')
                
                # Extract text
                extractor = TextExtractor()
                extractor.feed(html_content)
                text = extractor.get_text()
                
                # Clean up the text
                text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
                text = text.strip()
                
                return text[:5000]  # Limit to 5000 chars per page
                
        except Exception as e:
            print(f"[DEBUG] Failed to fetch {url}: {e}")
            return ""
    
    def _fetch_contents_parallel(self, results: List['SearchResult'], max_workers: int = 3) -> List['SearchResult']:
        """Fetch content for multiple URLs in parallel."""
        if not results:
            return results
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all fetch tasks
            future_to_result = {
                executor.submit(self._fetch_page_content, result.url): result 
                for result in results
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_result, timeout=15):
                result = future_to_result[future]
                try:
                    content = future.result()
                    result.content = content
                except Exception as e:
                    print(f"[DEBUG] Content fetch failed for {result.url}: {e}")
                    result.content = ""
        
        return results
    
    def search(
        self, 
        query: str, 
        max_results: Optional[int] = None,
        fetch_content: Optional[bool] = None
    ) -> List[SearchResult]:
        """Perform a web search and optionally fetch page content."""
        self._ensure_initialized()
        
        num_results = max_results or self.max_results
        should_fetch = fetch_content if fetch_content is not None else self.fetch_content
        
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
                    content="",
                )
                for r in results
            ]
            
            # Fetch actual page content if enabled
            if should_fetch and search_results:
                print(f"[DEBUG] Fetching content from {len(search_results)} pages...")
                search_results = self._fetch_contents_parallel(search_results)
                fetched_count = sum(1 for r in search_results if r.content)
                print(f"[DEBUG] Successfully fetched content from {fetched_count} pages")
            
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
        max_context_chars: int = 4000,
        fetch_content: bool = True
    ) -> tuple[str, List[Dict[str, Any]]]:
        """Get formatted context and sources from web search.
        
        Args:
            query: Search query
            max_results: Max number of results
            max_context_chars: Max total characters for context (default 4000)
            fetch_content: Whether to fetch actual page content
        """
        results = self.search(query, max_results, fetch_content=fetch_content)
        
        if not results:
            return "", []
        
        context_parts = []
        sources = []
        total_chars = 0
        
        for i, result in enumerate(results, 1):
            # Use fetched content if available, otherwise use snippet
            if result.content:
                # Use up to 800 chars of actual content per result
                content_preview = result.content[:800]
                if len(result.content) > 800:
                    content_preview += "..."
            else:
                content_preview = result.snippet[:300] if len(result.snippet) > 300 else result.snippet
            
            entry = f"[{i}] {result.title}\nURL: {result.url}\n{content_preview}"
            
            # Check if adding this would exceed limit
            if total_chars + len(entry) > max_context_chars:
                break
                
            context_parts.append(entry)
            total_chars += len(entry) + 2  # +2 for newlines
            sources.append({
                "title": result.title,
                "url": result.url,
                "content": content_preview,
            })
        
        context = "\n\n".join(context_parts)
        print(f"[DEBUG] Context: {len(context)} chars, {len(sources)} sources")
        return context, sources
