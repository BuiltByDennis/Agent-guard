import re
from core.config import settings

REGEX_SSN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
REGEX_CC = re.compile(r'\b(?:\d[ -]*?){13,16}\b') # Simple PAN approximation
REGEX_API_KEY = re.compile(r'\bsk-[a-zA-Z0-9]{48}\b')

def scan_and_redact(text_content: str) -> tuple[str, bool]:
    """Returns (redacted_text, has_violation)"""
    has_violation = False
    
    if REGEX_SSN.search(text_content) or REGEX_CC.search(text_content) or REGEX_API_KEY.search(text_content):
        has_violation = True
        
    if has_violation and settings.FIREWALL_MODE == "SANITIZE":
        text_content = REGEX_SSN.sub('[REDACTED_BY_FIREWALL]', text_content)
        text_content = REGEX_CC.sub('[REDACTED_BY_FIREWALL]', text_content)
        text_content = REGEX_API_KEY.sub('[REDACTED_BY_FIREWALL]', text_content)
        
    return text_content, has_violation
