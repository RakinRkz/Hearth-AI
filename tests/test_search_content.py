#!/usr/bin/env python3
"""Quick test to verify search service is fetching content properly."""

import sys
from pathlib import Path

# Add src to path (this file lives in tests/, so src/ is one level up)
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from services.search_service import SearchService


def test_search_with_content():
    """Test that search service fetches page content."""
    service = SearchService(max_results=3, fetch_content=True)
    
    # Test with a query that should return factual information
    query = "what is today's date"
    print(f"\n📝 Testing search with query: '{query}'")
    print("=" * 60)
    
    # Get context and sources
    context, sources = service.get_context_for_query(query, max_context_chars=5000)
    
    print(f"\n✅ Context Retrieved ({len(context)} chars):")
    print("-" * 60)
    print(context[:1000] if len(context) > 1000 else context)
    if len(context) > 1000:
        print(f"... ({len(context) - 1000} more characters)")
    
    print(f"\n📊 Sources ({len(sources)} total):")
    print("-" * 60)
    for i, source in enumerate(sources, 1):
        has_content = "✓ fetched" if len(source["content"]) > 100 else "✗ snippet only"
        print(f"{i}. {source['title']} {has_content}")
        print(f"   URL: {source['url']}")
        if source["content"]:
            preview = source["content"][:150].replace('\n', ' ')
            print(f"   Content: {preview}...")
        print()


if __name__ == "__main__":
    test_search_with_content()
