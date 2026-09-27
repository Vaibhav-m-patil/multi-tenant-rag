import os
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

# 1. Initialize Embeddings
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Simulate Uploading Documents for Different Tenants
print("Processing tenant documents...")
doc_tenant_a = Document(
    page_content="Acme Corp's Q3 revenue was $50 Million. The CEO is Jane Doe.",
    metadata={"tenant_id": "tenant_A", "source": "financial_report"}
)
doc_tenant_b = Document(
    page_content="Globex Inc's secret project is named Project Orion. The CEO is John Smith.",
    metadata={"tenant_id": "tenant_B", "source": "internal_wiki"}
)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
chunks = text_splitter.split_documents([doc_tenant_a, doc_tenant_b])

# 3. Store in Qdrant (This safely creates the collection if it doesn't exist)
print("Creating and saving to Qdrant...")
vector_db = QdrantVectorStore.from_documents(
    documents=chunks,
    embedding=embedding_model,
    path="./qdrant_db",  # Saves locally in this folder
    collection_name="multi_tenant_kb"
)

print("Documents successfully ingested and partitioned by tenant_id!")