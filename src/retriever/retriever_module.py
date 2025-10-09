import os
import logging
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb import PersistentClient
from .sync_chroma import download_chroma_from_gcs  # adjust import

load_dotenv()
logging.basicConfig(level=logging.INFO)

CHROMA_PATH = "/app/src/chroma_storage"
COLLECTION_DIR = "1a90eda1-e932-4e73-89dd-edb1adf9d126"
COLLECTION_NAME = "finwhiz_docs"
GCS_BUCKET = os.getenv("GCS_BUCKET")
GCS_PREFIX = "chroma_storage_backup"  # match your GCS folder name


class Retriever:
    def __init__(self):
        logging.info(f"GCS_BUCKET={GCS_BUCKET}")
        logging.info(f"CHROMA_PATH exists? {os.path.exists(CHROMA_PATH)}")

        # Ensure DB is downloaded
        if not os.path.exists(CHROMA_PATH) or not os.listdir(CHROMA_PATH):
            logging.info("Downloading Chroma database from GCS")
            download_chroma_from_gcs(GCS_BUCKET, GCS_PREFIX, COLLECTION_DIR, CHROMA_PATH)
        else:
            logging.info("Found local Chroma storage.")

        # Initialize Chroma
        logging.info("Initializing ChromaDB client")
        self.client = PersistentClient(path=CHROMA_PATH)
        self.collection = self.client.get_or_create_collection(COLLECTION_NAME)
        self.embedder = None

    def _load_model(self):
        if self.embedder is None:
            logging.info("Loading Jina embedding model...")
            self.embedder = SentenceTransformer(
                "jinaai/jina-embeddings-v3", 
                device="cpu", 
                trust_remote_code=True
            )

    def retrieve(self, query, top_k=5):
        self._load_model()
        logging.info(f"Querying with: {query}")

        query_emb = self.embedder.encode(query, task="retrieval.passage", convert_to_numpy=True)
        if query_emb.ndim == 1:
            query_emb = [query_emb.tolist()]

        results = self.collection.query(query_embeddings=query_emb, n_results=top_k)
        if not results["documents"] or not results["documents"][0]:
            logging.warning("No context retrieved from Chroma.")
            return "No relevant context found in vector database."

        context_info = results["documents"][0]
        context_str = "\n".join(context_info)
        logging.info(f"Retrieved {len(context_info)} context documents.")
        return context_str
