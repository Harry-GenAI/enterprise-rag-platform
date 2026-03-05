from logger import logger

def rewrite_query(question:str, history:str):

    if len(question.split()) < 4 and history:
        logger.log("rewriting the question from history")
        return f"""
        Converstion:
        {history}

        Follow-up question:
        {question}
        """

        return question
        
