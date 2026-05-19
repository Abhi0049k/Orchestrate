import logging
from typing import Dict, Any, Tuple
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser

from llm.prompts import CLASSIFICATION_PROMPT, ESCALATION_PROMPT, RESPONSE_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    llm = ChatOllama(
        model="llama3.2:latest", 
        temperature=0,
        base_url="http://localhost:11434"
    )
except Exception as e:
    logger.error(f"Failed to initialize ChatOllama: {e}")
    llm = None

output_parser = StrOutputParser()

classification_chain = CLASSIFICATION_PROMPT | llm | output_parser
escalation_chain = ESCALATION_PROMPT | llm | output_parser
response_chain = RESPONSE_PROMPT | llm | output_parser

def _invoke_chain(chain, inputs: Dict[str, Any], default_return: Any) -> Any:
    if not llm:
        logger.error("LLM is not initialized.")
        return default_return
        
    try:
        return chain.invoke(inputs)
    except ConnectionError:
        logger.error("Connection Error: Could not reach Ollama at localhost:11434.")
        return default_return
    except Exception as e:
        logger.error(f"LLM Error during inference: {e}")
        return default_return

def classify_ticket(ticket: str, examples: str = "") -> Tuple[str, str]:
    """
    Classifies a ticket into product_area and request_type using few-shot examples.
    """
    res = _invoke_chain(classification_chain, {"ticket": ticket, "examples": examples}, default_return="unknown | unknown")
    parts = res.split("|", 1)
    if len(parts) == 2:
        return parts[0].strip().lower(), parts[1].strip().lower()
    return "unknown", "unknown"

def should_escalate(ticket: str, context: str, confidence: str, examples: str = "") -> Tuple[bool, str]:
    """
    Decides whether a ticket should be escalated and provides justification using few-shot examples.
    """
    res = _invoke_chain(escalation_chain, {"ticket": ticket, "context": context, "confidence": confidence, "examples": examples}, default_return="yes | Error during escalation check")
    parts = res.split("|", 1)
    if len(parts) == 2:
        decision = "yes" in parts[0].strip().lower()
        justification = parts[1].strip()
        return decision, justification
    return True, "Failed to parse escalation decision properly"

def generate_response(ticket: str, domain: str, context: str, examples: str = "") -> str:
    """
    Generates a support response based strictly on context and few-shot examples.
    """
    if not context or context.strip() == "":
        return "I'm escalating this to a human agent because I lack the context to resolve it."
        
    res = _invoke_chain(response_chain, {"ticket": ticket, "domain": domain, "context": context, "examples": examples}, default_return="Error: Unable to generate response at this time.")
    return res.strip()
