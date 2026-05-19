from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TICKETS_FILE = BASE_DIR.parent / "support_tickets" / "support_tickets.csv"
OUTPUT_FILE = BASE_DIR.parent / "support_tickets" / "output.csv"
SAMPLE_TICKETS_FILE = BASE_DIR.parent / "support_tickets" / "sample_support_tickets.csv"

# Optional overrides if you are running from somewhere else
if not TICKETS_FILE.exists():
    TICKETS_FILE = Path("../support_tickets/support_tickets.csv")
    OUTPUT_FILE = Path("../support_tickets/output.csv")
    SAMPLE_TICKETS_FILE = Path("../support_tickets/sample_support_tickets.csv")
