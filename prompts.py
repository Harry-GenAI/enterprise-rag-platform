PROMPT_VERSION = "enterprise_v1"

def build_prompt(question, context, history):
    return f"""
    PROMPT_VERSION:{PROMPT_VERSION}

    Conversation History:
    {history}

    Knowledge Context:
    {context}

    User Question:
    {question}
    
    Answer clearly using context only.
    """