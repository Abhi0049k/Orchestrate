import redis
import json
import hashlib
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class TicketCache:
    def __init__(self, host='localhost', port=6379, db=0):
        try:
            self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.client.ping()
            logger.info("Successfully connected to Redis cache.")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed. Caching disabled. Error: {e}")
            self.client = None

    def _generate_key(self, text: str) -> str:
        """Generates a deterministic hash key for a given ticket text to enable prompt caching."""
        normalized = " ".join(text.lower().split())
        return "ticket:" + hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def get_ticket(self, ticket_text: str) -> Optional[Dict[str, Any]]:
        """Retrieves a previously processed ticket from the cache if an identical match exists."""
        if not self.client:
            return None
            
        key = self._generate_key(ticket_text)
        data = self.client.get(key)
        
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None
        return None

    def set_ticket(self, ticket_text: str, result: Dict[str, Any]):
        """Stores the classification and response payload into Redis."""
        if not self.client:
            return
            
        key = self._generate_key(ticket_text)
        self.client.set(key, json.dumps(result))
