import json
import boto3
from logger import logger
from langchain_community.vectorstores import FAISS

#Bedrock client
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)

#embd function
def create_embd(query:str):
    logger.info("creating embedding for the query")

    body = {"inputText":query}

    response=bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())
    return result["embedding"]

#load FAISS VDB

logger.info("Loading faiss index")

vector_db = FAISS.load_local(
    "faiss_index",
    embeddings=None,
    allow_dangerous_deserialization=True
)

#Main Retrieval fun

def retrieve_context(query:str, metadata_filter: dict| None = None):

    #step-1: embd user query
    query_vector = create_embd(query)

    #step-2: similarity search with scores
    results = vector_db.similarity_search_with_score_by_vector(
        query_vector,
        k=4
    )
    
    logger.info(f"initially retrieved chunks:{len(results)}")

    #step-3: Metadata filtering
    filtered_docs = []
    
    for doc,score in results:

        if metadata_filter:
            match = all(
            doc.metadata.get(k) == v
            for k,v in metadata_filter.items()
            )

            if not match:
                continue
        
        filtered_docs.append((doc,score))

    logger.info(f"after metadata filtered {len(filtered_docs)}will go to the LLM")

    #step-4: fallback logic
    if not filtered_docs:
        logger.warning("Fallback triggered - no relevant documents")
        return "No relevant company knowledge found", []
    
    #optional confidence fallback(best score comparsion)
    best_score = filtered_docs[0][1]

    if best_score > 1.5:
        logger.warning("Low similarity confidence- fallback activated")
        return "information confidence is low. please refine your question.", []
    
    #step-5 Build context + citations
    context =""
    sources =[]

    for doc, score in filtered_docs:
        context += f"[SOURCE : {doc.metadata.get('source')}]\n"
        context += doc.page_content+"\n\n"
        sources.append(doc.metadata.get("source"))

    return context, list(set(sources))









