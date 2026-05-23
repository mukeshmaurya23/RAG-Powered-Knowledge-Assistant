from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest, SourceCitation
from langchain_utils import get_rag_chain
from db_utils import (
    insert_application_logs, get_chat_history, get_all_documents,
    insert_document_record, delete_document_record, get_analytics_data,
    get_chat_history_for_export
)
from chroma_utils import index_document_to_chroma, delete_doc_from_chroma
import os
import uuid
import logging
logging.basicConfig(filename='app.log', level=logging.INFO)
app = FastAPI(title="LangChain RAG Chatbot API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_source_citations(context_docs) -> list[SourceCitation]:
    citations: list[SourceCitation] = []
    for doc in context_docs[:6]:
        metadata = getattr(doc, "metadata", {}) or {}
        page_value = metadata.get("page")
        page_number = page_value + 1 if isinstance(page_value, int) else None
        snippet = (getattr(doc, "page_content", "") or "").strip().replace("\n", " ")[:240]

        citations.append(
            SourceCitation(
                file_id=metadata.get("file_id"),
                source=metadata.get("source"),
                page=page_number,
                snippet=snippet,
            )
        )
    return citations


def _estimate_confidence(source_count: int) -> str:
    if source_count >= 4:
        return "high"
    if source_count >= 2:
        return "medium"
    if source_count >= 1:
        return "low"
    return "none"

@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):
    session_id = query_input.session_id
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question}, Model: {query_input.model.value}")
    if not session_id:
        session_id = str(uuid.uuid4())

    

    chat_history = get_chat_history(session_id)
    rag_chain = get_rag_chain(query_input.model.value, query_input.file_id, query_input.language)
    result = rag_chain.invoke({
        "input": query_input.question,
        "chat_history": chat_history
    })
    answer = result.get('answer', '')
    sources = _build_source_citations(result.get("context", []))
    source_count = len(sources)
    confidence = _estimate_confidence(source_count)
    
    insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")
    return QueryResponse(
        answer=answer,
        session_id=session_id,
        model=query_input.model,
        sources=sources,
        source_count=source_count,
        confidence=confidence,
    )

import shutil

@app.post("/upload-doc")
def upload_and_index_document(file: UploadFile = File(...)):
    allowed_extensions = ['.pdf', '.docx', '.html', '.txt', '.csv', '.pptx']
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")

    # Use a safe temp file path with uuid to avoid name collisions and special char issues
    import tempfile
    temp_dir = tempfile.gettempdir()
    safe_name = f"{uuid.uuid4().hex}{file_extension}"
    temp_file_path = os.path.join(temp_dir, safe_name)

    try:
        # Save the uploaded file to a temporary file
        with open(temp_file_path, "wb") as buffer:
            content = file.file.read()
            if not content:
                raise HTTPException(status_code=400, detail="Received empty file. Please try uploading again.")
            buffer.write(content)
            logging.info(f"Saved temp file: {temp_file_path} ({len(content)} bytes)")

        file_id = insert_document_record(file.filename)
        success, error_detail = index_document_to_chroma(temp_file_path, file_id)

        if success:
            return {"message": f"File {file.filename} has been successfully uploaded and indexed.", "file_id": file_id}
        else:
            delete_document_record(file_id)
            detail = f"Failed to index {file.filename}. {error_detail or ''}".strip()
            if error_detail and "No extractable text found" in error_detail:
                raise HTTPException(status_code=400, detail=detail)
            if error_detail and "No usable text chunks found" in error_detail:
                raise HTTPException(status_code=400, detail=detail)
            if error_detail and (
                "quota exceeded" in error_detail.lower()
                or "rate limit" in error_detail.lower()
                or "429" in error_detail
            ):
                raise HTTPException(status_code=429, detail=detail)
            raise HTTPException(status_code=500, detail=detail)
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/list-docs", response_model=list[DocumentInfo])
def list_documents():
    return get_all_documents()

@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest):
    chroma_delete_success = delete_doc_from_chroma(request.file_id)
    if chroma_delete_success:
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {"message": f"Successfully deleted document with file_id {request.file_id} from the system."}
        else:
            return {"error": f"Deleted from Chroma but failed to delete document with file_id {request.file_id} from the database."}
    else:
        return {"error": f"Failed to delete document with file_id {request.file_id} from Chroma."}


# ── Analytics Endpoints ──────────────────────────────────────────────

@app.get("/analytics")
def analytics():
    """Return usage statistics for the analytics dashboard."""
    try:
        data = get_analytics_data()
        return data
    except Exception as e:
        logging.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Chat Export Endpoint ─────────────────────────────────────────────

@app.get("/export-chat/{session_id}")
def export_chat(session_id: str):
    """Return full chat history for a session (for export)."""
    try:
        history = get_chat_history_for_export(session_id)
        return {"session_id": session_id, "messages": history}
    except Exception as e:
        logging.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Health Check ─────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}
