"""Evaluation module for logging and analyzing RAG system performance."""

import os
import json
from loguru import logger
from datetime import datetime

import config

# Configure logger
logger.add(
    config.LOG_FILE_PATH,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    rotation="10 MB",
    serialize=True  # Write logs as JSON
)

def log_evaluation_data(query: str, retrieved_chunks: list, reranked_chunks: list, response: str, similarity_scores: list, reranker_scores: list):
    """Logs all relevant data for a single query-response cycle."""
    if not config.ENABLE_EVALUATION_LOGGING:
        return

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "query": query,
        "response": response,
        "retrieved_chunks": [
            {
                "chunk_id": chunk["chunk_id"],
                "source": chunk["source"],
                "text": chunk["text"],
                "initial_score": score
            } for chunk, score in zip(retrieved_chunks, similarity_scores)
        ],
        "reranked_chunks": [
            {
                "chunk_id": chunk["chunk_id"],
                "source": chunk["source"],
                "reranker_score": score
            } for chunk, score in zip(reranked_chunks, reranker_scores)
        ],
        "potential_hallucination": check_for_hallucination(response, reranked_chunks)
    }

    logger.info(json.dumps(log_entry))

def check_for_hallucination(response: str, context_chunks: list) -> bool:
    """Checks for potential hallucinations by ensuring the response is grounded in the context."""
    # This is a simple heuristic. A more advanced approach would use an NLI model.
    response_tokens = set(response.lower().split())
    context_tokens = set()
    for chunk in context_chunks:
        context_tokens.update(chunk["text"].lower().split())

    # Calculate the percentage of response tokens that are in the context
    if not context_tokens:
        return True
    
    overlap = len(response_tokens.intersection(context_tokens)) / len(response_tokens)
    
    return overlap < config.HALLUCINATION_DETECTION_THRESHOLD

