from logger import logger

words = ["hack","illegal","exploit"]

def is_safe(question:str)->bool:
    logger.info("Running guardrail check")

    q = question.lower()
    safe = not any(w in q for w in words)

    if not safe:
        logger.warning("blocked unsafe query")
    
    return safe