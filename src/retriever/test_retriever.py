# test_retriever.py
import os
import logging
from src.retriever.retriever_module import Retriever  # adjust import if your path is different
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)

def test_retriever():
    try:
        logging.info("Initializing Retriever")
        retriever = Retriever()
        
        # Simple test query
        test_query = "Explain the impact of inflation on the stock market"
        logging.info(f"Querying with: {test_query}")
        
        context = retriever.retrieve(test_query, top_k=5)
        logging.info(f"Retrieved context:\n{context}")

        if context:
            logging.info("Retriever test successful!")
        else:
            logging.warning("Retriever returned empty context.")

    except Exception as e:
        logging.error(f"Error testing retriever: {e}")

if __name__ == "__main__":
    test_retriever()
