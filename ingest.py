import os
import json
import boto3
from logger import logger
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

#Bedrock client

bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)

#Create embd function
#text -> vector

def create_embedding(text:str):
    
    logger.info("Creating embedding")

    body = {"inputText":text}

    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())
    
    return result["embedding"]

#load pdf docs
def load_documents(folder="docs"):
    
    logger.info("loading PDF documents from folder docs folder")

    documents = []

    for file in os.listdir(folder):
        
        if not file.endswith(".pdf"):
            continue

        path = os.path.join(folder,file)

        logger.info(f"Reading file:{file}")

        loader = PyPDFLoader(path)
        docs = loader.load()
        #--------------------------
        #metadata attachment(which will be use for filter and citations)
        #--------------------------

        for d in docs:
            d.metadata["source"] = file
            d.metadata["doc_type"]=file.replace(".pdf","")
            d.metadata["department"]="general"
        
        documents.extend(docs)

    logger.info(f"Total pages loaded:{len(documents)}")
    
    return documents

#Chunk docs

def chunk_documents(data):

    logger.info("Chunking documents")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(data)

    logger.info(f"documents has been chunked with {len(chunks)} chunks" )

    return chunks


#Build FAISS

def build_faiss_index(chunks):
    logger.info("generating embeddings and building faiss")

    embeddings = []

    texts = [c.page_content for c in chunks]
    metadatas = [c.metadata for c in chunks]

    for text in texts:
        embeddings.append(create_embedding(text))
    
    vector_db = FAISS.from_embeddings(
        list(zip(texts,embeddings)),
        embedding=None,
        metadatas=metadatas
    )

    return vector_db

#MAIN INGESTION PP:

def main():

    logger.info("starting ingestion pipeline")

    docs = load_documents()
    chunks = chunk_documents(docs)
    vector_db = build_faiss_index(chunks)

    logger.info("saving FAISS index to faiss_index/")
    vector_db.save_local("faiss_index")

    logger.info("Ingestion completed successfully")

if __name__ == "__main__":
    main()



            







