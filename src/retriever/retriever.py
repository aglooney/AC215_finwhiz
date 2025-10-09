from fastapi import FastAPI
from pydantic import BaseModel
from .retriever_module import Retriever  # Your retriever class (ChromaDB + embeddings)
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


app = FastAPI()
r = Retriever()

class Query(BaseModel):
    user_query: str
    top_k: int = 5

@app.post("/retrieve")
def retrieve(query: Query):
    context = r.retrieve(query.user_query, top_k = query.top_k)
    logger.info(f"Retrieved {len(context)} results for query.")
    return {"context": context}
