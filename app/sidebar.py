import streamlit as st
from api_utils import upload_document, list_documents, delete_document, check_backend_health


SUPPORTED_LANGUAGES = [
    "English", "Hindi", "Marathi", "Tamil", "Telugu", "Bengali", "Gujarati", "Kannada"
]

FILE_TYPE_LABELS = {
    "PDF": "PDF", "DOCX": "Word", "HTML": "HTML",
    "TXT": "Text", "CSV": "CSV", "PPTX": "PowerPoint"
}


def display_sidebar():
    st.sidebar.markdown("<h2 style='margin-top: -4.5rem;'>Nexus</h2>", unsafe_allow_html=True)
    st.sidebar.caption("<p style='color: #9ca3af; margin-top: -3rem;'>Intelligent Document Analysis Engine</p>", unsafe_allow_html=True)
    st.sidebar.divider()

    # -- Backend Status --
    if st.session_state.backend_ok is None:
        st.session_state.backend_ok = check_backend_health()

    if st.session_state.backend_ok:
        st.sidebar.success("Backend: Connected")
    else:
        st.sidebar.error("Backend: Not reachable")
        st.sidebar.caption("Make sure FastAPI is running on port 8000")
        if st.sidebar.button("Retry Connection"):
            st.session_state.backend_ok = check_backend_health()
            st.rerun()
        return

    # -- Settings --
    with st.sidebar.expander("Settings", expanded=False):
        model_options = ["gemini-flash-latest"]
        st.selectbox("Model", options=model_options, key="model")
        st.selectbox(
            "Response Language",
            options=SUPPORTED_LANGUAGES,
            key="language",
            help="AI will respond in the selected language",
        )

    st.sidebar.divider()

    # -- Upload Document --
    st.sidebar.markdown("### Upload Document")
    uploaded_file = st.sidebar.file_uploader(
        "Choose a file",
        type=["pdf", "docx", "html", "txt", "csv", "pptx"],
        help="Supported: PDF, DOCX, HTML, TXT, CSV, PPTX",
    )

    if uploaded_file is not None:
        size_kb = uploaded_file.size / 1024
        size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb / 1024:.1f} MB"
        file_ext = uploaded_file.name.rsplit(".", 1)[-1].upper() if "." in uploaded_file.name else ""
        label = FILE_TYPE_LABELS.get(file_ext, file_ext)
        st.sidebar.caption(f"{uploaded_file.name}  |  {size_str}  |  {label}")

        if st.sidebar.button("Upload & Index", use_container_width=True):
            with st.spinner("Uploading and indexing..."):
                upload_response = upload_document(uploaded_file)
                if upload_response and not upload_response.get("_error"):
                    st.sidebar.success(f"Indexed successfully (ID: {upload_response['file_id']})")
                    st.session_state.documents = list_documents()
                    st.rerun()
                else:
                    msg = (upload_response or {}).get("_error", "Upload failed.")
                    st.sidebar.error(msg)

    st.sidebar.divider()

    # -- Document Library --
    st.sidebar.markdown("## Document Library")

    if st.sidebar.button("Refresh List", help="Refresh document list", use_container_width=True):
        st.session_state.documents = list_documents()
        st.rerun()

    if not st.session_state.documents:
        st.session_state.documents = list_documents()

    documents = st.session_state.documents

    if documents:
        # Chat scope
        scope_options = [None] + [doc["id"] for doc in documents]
        selected_scope = st.sidebar.selectbox(
            "Chat Scope",
            options=scope_options,
            format_func=lambda x: "All documents" if x is None else next(
                (doc["filename"] for doc in documents if doc["id"] == x), "Unknown"
            ),
            key="chat_scope_file_id",
            help="Restrict AI answers to a specific document",
        )
        st.session_state.active_file_id = selected_scope

        # Document list
        for doc in documents:
            ext = doc["filename"].rsplit(".", 1)[-1].upper() if "." in doc["filename"] else ""
            label = FILE_TYPE_LABELS.get(ext, ext)
            st.sidebar.caption(f"{doc['filename']}  (ID: {doc['id']})  [{label}]")

        # Delete
        with st.sidebar.expander("Delete Document"):
            selected_file_id = st.selectbox(
                "Select document",
                options=[doc["id"] for doc in documents],
                format_func=lambda x: next(
                    (doc["filename"] for doc in documents if doc["id"] == x), "Unknown"
                ),
            )
            if st.button("Delete", type="secondary", use_container_width=True):
                with st.spinner("Deleting..."):
                    resp = delete_document(selected_file_id)
                    if resp:
                        st.success("Deleted.")
                        st.session_state.documents = list_documents()
                        st.rerun()
                    else:
                        st.error("Failed to delete.")
    else:
        st.sidebar.info("No documents uploaded yet.")

    st.sidebar.divider()

    if st.sidebar.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()
