from fastapi import FastAPI
from pydantic import BaseModel
import uuid
import asyncio

from logger import logger
from db import create_table, save_chat, get_chat_history
from rag import retrieve_context
from llmservice import generate_reply
from prompts import build_prompt
from guardrails import is_safe
from query_rewriter import rewrite_query


# ---------------------------------------------------------
# APP INITIALIZATION
# ---------------------------------------------------------
logger.info("Starting Enterprise RAG API")

create_table()

app = FastAPI()


# ---------------------------------------------------------
# REQUEST / RESPONSE SCHEMAS
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    domain: str | None = None   # metadata filter support


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[str]


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------
@app.get("/")
def health():
    logger.info("Health check called")
    return {"status": "Enterprise Bedrock RAG running"}


# ---------------------------------------------------------
# MAIN CHAT ENDPOINT
# ---------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):

    # create or reuse session
    session_id = req.session_id or str(uuid.uuid4())

    logger.info(f"New chat request | session={session_id}")

    # -----------------------------------------------------
    # Guardrails check
    # -----------------------------------------------------
    if not is_safe(req.message):
        return {
            "answer": "Request blocked by policy.",
            "session_id": session_id,
            "sources": []
        }

    # -----------------------------------------------------
    # Load conversation memory
    # -----------------------------------------------------
    history = get_chat_history(session_id)

    # -----------------------------------------------------
    # Rewrite vague questions
    # -----------------------------------------------------
    rewritten_query = rewrite_query(req.message, history)

    # -----------------------------------------------------
    # Metadata filter (domain routing)
    # -----------------------------------------------------
    metadata_filter = None

    if req.domain:
        metadata_filter = {
            "doc_type": req.domain
        }

    # -----------------------------------------------------
    # Retrieve context from FAISS (non-blocking)
    # -----------------------------------------------------
    
   # rewrite query first
    rewritten_query = rewrite_query(req.message, history)

# safety fallback
    if not rewritten_query:
        rewritten_query = req.message

    context, sources = await asyncio.to_thread(
        retrieve_context,
        rewritten_query,
        metadata_filter
    )

    if not context:
        logger.warning("No retrieval context found")
        context = "No company knowledge found."

    # -----------------------------------------------------
    # Build final prompt
    # -----------------------------------------------------
    prompt = build_prompt(history, context, req.message)

    # -----------------------------------------------------
    # Call LLM
    # -----------------------------------------------------
    answer = await generate_reply(prompt)

    # -----------------------------------------------------
    # Save conversation memory
    # -----------------------------------------------------
    save_chat(session_id, req.message, answer)

    logger.info(f"Response completed | session={session_id}")

    return {
        "answer": answer,
        "session_id": session_id,
        "sources": sources
    }