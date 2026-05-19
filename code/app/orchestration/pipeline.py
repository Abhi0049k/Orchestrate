import logging
from typing import Dict, Any

from cache.cache import TicketCache
from retrieval.retriever import hybrid_search
from retrieval.example_retriever import few_shot_retriever
from llm.llm import classify_ticket, should_escalate, generate_response

logger = logging.getLogger(__name__)

def format_examples_for_classification(examples: list) -> str:
    parts = []
    for ex in examples:
        meta = ex["metadata"]
        parts.append(f"Ticket: Subject: {meta['subject']} Issue: {meta['issue']}\nClassification: {meta['product_area']} | {meta['request_type']}")
    return "\n\n".join(parts)

def format_examples_for_escalation(examples: list) -> str:
    parts = []
    for ex in examples:
        meta = ex["metadata"]
        status = "yes" if meta['status'].lower() == "escalated" else "no"
        parts.append(f"Ticket: Subject: {meta['subject']} Issue: {meta['issue']}\nEscalate: {status} | Previous decision: {meta['status']}")
    return "\n\n".join(parts)

def format_examples_for_response(examples: list) -> str:
    parts = []
    for ex in examples:
        meta = ex["metadata"]
        parts.append(f"Ticket: Subject: {meta['subject']} Issue: {meta['issue']}\nResponse: {meta['response']}")
    return "\n\n".join(parts)

def process_ticket(ticket_text: str, cache: TicketCache) -> Dict[str, Any]:
    """
    End-to-end orchestration for a single support ticket.
    Includes caching, retrieval, classification, escalation decision, and generation.
    """
    cached_result = cache.get_ticket(ticket_text)
    if cached_result:
        logger.info("Cache HIT for ticket. Reusing previous response.")
        return cached_result
        
    logger.info("Cache MISS. Processing ticket...")
    
    try:
        retrieved_examples = few_shot_retriever.search_examples(ticket_text, top_k=2)
        logger.info(f"Retrieved {len(retrieved_examples)} highly relevant few-shot examples.")
        class_examples = format_examples_for_classification(retrieved_examples)
        
        product_area, request_type = classify_ticket(ticket_text, examples=class_examples)
        logger.info(f"Classified as: {product_area} | {request_type}")
        
        domain_filter = product_area if product_area in ["hackerrank", "claude", "visa"] else None
        retrieved_chunks = hybrid_search(ticket_text, domain_filter=domain_filter, top_k=3)
        
        best_distance = retrieved_chunks[0]['distance'] if retrieved_chunks and 'distance' in retrieved_chunks[0] else float('inf')
        
        if not retrieved_chunks:
            retrieval_confidence = "WEAK"
        elif best_distance <= 0.65:
            retrieval_confidence = "STRONG"
        elif best_distance <= 0.85:
            retrieval_confidence = "MODERATE"
        else:
            retrieval_confidence = "WEAK"
            
        logger.info(f"Retrieval Confidence: {retrieval_confidence} (Best Distance: {best_distance if best_distance != float('inf') else 'N/A'})")
        
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks):
            text = chunk.get("payload", {}).get("text", "")
            if text:
                context_parts.append(f"--- Document {i+1} ---\n{text}")
                
        context = "\n\n".join(context_parts)
        
        esc_examples = format_examples_for_escalation(retrieved_examples)
        escalate, justification = should_escalate(ticket_text, context, confidence=retrieval_confidence, examples=esc_examples)
        
        status = "escalated" if escalate else "replied"
        if escalate:
            response = "This ticket has been escalated to a human agent."
        else:
            res_examples = format_examples_for_response(retrieved_examples)
            response = generate_response(ticket_text, product_area, context, examples=res_examples)
            
        result = {
            "status": status,
            "product_area": product_area,
            "response": response,
            "justification": justification,
            "request_type": request_type
        }
        
        cache.set_ticket(ticket_text, result)
        return result
        
    except Exception as e:
        logger.error(f"Failed to process ticket: {e}")
        return {
            "status": "error",
            "product_area": "unknown",
            "response": "Internal processing error.",
            "justification": str(e),
            "request_type": "unknown"
        }
