import csv
import logging
from config.settings import TICKETS_FILE, OUTPUT_FILE
from cache.cache import TicketCache
from retrieval.example_retriever import few_shot_retriever
from utils.preprocessing import preprocess_ticket
from orchestration.pipeline import process_ticket

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    cache = TicketCache()
    
    if not TICKETS_FILE.exists():
        logger.error(f"Input file not found at: {TICKETS_FILE.resolve()}")
        return
        
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Pre-build the few-shot FAISS index
    few_shot_retriever.build_index()
    
    results = []
    
    logger.info("Starting ticket orchestration pipeline...")
    
    with open(TICKETS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            issue = row.get("Issue", "").strip()
            subject = row.get("Subject", "").strip()
            
            if not issue and not subject:
                logger.warning(f"Row {i+1} has empty Issue and Subject. Skipping.")
                continue
                
            ticket_text = preprocess_ticket(issue, subject)
                
            logger.info(f"\n--- Processing Row {i+1} ---")
            
            res = process_ticket(ticket_text, cache)
            
            res["issue"] = issue
            res["subject"] = subject
            res["company"] = row.get("Company", "")
            
            results.append(res)
            
    fieldnames = ["issue", "subject", "company", "response", "product_area", "status", "request_type", "justification"]
    
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            writer.writerow(res)
            
    logger.info(f"\nPipeline complete! Processed {len(results)} tickets. Output saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
