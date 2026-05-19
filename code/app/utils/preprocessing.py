def preprocess_ticket(issue: str, subject: str) -> str:
    """Applies heuristics to prioritize issue body and down-weight noisy subjects."""
    noisy_keywords = ["help", "issue", "question", "support", "urgent", "error", "bug", "help needed"]
    is_noisy_subject = len(subject) < 8 or any(subject.lower() == k for k in noisy_keywords)
    
    if not issue:
        return f"Subject: {subject}"
    elif is_noisy_subject or not subject:
        return f"Issue Body: {issue}"
    else:
        return f"Issue Body: {issue}\n(Additional Context from Subject: {subject})"
