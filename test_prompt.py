import requests
import logging
import os

logging.basicConfig(level=logging.INFO)

# These URLs should match the Docker Compose service ports
RETRIEVER_URL = os.environ.get("RETRIEVER_URL", "http://localhost:8000/retrieve")
LLM_URL = os.environ.get("LLM_URL", "http://localhost:8001/query")

user_query = "Explain how inflation affects stock prices."

def test_retriever(query: str):
    logging.info("Testing Retriever Service")
    payload = {"user_query": query, "top_k": 5}
    try:
        response = requests.post(RETRIEVER_URL, json=payload)
        response.raise_for_status()
        context = response.json().get("context", "")
        logging.info(f"Retriever Response: {context}")
        return context
    except requests.HTTPError as e:
        logging.error(f"Retriever Request failed: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in Retriever test: {e}")


def test_llm(query: str):
    logging.info("Testing LLM Service...")
    payload = {"query": query, "top_k": 5}  # top_k is optional if LLM needs it
    try:
        response = requests.post(LLM_URL, json=payload)
        response.raise_for_status()
        answer = response.json().get("answer", "")
        logging.info(f"LLM Answer: {answer}")
        return answer
    except requests.HTTPError as e:
        logging.error(f"LLM Request failed: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in LLM test: {e}")


if __name__ == "__main__":
    logging.info(f"Input Query: {user_query}")
    context = test_retriever(user_query)
    answer = test_llm(user_query)
