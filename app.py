import streamlit as st
import os
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- Page Configuration ---
st.set_page_config(page_title="Enterprise Secure RAG", page_icon="🔐", layout="wide")

# --- 1. Database Connection (Cached to prevent Windows lock errors) ---
@st.cache_resource
def get_qdrant_db():
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    try:
        vector_db = QdrantVectorStore.from_existing_collection(
            embedding=embedding_model,
            collection_name="multi_tenant_kb",
            path="./qdrant_db"
        )
        return vector_db
    except Exception as e:
        st.error(f"Database Error: {e}")
        st.stop()

vector_db = get_qdrant_db()

# --- 2. Sidebar Control Panel ---
with st.sidebar:
    st.title("🔐 Control Panel")
    st.caption("Multi-Tenant RAG Architecture")
    st.divider()
    
    st.subheader("1. Authentication")
    api_key = st.text_input("Google API Key", type="password", help="Requires Gemini 3.8 Flash key")
    
    st.subheader("2. Security Context")
    
    # Track the previous tenant to detect switches
    if "current_tenant" not in st.session_state:
        st.session_state.current_tenant = "tenant_A"

    active_tenant = st.selectbox(
        "Simulate Login As:",
        options=["tenant_A", "tenant_B"],
        format_func=lambda x: "Acme Corp (Tenant A)" if x == "tenant_A" else "Globex Inc (Tenant B)"
    )

    # Immediately purge chat history when switching organizations
    if active_tenant != st.session_state.current_tenant:
        st.session_state.current_tenant = active_tenant
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 3. Main Chat Interface ---
st.title("🏢 Corporate Knowledge Base")
st.info(f"**Security Status:** Authenticated and isolated to `{active_tenant}`. You cannot access data outside your organization.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. The Retrieval & Generation Loop ---
if user_question := st.chat_input(f"Search {active_tenant}'s documents..."):
    
    if not api_key:
        st.warning("⚠️ Please enter your Google API Key in the sidebar to continue.")
        st.stop()

    # Add user message to UI
    with st.chat_message("user"):
        st.markdown(user_question)
    st.session_state.messages.append({"role": "user", "content": user_question})

    # The AI response block
    with st.chat_message("assistant"):
        
        # A. Apply strict tenant-level payload filtering
        tenant_filter = models.Filter(
            must=[models.FieldCondition(
                key="metadata.tenant_id",
                match=models.MatchValue(value=active_tenant)
            )]
        )
        
        retriever = vector_db.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 3, "filter": tenant_filter, "score_threshold": 0.4}
        )
        
        # B. Retrieve authorized context chunks
        with st.spinner("Scanning authorized documents..."):
            retrieved_docs = retriever.invoke(user_question)
            
        # C. Render Security Audit Log
        with st.expander(f"🛡️ Security Audit Log: Retrieved {len(retrieved_docs)} chunks"):
            if retrieved_docs:
                for i, doc in enumerate(retrieved_docs):
                    st.markdown(f"**Chunk {i+1}** | **Source:** `{doc.metadata.get('source', 'Unknown')}`")
                    st.caption(f'"{doc.page_content}"')
                    st.divider()
            else:
                st.warning("Filter blocked the request or no context found above similarity threshold.")

        # D. Generate secure answer with error handling
        context_str = "\n\n".join(doc.page_content for doc in retrieved_docs)
        
        prompt_template = """
        You are a highly secure corporate AI assistant. Answer the question based ONLY on the following context. 
        If the context is empty or the answer is not in the context, you must reply: "I do not have access to that information for your organization."
        
        Context:
        {context}
        
        Question: {question}
        """
        prompt = PromptTemplate.from_template(prompt_template)
        llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash", google_api_key=api_key)
        chain = prompt | llm | StrOutputParser()
        
        with st.spinner("Formulating secure response..."):
            try:
                response = chain.invoke({"context": context_str, "question": user_question})
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_message = str(e)
                if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
                    st.error("⏳ **System Busy:** Rate limit reached on free tier. Please wait approximately 60 seconds before trying again.")
                else:
                    st.error(f"⚠️ **Unexpected Error:** {error_message}")