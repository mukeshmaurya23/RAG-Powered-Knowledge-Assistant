import requests
import streamlit as st
import os


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def check_backend_health() -> bool:
    """Check if the FastAPI backend is reachable."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def _api_url(path: str) -> str:
    return f"{API_BASE_URL}{path}"

def get_api_response(question, session_id, model, file_id=None, language="English"):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {
        "question": question,
        "model": model,
        "language": language,
    }
    if session_id:
        data["session_id"] = session_id
    if file_id is not None:
        data["file_id"] = file_id

    try:
        response = requests.post(_api_url("/chat"), headers=headers, json=data, timeout=120)
        if response.status_code == 200:
            return response.json()
        else:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            st.error(f"API error ({response.status_code}): {detail}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to backend at {API_BASE_URL}. Is the FastAPI server running?")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. Try a simpler question or check the backend.")
        return None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

def upload_document(file):
    print("Uploading file...")
    try:
        # Reset file pointer to start — critical fix!
        # After Streamlit reads the file internally, the pointer may be at the end,
        # causing an empty file to be sent to the backend.
        file.seek(0)

        # Read file content into memory to avoid stream issues
        file_bytes = file.read()
        if not file_bytes:
            error_text = "File appears to be empty. Please re-select the file and try again."
            st.error(error_text)
            return {"_error": error_text}

        mime_type = file.type or "application/octet-stream"
        files = {"file": (file.name, file_bytes, mime_type)}
        response = requests.post(_api_url("/upload-doc"), files=files, timeout=120)
        if response.status_code == 200:
            return response.json()
        else:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            error_text = f"Upload failed ({response.status_code}): {detail}"
            st.error(error_text)
            return {"_error": error_text}
    except requests.exceptions.ConnectionError:
        error_text = f"Cannot connect to backend at {API_BASE_URL}. Is the FastAPI server running?"
        st.error(error_text)
        return {"_error": error_text}
    except requests.exceptions.Timeout:
        error_text = "Upload timed out. The file may be too large or the backend is slow."
        st.error(error_text)
        return {"_error": error_text}
    except Exception as e:
        error_text = f"An error occurred while uploading the file: {str(e)}"
        st.error(error_text)
        return {"_error": error_text}

def list_documents():
    try:
        response = requests.get(_api_url("/list-docs"))
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch document list. Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching the document list: {str(e)}")
        return []

def delete_document(file_id):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {"file_id": file_id}

    try:
        response = requests.post(_api_url("/delete-doc"), headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to delete document. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while deleting the document: {str(e)}")
        return None