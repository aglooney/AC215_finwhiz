# FinWhiz

**FinWhiz** is an AI-powered financial education app designed to make finance accessible and personalized.  
It leverages **Retrieval-Augmented Generation (RAG)** with a **Large Language Model (LLM)** to provide two complementary experiences:

1. **Financial Education Chatbot**  
   - Ask general finance-related questions (e.g., "What’s the difference between a Roth IRA and a traditional IRA?").  
   - The chatbot retrieves information from curated financial education resources and explains concepts in clear, simple language.
<!-- 
2. **Personal Finance Assistant**  
   - Securely input your own financial information (e.g., income, expenses, savings goals).  
   - The chatbot uses a dedicated RAG pipeline over your personal data to answer tailored questions like:  
     > "Based on my current spending, how much can I safely put into retirement savings each month?" -->

---

## Features

- **RAG-powered chatbot** for accurate, context-aware responses.  
- **Two data layers**:
  - **General knowledge base** of financial concepts.  
  - **User-specific knowledge base** for personalized advice.  
<!-- - **Privacy-first design** — personal data stays separate from the general model context.  
- **Interactive UI** for chatting, data entry, and visualizing insights.   -->

---

## Project Structure (prototype)
```
AC215_finwhiz/
├── data/ # Educational datasets & knowledge base
├── user_data/ # Encrypted personal financial data (per user)
├── src/
│ ├── agentic_user_data_processing/ # Session + user document microservice
│ ├── embedder/ # Embedding model and script to create vectordb
│ ├── llm/ # RAG-LLM interface
│ └── query_client/ # Chat Feature
└── README.md # This file
```

---

## ⚙️ Tech Stack

- **Backend**: Python, LangChain for RAG pipelines.  
- **Embedding Model**: jina-embeddings-v3
- **LLM**: gemini-pro-v2.5
- **Educational Database**: Vector database ChromaDB for document retrieval
- **User Database**: PostgreSQL
- **Frontend**: React  

---

## Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/aglooney/AC215_finwhiz.git
   cd AC215_finwhiz
2. Set Environment Variables
    ```bash
    cp .env.example .env  # create locally, file is gitignored
    # inside .env (values shown as examples only)
    GOOGLE_APPLICATION_CREDENTIALS=secrets/reliable-sight-471200-v5.json
    USER_UPLOAD_BUCKET=fw_user_uploads
    DATABASE_URL=postgresql+psycopg://finwhiz:finwhiz@postgres:5432/finwhiz
    GCS_BUCKET=fw_ws
    ```
3. Run the services
    ```bash
    docker-compose up --build agent postgres retriever llm query_client
    ```
4. (Optional) Generate synthetic W-2s for testing
    ```bash
    docker run --rm \
      --entrypoint /bin/bash \
      -v "$(pwd)":/app \
      synthetic_w2 \
      -lc "python -m src.w2.synthetic_w2.cli --count 1 --seed 42 --output-dir synthetic_data/w2/outputs"
    ```

With the stack running you can sanity-check the agent service:
```bash
SESSION_ID=$(curl -s -X POST http://127.0.0.1:8010/sessions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo-user"}' | jq -r .id)

curl -X POST http://127.0.0.1:8010/sessions/$SESSION_ID/w2 \
  -F file=@src/synthetic_data/w2/outputs/w2_000.pdf

curl http://127.0.0.1:8010/sessions/$SESSION_ID/context
```
Uploads are automatically flattened with `pdftk`, so `w2_fields` should be populated even for fillable forms.

## Next Steps
- Integrate the agent-provided context with the RAG-LLM flow so responses combine Chroma results with user-specific data.
- Add fallback logic for non-PDF uploads and extend integration tests around the `/sessions` endpoints.
- Document the end-to-end client workflow once the agent/LLM handshake is finalized.

## Security and Privacy
- User financial information is stored locally and separately from global knowledge sources.
- No personal data is shared with external services without explicit consent.

## Disclaimer
FinWhiz is an educational tool, not a licensed financial advisor.
