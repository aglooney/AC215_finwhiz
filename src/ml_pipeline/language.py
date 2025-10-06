import os
import chromadb
#from chromadb.config import Settings
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from langchain_google_vertexai import VertexAI
from dotenv import load_dotenv
import logging


logging.basicConfig(level=logging.INFO)
logging.getLogger("sentence-transformers").setLevel(logging.WARNING)
load_dotenv()

CHROMA_PATH="chroma_storage_backup"
COLLECTION_NAME="1a90eda1-e932-4e73-89dd-edb1adf9d126"
BUCKET_CREDENTIALS = os.environ.get("BUCKET_CREDENTIALS")
VERTEXAI_CREDENTIALS = os.environ.get("VERTEXAI_CREDENTIALS")
GCS_BUCKET= os.environ.get('GCS_BUCKET')

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = BUCKET_CREDENTIALS


chroma_client = PersistentClient(path=CHROMA_PATH)

all_collections = chroma_client.list_collections()
logging.info(all_collections)

collection = chroma_client.get_or_create_collection(COLLECTION_NAME)


logging.info("Accessed Data from GCS Bucket")

logging.info("Downloading Embedding Model from HuggingFace")
embedder = SentenceTransformer("jinaai/jina-embeddings-v3", trust_remote_code=True)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = VERTEXAI_CREDENTIALS
language_model = VertexAI(model_name="gemini-2.5-pro")

def query_rag(query, top_k=5):
    query_emb = embedder.encode(query,task="retrieval.query", convert_to_numpy=True).tolist()
    results = collection.query(query_embeddings=[query_emb], n_results=top_k)
    context_info = results['documents'][0]
    context_str = "\n".join(context_info)

    prompt = f"Answer using context: \n{context_str}\n\nQuery:{query}"

    response = language_model.invoke(prompt)

    return response

if __name__ == "__main__":
    query = input("Welcome to FinWhiz. Please ask me a question.")
    response = query_rag(query)
    print(response)