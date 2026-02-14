
# import os
# from dotenv import load_dotenv
# from groq import Groq

# # Load environment variables
# load_dotenv()

# # Initialize Groq client
# client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# # Conversation memory
# messages = [
#     {"role": "system", "content": "You are a helpful AI assistant."}
# ]

# print("🤖 Groq Chatbot (type 'exit' to quit)\n")

# while True:
#     user_input = input("You: ")

#     if user_input.lower() == "exit":
#         print("Goodbye 👋")
#         break

#     messages.append({"role": "user", "content": user_input})

#     try:
#         response = client.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=messages,
#             temperature=0.7,
#             max_tokens=1024,
#         )

#         reply = response.choices[0].message.content
#         print("Bot:", reply, "\n")

#         messages.append({"role": "assistant", "content": reply})

#     except Exception as e:
#         print("Error:", e)


import os
import httpx
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv("addon.env")
load_dotenv()

def _get_key(key_name):
    """Get API key from environment or Streamlit secrets."""
    val = os.getenv(key_name)
    if val:
        return val
    try:
        return st.secrets.get(key_name)
    except Exception:
        return None

# ──────────────────────────────────────────────
# MODEL REGISTRY
# ──────────────────────────────────────────────
MODELS = {
    # Groq models (ultra-fast)
    "LLaMA 3.3 70B": {"id": "llama-3.3-70b-versatile", "provider": "groq", "speed": "Ultra Fast", "icon": "⚡"},
    "LLaMA 3.1 8B": {"id": "llama-3.1-8b-instant", "provider": "groq", "speed": "Instant", "icon": "🚀"},
    "Mixtral 8x7B": {"id": "mixtral-8x7b-32768", "provider": "groq", "speed": "Very Fast", "icon": "🔥"},
    "Gemma 2 9B": {"id": "gemma2-9b-it", "provider": "groq", "speed": "Fast", "icon": "💎"},
    # OpenAI models (via API key)
    "GPT-4o": {"id": "gpt-4o", "provider": "openai", "speed": "Moderate", "icon": "🧠"},
    "GPT-4o Mini": {"id": "gpt-4o-mini", "provider": "openai", "speed": "Fast", "icon": "⚙️"},
    # Gemini models (via API key)
    "Gemini 2.0 Flash": {"id": "gemini-2.0-flash", "provider": "gemini", "speed": "Fast", "icon": "✨"},
    "Gemini 1.5 Pro": {"id": "gemini-1.5-pro", "provider": "gemini", "speed": "Moderate", "icon": "🌟"},
}

def get_available_models():
    """Return models whose API keys are configured."""
    available = {}
    for name, info in MODELS.items():
        if info["provider"] == "groq" and _get_key("GROQ_API_KEY"):
            available[name] = info
        elif info["provider"] == "openai" and _get_key("OPENAI_API_KEY"):
            available[name] = info
        elif info["provider"] == "gemini" and _get_key("GEMINI_API_KEY"):
            available[name] = info
    return available

# ──────────────────────────────────────────────
# CLIENTS (lazy init)
# ──────────────────────────────────────────────
_clients = {}

def _get_groq_client():
    if "groq" not in _clients:
        _clients["groq"] = Groq(
            api_key=_get_key("GROQ_API_KEY"),
            timeout=httpx.Timeout(60.0, connect=10.0),
            max_retries=2,
        )
    return _clients["groq"]

def _get_openai_client():
    if "openai" not in _clients:
        from openai import OpenAI
        _clients["openai"] = OpenAI(api_key=_get_key("OPENAI_API_KEY"))
    return _clients["openai"]

def _get_gemini_client():
    if "gemini" not in _clients:
        import google.generativeai as genai
        genai.configure(api_key=_get_key("GEMINI_API_KEY"))
        _clients["gemini"] = genai
    return _clients["gemini"]

# ──────────────────────────────────────────────
# STREAMING RESPONSE
# ──────────────────────────────────────────────
def get_response_stream(messages, model_name="LLaMA 3.3 70B", temperature=0.7):
    """Stream response from any provider."""
    model_info = MODELS.get(model_name, MODELS["LLaMA 3.3 70B"])
    provider = model_info["provider"]
    model_id = model_info["id"]

    if provider == "groq":
        client = _get_groq_client()
        stream = client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    elif provider == "openai":
        client = _get_openai_client()
        stream = client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    elif provider == "gemini":
        genai = _get_gemini_client()
        model = genai.GenerativeModel(model_id)
        # Convert messages to Gemini format
        gemini_msgs = []
        for m in messages:
            if m["role"] == "system":
                continue
            role = "user" if m["role"] == "user" else "model"
            gemini_msgs.append({"role": role, "parts": [m["content"]]})
        
        # Get system instruction
        sys_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
        if sys_msg:
            model = genai.GenerativeModel(model_id, system_instruction=sys_msg)
        
        response = model.generate_content(
            gemini_msgs,
            generation_config=genai.types.GenerationConfig(temperature=temperature),
            stream=True,
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text