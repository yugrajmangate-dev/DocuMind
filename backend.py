import os
import faiss
import httpx
import numpy as np
from groq import Groq
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    timeout=httpx.Timeout(60.0, connect=10.0),
    max_retries=2,
)
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are DocuMind AI — an expert document analyst. You provide thorough, detailed, well-structured answers based on the document context provided to you.

Your approach:
- Give **comprehensive, in-depth** answers — not one-liners.
- Use **markdown formatting**: headers, bullet points, bold text, tables when helpful.
- **Infer and elaborate** on what the document implies, don't just quote text literally.
- If the user asks for a summary, give a rich, multi-paragraph overview covering ALL key points.
- If the user asks about a person, describe everything you can find: background, skills, education, projects, achievements, contacts, etc.
- If information is partially available, share what you found and note what's missing.
- Only say information is not found if it is truly absent from all provided context.
- Be warm, professional, and helpful — like a knowledgeable research assistant."""


# ---------- PDF TEXT ----------
def read_pdf(file):
    reader = PdfReader(file)
    return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())


# ---------- CHUNKING ----------
def chunk_text(text, size, overlap):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


# ---------- VECTOR STORE ----------
def create_vectorstore(chunks):
    if not chunks:
        raise ValueError("No text chunks to embed. The PDF may be empty or image-only.")
    embeddings = embed_model.encode(chunks)
    embeddings = np.atleast_2d(np.array(embeddings, dtype=np.float32))
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index, embeddings


# ---------- RETRIEVAL ----------
def retrieve(query, chunks, index, embeddings, k=5):
    q_embed = embed_model.encode([query])
    k = min(k, len(chunks))
    _, idx = index.search(np.array(q_embed, dtype=np.float32), k)
    return [chunks[i] for i in idx[0] if i < len(chunks)]


# ---------- STREAMING LLM RESPONSE ----------
def generate_answer_stream(query, context, chat_history, temp, max_tokens):
    """Stream a detailed response using the document context and chat history."""

    # Build conversation messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add recent chat history for context continuity (last 6 exchanges)
    for role, content in chat_history[-12:]:
        messages.append({"role": role, "content": content})

    # The actual user query with context
    user_prompt = f"""Here is the relevant document content:

---
{context}
---

Based on the document content above, please answer the following question in detail with proper formatting:

**Question:** {query}"""

    messages.append({"role": "user", "content": user_prompt})

    stream = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temp,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content


def generate_answer(query, context, chat_history, temp, max_tokens):
    """Non-streaming fallback."""
    full = ""
    for token in generate_answer_stream(query, context, chat_history, temp, max_tokens):
        full += token
    return full