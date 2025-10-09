import requests

RETRIEVER_URL = "http://retriever:8000/retrieve"
LLM_URL = "http://llm:8001/query"

def main():
    while True:
        user_input = input("\nEnter your query (or 'exit' to quit): ")
        if user_input.lower() == "exit":
            break

        #get context from retrieval
        retriever_resp = requests.post(RETRIEVER_URL, json={"user_query": user_input, "top_k": 5})
        retriever_resp.raise_for_status()
        context = retriever_resp.json().get("context", "")

        #send query and context to llm
        llm_resp = requests.post(LLM_URL, json={"query": user_input, "context": context})
        llm_resp.raise_for_status()
        answer = llm_resp.json().get("answer", "")
        print(f"\nLLM Answer:\n{answer}")

if __name__ == "__main__":
    main()
