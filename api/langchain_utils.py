from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import os
import chroma_utils

output_parser = StrOutputParser()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

DEFAULT_CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-flash-latest")
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
RETRIEVAL_FETCH_K = int(os.getenv("RETRIEVAL_FETCH_K", "20"))


# ── Question Contextualizer ─────────────────────────────────────────

contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


# ── Language Config ──────────────────────────────────────────────────

LANGUAGE_PROMPTS = {
    "English": "Respond in English.",
    "Hindi": "Respond in Hindi (Devanagari script).",
    "Marathi": "Respond in Marathi (Devanagari script).",
    "Tamil": "Respond in Tamil.",
    "Telugu": "Respond in Telugu.",
    "Bengali": "Respond in Bengali.",
    "Gujarati": "Respond in Gujarati.",
    "Kannada": "Respond in Kannada.",
}


# ── QA Prompt (improved for accuracy) ───────────────────────────────

def _build_qa_prompt(language: str = "English"):
    lang_instruction = LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS["English"])
    return ChatPromptTemplate.from_messages([
        ("system",
         "You are an intelligent document assistant. Your primary job is to answer "
         "questions accurately using ONLY the provided context from the uploaded documents.\n\n"
         "RULES:\n"
         "1. Read the context carefully and thoroughly before answering.\n"
         "2. Base your answer strictly on the information found in the context.\n"
         "3. Quote or paraphrase specific parts of the context to support your answer.\n"
         "4. If the context contains the answer, provide a detailed and complete response.\n"
         "5. If the context does NOT contain enough information to fully answer, say so clearly "
         "and then provide supplementary information from your own knowledge, prefixed with "
         "'Beyond the uploaded document:'.\n"
         "6. Never fabricate information that contradicts the context.\n"
         "7. If the context has relevant data (numbers, dates, names), include them precisely.\n\n"
         f"{lang_instruction}"),
        ("system", "Context from uploaded documents:\n\n{context}"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])


qa_prompt = _build_qa_prompt("English")


# ── RAG Chain Builder ────────────────────────────────────────────────

def get_rag_chain(model=DEFAULT_CHAT_MODEL, file_id: int | None = None, language: str = "English"):
    # When a specific file is selected, retrieve more chunks for better accuracy
    if file_id is not None:
        top_k = max(RETRIEVAL_TOP_K, 8)
        fetch_k = max(RETRIEVAL_FETCH_K, 30)
    else:
        top_k = RETRIEVAL_TOP_K
        fetch_k = RETRIEVAL_FETCH_K

    search_kwargs = {
        "k": top_k,
        "fetch_k": max(fetch_k, top_k),
    }
    if file_id is not None:
        search_kwargs["filter"] = {"file_id": file_id}

    retriever = chroma_utils.vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs=search_kwargs,
    )
    llm = ChatGoogleGenerativeAI(model=model, temperature=0.2)
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    prompt = _build_qa_prompt(language)
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    return rag_chain
