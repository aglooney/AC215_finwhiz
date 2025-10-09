import os
import logging
from langchain_google_vertexai import VertexAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

VERTEXAI_CREDENTIALS = os.environ.get("VERTEXAI_CREDENTIALS")
if VERTEXAI_CREDENTIALS is None:
    raise ValueError("VERTEXAI_CREDENTIALS must be set in environment")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = VERTEXAI_CREDENTIALS

# Initialize the LLM
llm = VertexAI(model_name="gemini-2.5-pro")


def query_llm(prompt: str) -> str:
    """
    Query the VertexAI LLM with a given prompt.
    Returns the LLM's response.
    """
    try:
        response = llm.invoke(prompt)
        return response
    except Exception as e:
        logging.error(f"Error querying LLM: {e}")
        return f"Error: {str(e)}"
