"""
Hybrid Retrieval: BM25 + Dense Embeddings with Reciprocal Rank Fusion (RRF)
Combines keyword matching (BM25) with semantic search (embeddings) for better recall.
"""
import os
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from packages.core_rag.chroma_client import get_collection
from packages.core_rag.embedding import get_embedder, embed_query
from packages.core_rag.rerank import rerank as apply_reranking


def reciprocal_rank_fusion(
    rankings: List[List[Dict[str, Any]]], 
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    Fuse multiple ranked lists using Reciprocal Rank Fusion (RRF).
    
    RRF formula: score = sum(1 / (k + rank)) for each ranking
    
    Args:
        rankings: List of ranked result lists (each result has 'id' and 'text')
        k: Constant to avoid division by zero (default 60 from literature)
    
    Returns:
        Fused and re-ranked results
    """
    fused_scores = {}
    doc_data = {}
    
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            doc_id = doc.get('id') or doc.get('text')  # Use text as fallback ID
            
            # Store document data
            if doc_id not in doc_data:
                doc_data[doc_id] = doc
            
            # Accumulate RRF score
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0
            fused_scores[doc_id] += 1 / (k + rank)
    
    # Sort by fused score
    sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
    
    # Rebuild ranked list with scores
    fused_results = []
    for doc_id in sorted_ids:
        doc = doc_data[doc_id].copy()
        doc['rrf_score'] = fused_scores[doc_id]
        fused_results.append(doc)
    
    return fused_results


def hybrid_retrieve(
    query: str,
    collection_name: str = "rag_documents",
    top_k: int = 10,
    rerank: bool = True,
    filters: Optional[Dict[str, Any]] = None,
    bm25_weight: float = 0.5,
    vector_weight: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval combining BM25 and dense vector search with RRF fusion.
    
    Args:
        query: User query
        collection_name: ChromaDB collection name
        top_k: Number of final results to return
        rerank: Whether to apply cross-encoder reranking
        filters: Metadata filters (plant, line, station, etc.)
        bm25_weight: Weight for BM25 results (not used in RRF, kept for compatibility)
        vector_weight: Weight for vector results (not used in RRF, kept for compatibility)
    
    Returns:
        List of passages with text, metadata, and scores
    """
    collection = get_collection(name=collection_name)
    
    # Fetch all documents from collection (with filters if provided)
    # We need full corpus for BM25
    if filters:
        results = collection.get(where=filters, include=["documents", "metadatas"])
    else:
        results = collection.get(include=["documents", "metadatas"])
    
    all_docs = results.get('documents', [])
    all_metadatas = results.get('metadatas', [])
    all_ids = results.get('ids', [])
    
    # Log for debugging
    if filters:
        print(f"[Hybrid] Filtered to {len(all_docs)} docs with filters: {filters}")
    
    if not all_docs:
        return []
    
    # === BM25 Retrieval ===
    # Tokenize documents (simple whitespace split)
    tokenized_corpus = [doc.lower().split() for doc in all_docs]
    bm25 = BM25Okapi(tokenized_corpus)
    
    # Get BM25 scores
    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)
    
    # Rank by BM25 score
    bm25_ranked_indices = sorted(
        range(len(bm25_scores)), 
        key=lambda i: bm25_scores[i], 
        reverse=True
    )[:top_k * 2]  # Get more candidates for fusion
    
    bm25_results = [
        {
            'id': all_ids[i],
            'text': all_docs[i],
            'metadata': all_metadatas[i],
            'bm25_score': float(bm25_scores[i])
        }
        for i in bm25_ranked_indices
    ]
    
    # === Dense Vector Retrieval ===
    query_embedding = embed_query(query)
    
    vector_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k * 2,  # Get more candidates for fusion
        where=filters,
        include=["documents", "metadatas", "distances"]
    )
    
    vector_ranked = []
    if vector_results['documents'] and vector_results['documents'][0]:
        for i, (doc_id, doc, metadata, distance) in enumerate(zip(
            vector_results['ids'][0],
            vector_results['documents'][0],
            vector_results['metadatas'][0],
            vector_results['distances'][0]
        )):
            vector_ranked.append({
                'id': doc_id,  # Use actual ChromaDB ID
                'text': doc,
                'metadata': metadata,
                'vector_distance': float(distance)
            })
    
    # === Reciprocal Rank Fusion ===
    fused_results = reciprocal_rank_fusion([bm25_results, vector_ranked])
    
    # Take top_k after fusion
    fused_results = fused_results[:top_k]
    
    # === Optional Reranking ===
    if rerank and fused_results:
        reranked = apply_reranking(query, fused_results, top_k=top_k)
        
        # Merge rerank scores with fusion results
        for i, reranked_item in enumerate(reranked):
            reranked_item['final_rank'] = i + 1
            reranked_item['rerank_score'] = reranked_item.get('score', 0.0)
        
        return reranked
    
    return fused_results


def hybrid_retrieve_and_answer(
    query: str,
    collection_name: str = "rag_documents",
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function: hybrid retrieve + format for answer generation.
    
    Returns:
        {
            'passages': List of retrieved passages,
            'context': Formatted context string for LLM
        }
    """
    passages = hybrid_retrieve(
        query=query,
        collection_name=collection_name,
        top_k=top_k,
        rerank=True,
        filters=filters
    )
    
    # Format context for LLM
    context_parts = []
    for i, passage in enumerate(passages, 1):
        metadata = passage.get('metadata', {})
        meta_str = f"[{metadata.get('source', 'N/A')} | {metadata.get('plant', '')} {metadata.get('line', '')}]"
        context_parts.append(f"[{i}] {meta_str}\n{passage['text']}\n")
    
    context = "\n".join(context_parts)
    
    return {
        'passages': passages,
        'context': context
    }
