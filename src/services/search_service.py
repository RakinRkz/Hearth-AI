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
            
            # Improved HTML text extractor that better handles content
            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text_parts = []
                    self.in_script_style = False
                    self.skip_tags = {'script', 'style', 'meta', 'noscript', 'iframe', 'svg'}
                    self.preserve_structure_tags = {'p', 'div', 'section', 'article', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'tr', 'td', 'th', 'blockquote'}
                    self.current_tag = None
                
                def handle_starttag(self, tag, attrs):
                    self.current_tag = tag.lower()
                    if self.current_tag in self.skip_tags:
                        self.in_script_style = True
                    # Add spacing for structure
                    elif self.current_tag in self.preserve_structure_tags and self.text_parts and self.text_parts[-1] and not self.text_parts[-1].endswith(' '):
                        self.text_parts.append(' ')
                
                def handle_endtag(self, tag):
                    tag = tag.lower()
                    if tag in self.skip_tags:
                        self.in_script_style = False
                    # Add spacing for structure
                    elif tag in self.preserve_structure_tags and self.text_parts and self.text_parts[-1] and not self.text_parts[-1].endswith(' '):
                        self.text_parts.append(' ')
                
                def handle_data(self, data):
                    if not self.in_script_style:
                        # Preserve numbers and special characters
                        text = data.strip()
                        # Include even short text if it contains numbers or special chars (dates, etc)
                        if text and (len(text) > 2 or any(c.isdigit() for c in text)):
                            self.text_parts.append(text)
                
                def get_text(self) -> str:
                    # Join with space and clean up multiple spaces
                    text = ' '.join(self.text_parts)
                    # Normalize whitespace while preserving some structure
                    import re
                    text = re.sub(r'\s+', ' ', text)
                    return text.strip()
            
            # Create request with headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'close',
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' not in content_type.lower() and 'application/xhtml' not in content_type.lower():
                    print(f"[DEBUG] Skipping {url} - not HTML (type: {content_type})")
                    return ""
                
                # Read and decode content
                raw_content = response.read()
                
                if not raw_content:
                    print(f"[DEBUG] No content received from {url}")
                    return ""
                
                # Try to detect encoding
                encoding = 'utf-8'
                if 'charset=' in content_type:
                    charset = content_type.split('charset=')[-1].split(';')[0].strip()
                    charset = charset.strip('\'"')  # Remove quotes if present
                    if charset and charset.lower() != 'utf-8':
                        encoding = charset
                
                try:
                    html_content = raw_content.decode(encoding)
                except (UnicodeDecodeError, LookupError) as e:
                    print(f"[DEBUG] Encoding {encoding} failed for {url}, trying utf-8 with errors='ignore'")
                    html_content = raw_content.decode('utf-8', errors='ignore')
                
                # Extract text
                extractor = TextExtractor()
                try:
                    extractor.feed(html_content)
                except Exception as e:
                    print(f"[DEBUG] HTML parsing failed for {url}: {e}")
                    return ""
                
                text = extractor.get_text()
                
                if not text:
                    print(f"[DEBUG] No text extracted from {url}")
                    return ""
                
                # Limit to 8000 chars per page to preserve more content
                return text[:8000]
                
        except Exception as e:
            print(f"[DEBUG] Failed to fetch {url}: {e}")
            return ""
    
    def _fetch_contents_parallel(self, results: List['SearchResult'], max_workers: int = 5) -> List['SearchResult']:
        """Fetch content for multiple URLs in parallel with robust error handling."""
        if not results:
            return results
        
        # Increase timeout and workers for better throughput
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all fetch tasks with individual timeouts
            future_to_result = {}
            for result in results:
                try:
                    future = executor.submit(self._fetch_page_content, result.url, timeout=15)
                    future_to_result[future] = result
                except Exception as e:
                    print(f"[DEBUG] Failed to submit fetch task for {result.url}: {e}")
                    result.content = ""
            
            # Collect results as they complete, with overall timeout
            completed = 0
            for future in as_completed(future_to_result, timeout=30):
                result = future_to_result[future]
                try:
                    content = future.result()
                    if content:
                        result.content = content
                        completed += 1
                    else:
                        result.content = ""
                except Exception as e:
                    print(f"[DEBUG] Content fetch exception for {result.url}: {type(e).__name__}: {e}")
                    result.content = ""
        
        print(f"[DEBUG] Successfully fetched content from {completed}/{len(results)} pages")
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
            # Prioritize fetched content, fall back to snippet
            if result.content:
                # Use fetched content (up to 1200 chars per result for better context)
                content_preview = result.content[:1200]
                if len(result.content) > 1200:
                    content_preview += "..."
                source_type = "fetched"
            else:
                # Fall back to snippet if no content was fetched
                content_preview = result.snippet[:400] if len(result.snippet) > 400 else result.snippet
                source_type = "snippet"
            
            # Format with title, URL, and content
            entry = f"[{i}] {result.title}\nURL: {result.url}\nContent ({source_type}):\n{content_preview}"
            
            # Check if adding this would exceed limit
            if total_chars + len(entry) > max_context_chars:
                # Try to fit a partial entry if we have some space left
                if total_chars + 200 < max_context_chars:
                    # At least include title and URL
                    partial_entry = f"[{i}] {result.title}\nURL: {result.url}"
                    context_parts.append(partial_entry)
                    total_chars += len(partial_entry) + 2
                break
                
            context_parts.append(entry)
            total_chars += len(entry) + 2  # +2 for newlines
            sources.append({
                "title": result.title,
                "url": result.url,
                "content": content_preview,
            })
        
        context = "\n\n".join(context_parts)
        print(f"[DEBUG] Context: {len(context)} chars, {len(sources)} sources (fetched={sum(1 for r in results if r.content)})")
        return context, sources
