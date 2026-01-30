# RAG (Retrieval Augmented Generation) Service
"""
RAG Service - Learn from historical news to improve predictions.
Uses ChromaDB for vector storage and sentence-transformers for embeddings.
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
from datetime import datetime
import hashlib
import os
import json


# Initialize embedding model (runs locally, no API needed)
_embedding_model = None
_chroma_client = None
_collection = None

# Data directory for persistent storage
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "rag")


def get_embedding_model() -> SentenceTransformer:
    """
    Get or initialize the embedding model (lazy loading).
    Uses all-MiniLM-L6-v2: fast, accurate, small footprint.
    """
    global _embedding_model
    if _embedding_model is None:
        print("Loading embedding model (first time may take a few seconds)...")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding model loaded!")
    return _embedding_model


def get_chroma_collection():
    """
    Get or initialize ChromaDB collection.
    Stores news embeddings with metadata.
    """
    global _chroma_client, _collection
    
    if _collection is None:
        # Ensure data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Initialize persistent ChromaDB client
        _chroma_client = chromadb.PersistentClient(path=DATA_DIR)
        
        # Get or create collection for news
        _collection = _chroma_client.get_or_create_collection(
            name="financial_news",
            metadata={"description": "Financial news with outcomes for RAG"}
        )
        print(f"ChromaDB collection initialized with {_collection.count()} items")
    
    return _collection


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for text.
    
    Args:
        text: Input text (news title + summary)
    
    Returns:
        384-dimensional embedding vector
    """
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def generate_news_id(title: str, source: str) -> str:
    """Generate unique ID for a news item."""
    content = f"{title}:{source}"
    return hashlib.md5(content.encode()).hexdigest()[:16]


def store_news_with_outcome(
    news_id: str,
    title: str,
    summary: str,
    symbol: str,
    asset_type: str,
    sentiment: str,
    confidence: float,
    actual_outcome: Optional[str] = None,
    price_change_percent: Optional[float] = None
) -> bool:
    """
    Store a news item with its analysis outcome for future RAG retrieval.
    
    Args:
        news_id: Unique identifier
        title: News headline
        summary: News summary
        symbol: Trading symbol
        asset_type: 'crypto' or 'stock'
        sentiment: Analyzed sentiment
        confidence: Confidence score
        actual_outcome: What actually happened (optional, for feedback)
        price_change_percent: Actual price change after news (optional)
    
    Returns:
        True if stored successfully
    """
    try:
        collection = get_chroma_collection()
        
        # Combine title and summary for embedding
        text = f"{title}. {summary}"
        embedding = generate_embedding(text)
        
        # Metadata for filtering and context
        metadata = {
            "news_id": news_id,
            "title": title[:500],  # Truncate for storage
            "symbol": symbol,
            "asset_type": asset_type,
            "sentiment": sentiment,
            "confidence": confidence,
            "stored_at": datetime.now().isoformat(),
        }
        
        if actual_outcome:
            metadata["actual_outcome"] = actual_outcome
        if price_change_percent is not None:
            metadata["price_change_percent"] = price_change_percent
        
        # Store in ChromaDB
        collection.upsert(
            ids=[news_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[text[:2000]]  # Store text for reference
        )
        
        return True
        
    except Exception as e:
        print(f"Error storing news: {e}")
        return False


def find_similar_news(
    query_text: str,
    symbol: Optional[str] = None,
    asset_type: Optional[str] = None,
    k: int = 5
) -> List[Dict]:
    """
    Find similar historical news items.
    
    Args:
        query_text: Text to find similar news for
        symbol: Filter by symbol (optional)
        asset_type: Filter by asset type (optional)
        k: Number of results to return
    
    Returns:
        List of similar news items with metadata
    """
    try:
        collection = get_chroma_collection()
        
        if collection.count() == 0:
            return []
        
        # Generate query embedding
        query_embedding = generate_embedding(query_text)
        
        # Build where filter
        where_filter = None
        if asset_type:
            where_filter = {"asset_type": asset_type}
        
        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, collection.count()),
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        if not results or not results['ids'][0]:
            return []
        
        # Format results
        similar_news = []
        for i, news_id in enumerate(results['ids'][0]):
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i]
            
            # Convert distance to similarity score (0-1, higher is better)
            similarity = 1 / (1 + distance)
            
            similar_news.append({
                "news_id": news_id,
                "title": metadata.get("title", ""),
                "symbol": metadata.get("symbol", ""),
                "sentiment": metadata.get("sentiment", ""),
                "confidence": metadata.get("confidence", 0),
                "actual_outcome": metadata.get("actual_outcome"),
                "price_change_percent": metadata.get("price_change_percent"),
                "similarity": round(similarity, 3),
                "stored_at": metadata.get("stored_at", "")
            })
        
        return similar_news
        
    except Exception as e:
        print(f"Error finding similar news: {e}")
        return []


def get_rag_context(
    title: str,
    summary: str,
    asset_type: str,
    k: int = 3
) -> str:
    """
    Get RAG context for LLM analysis.
    Finds similar historical news and formats them for the prompt.
    
    Args:
        title: News title
        summary: News summary
        asset_type: 'crypto' or 'stock'
        k: Number of similar news to include
    
    Returns:
        Formatted context string for LLM prompt
    """
    query_text = f"{title}. {summary}"
    similar_news = find_similar_news(query_text, asset_type=asset_type, k=k)
    
    if not similar_news:
        return ""
    
    # Filter to only include reasonably similar news (similarity > 0.5)
    relevant_news = [n for n in similar_news if n['similarity'] > 0.5]
    
    if not relevant_news:
        return ""
    
    # Format context
    context_parts = ["HISTORICAL CONTEXT (Similar past news and outcomes):"]
    
    for i, news in enumerate(relevant_news, 1):
        context_parts.append(f"\n{i}. \"{news['title'][:100]}...\"")
        context_parts.append(f"   - Past Sentiment: {news['sentiment'].upper()} ({news['confidence']*100:.0f}% confidence)")
        
        if news.get('actual_outcome'):
            context_parts.append(f"   - Actual Outcome: {news['actual_outcome']}")
        if news.get('price_change_percent') is not None:
            direction = "+" if news['price_change_percent'] > 0 else ""
            context_parts.append(f"   - Price Change: {direction}{news['price_change_percent']:.1f}%")
        
        context_parts.append(f"   - Similarity: {news['similarity']*100:.0f}%")
    
    return "\n".join(context_parts)


def get_collection_stats() -> Dict:
    """Get statistics about the RAG collection."""
    try:
        collection = get_chroma_collection()
        return {
            "total_items": collection.count(),
            "status": "healthy"
        }
    except Exception as e:
        return {
            "total_items": 0,
            "status": f"error: {str(e)}"
        }


# Initialize on import (lazy - won't load model until first use)
print("RAG Service module loaded. Model will initialize on first use.")
