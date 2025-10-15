# FinWhiz

**FinWhiz** is an AI-powered financial education app designed to make finance accessible and personalized.  
It leverages **Retrieval-Augmented Generation (RAG)** with a **Large Language Model (LLM)** to provide two complementary experiences:

1. **Financial Education Chatbot**  
   - Ask general finance-related questions (e.g., "What’s the difference between a Roth IRA and a traditional IRA?").  
   - The chatbot retrieves information from curated financial education resources and explains concepts in clear, simple language. 
2. **Personal Finance Assistant**  
   - Securely input your own financial information (e.g., income, expenses, savings goals).  
   - The chatbot uses a dedicated RAG pipeline over your personal data to answer tailored questions like:  
     > "Based on my current spending, how much can I safely put into retirement savings each month?"

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

- **RAG Pipeline**: Python, LangChain
- **API Service**: FastAPI
- **Embedding Model**: jina-embeddings-v3
- **LLM**: gemini-2.5-pro
- **Educational Database**: Vector database ChromaDB for document retrieval
- **User Database**: PostgreSQL with SQLAlchemy
- **Frontend**: React  

---

## Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/aglooney/AC215_finwhiz.git
   cd AC215_finwhiz
2. Example Environment Variables:
    ```bash
    BUCKET_CREDENTIALS=/app/secrets/data-service-account.json
    VERTEXAI_CREDENTIALS=/app/secrets/vertexai-service-account.json
    GCS_BUCKET=fw_ws
    DATABASE_URL=postgresql+psycopg://finwhiz:finwhiz@postgres:5432/finwhiz
    USER_UPLOAD_BUCKET=fw_user_uploads
    AGENT_URL=http://agent:8010
    LLM_URL=http://llm:8001
    ```
3. Run the services
    ```bash
    docker-compose up --build
    ```
4. (Optional) Basic Test for File Upload (just open a new terminal after all services from docker-compose are running)
    ```bash
    bash test_full_pipeline.sh
    ```


## Next Steps
- Add extensive integration testing
- Make the embedding model more robust
- Add support for more types of documents

## Security and Privacy
- User financial information is stored locally and separately from global knowledge sources.
- No personal data is shared with external services without explicit consent.

## Disclaimer
FinWhiz is an educational tool, not a licensed financial advisor.
