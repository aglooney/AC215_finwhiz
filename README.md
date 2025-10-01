# FinWhiz 🐋💸

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
- **Privacy-first design** — personal data stays separate from the general model context.  
- **Interactive UI** for chatting, data entry, and visualizing insights.  

---

## Project Structure (prototype)
```
AC215_finwhiz/
├── data/ # Educational datasets & knowledge base
├── user_data/ # Encrypted personal financial data (per user)
├── src/
│ ├── rag/ # RAG pipelines (general + personal)
│ ├── chatbot/ # LLM interface & conversation manager
│ ├── ui/ # Frontend code (chat + dashboards)
│ └── utils/ # Helper scripts
├── tests/ # Unit/integration tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

---

## ⚙️ Tech Stack

- **Backend**: Python, LangChain for RAG pipelines.  
- **Embedding Model**: jina-embeddings-v3
- **LLM**: OpenAI GPT / open-source LLM (configurable).  
- **Database**: Vector database ChromaDB for document retrieval
- **Frontend**: React (or Streamlit/Next.js for rapid prototyping).  
- **Security**: Encryption + separation of personal vs. educational data stores.  

---

## Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/aglooney/AC215_finwhiz.git
   cd FinWhiz
2. **Install Dependencies
    ```bash

    ```
3. Set Environment Variables
    ```bash
    ```
4. Run the app
    ```bash
    ```

## Security and Privacy
- User financial information is stored locally and separately from global knowledge sources.
- No personal data is shared with external services without explicit consent.

## Disclaimer
FinWhiz is an educational tool, not a licensed financial advisor.