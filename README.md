# 🏢 Multi-Tenant Enterprise RAG Knowledge Base

A production-grade, secure Retrieval-Augmented Generation (RAG) architecture built to handle multiple corporate tenants within a single vector database infrastructure.

This project demonstrates how to use **Payload Filtering** to achieve strict data isolation, ensuring that users from different organizations can share the same AI infrastructure without ever accessing each other's confidential data. This approach represents the recommended architectural standard for scalable B2B applications, utilizing purely logical separation via filtering within a single collection.

## ✨ Key Features

* **Multi-Tenant Data Isolation:** Implements strict security boundaries using Qdrant's `models.Filter`. Tenant A can never query, retrieve, or view Tenant B's documents.
* **Enterprise Security Audit Log:** A transparent UI component that intercepts the retriever to prove exactly which chunks the AI is authorized to see before generation occurs.
* **Similarity Score Thresholding:** Prevents "vector drift" by enforcing a strict `score_threshold`, ensuring the AI responds with *"Access Denied"* rather than returning irrelevant data when no authorized context is found.
* **Resilient API Handling:** Built-in exception handling for HTTP 429 Rate Limits, gracefully catching Google Gemini free-tier RPM (Requests Per Minute) bottlenecks without crashing the application.
* **Streamlit Admin Harness:** A unified web interface that allows administrators to instantly simulate secure logins across different corporate contexts and test the boundaries of the database.

## 🛠️ Technology Stack

* **Orchestration:** LangChain
* **Vector Database:** Qdrant (Local Persistent Mode)
* **LLM:** Google Gemini (`gemini-3.8-flash`) via `langchain-google-genai`
* **Embeddings:** HuggingFace (`all-MiniLM-L6-v2`)
* **Frontend:** Streamlit

---

## 🚀 Installation & Quickstart

### 1. Clone & Setup Environment

Ensure you are using Python 3.13 or later.

```bash
git clone https://github.com/YOUR_USERNAME/multi-tenant-rag.git
cd multi-tenant-rag

# Create and activate a virtual environment
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Mac/Linux: source .venv/bin/activate

# Install required dependencies
pip install langchain-qdrant qdrant-client langchain-huggingface langchain-google-genai langchain langchain-text-splitters sentence-transformers "scipy>=1.15.1" streamlit

```

### 2. Ingest the Data

Before running the app, you must build the local vector database and tag the payloads with their respective `tenant_id`.

```bash
python ingest.py

```

*This will create a `qdrant_db` folder containing the isolated data for "Acme Corp" and "Globex Inc."*

### 3. Run the Web Interface

Start the Streamlit application. **Do not** run this with the standard Python command.

```bash
streamlit run app.py

```

*Your browser will automatically open to `http://localhost:8501`.*

---

## 🔐 Security Architecture & Testing

Instead of building a separate database for every customer, this system stores all vectors in a single collection and tags each vector with a tenant identifier in its payload. This paradigm allows you to use payload filtering to isolate data at query time, resulting in a highly efficient and scalable system.

When testing the application, you must provide a **Google Gemini API Key**. The key does not store data; it only grants access to the LLM's reasoning engine. The security filtering happens locally inside Qdrant before the prompt is ever sent to Google.

### How to Verify Data Isolation:

1. **Log in as Tenant A (Acme Corp)** using the left sidebar.
2. Ask: *"What was the Q3 revenue?"*
* **Expected Result:** The AI answers "$50 Million". The Audit Log confirms 1 chunk retrieved.


3. **Attempt a Data Breach:** While still logged in as Tenant A, ask: *"What is the secret project?"*
* **Expected Result:** The system blocks the request. The AI replies: *"I do not have access to that information for your organization."* The Audit Log confirms 0 chunks retrieved.


4. **Cross-Tenant Validation:** Switch the sidebar dropdown to **Tenant B (Globex Inc)** and ask the exact same question.
* **Expected Result:** The system recognizes your new authorization token. The AI answers *"Project Orion"* and the exact document chunk is displayed in the Audit Log.
