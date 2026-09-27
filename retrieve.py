import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models

# 1. Initialize client explicitly so we can close it safely on Windows
client = QdrantClient(path="./qdrant_db")
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_db = QdrantVectorStore(
    client=client,
    collection_name="multi_tenant_kb",
    embedding=embedding_model,
)

# 2. Define the Security Boundary
active_user_tenant = "tenant_A" 

tenant_filter = models.Filter(
    must=[
        models.FieldCondition(
            key="metadata.tenant_id",
            match=models.MatchValue(value=active_user_tenant),
        )
    ]
)

# 3. Attach filter AND a score threshold to the retriever
# similarity_score_threshold ensures it only returns good matches
retriever = vector_db.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "k": 2, 
        "filter": tenant_filter,
        "score_threshold": 0.5  
    }
)

# 4. Test the Isolation
query = "What is the secret project?"
print(f"\nUser from {active_user_tenant} asks: '{query}'")

results = retriever.invoke(query)

if not results:
    print("\nAI Database: [ACCESS DENIED or NO RESULTS] - I don't have any information on that.")
else:
    for doc in results:
        print(f"\nRetrieved Context: {doc.page_content}")

# 5. Cleanly close the database connection to prevent Windows shutdown errors
client.close()