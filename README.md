# LangChain-RAG-Chatbot

A modern Retrieval-Augmented Generation (RAG) chatbot powered by LangChain, FastAPI, and Streamlit. Upload documents, chat with your data, and get AI-powered answers—all in a user-friendly web app.

**Live Preview:**  
👉 [https://langchain-rag-chatbot-frontend.onrender.com/](https://langchain-rag-chatbot-frontend.onrender.com/)

---

## 🚀 Features

- **Document Upload:** Upload PDF, Word, or HTML documents.
- **AI-Powered Chat:** Chat with your documents using Google’s Generative AI and LangChain.
- **Semantic Search:** Fast vector search powered by Chroma and Google embeddings.
- **Responsive UI:** Simple, intuitive Streamlit web interface.
- **Cloud-Ready:** Easy deployment to Render, AWS, or other platforms.

---

## 🏗️ Architecture Overview

- **Backend:** FastAPI (Python) for RESTful API, document processing, and chat logic.
- **Frontend:** Streamlit (Python) for the web UI.
- **Vector Database:** Chroma for local vector storage and semantic search.
- **LLM:** Google Generative AI for generating answers.
- **Deployment:** Docker and Render for containerized and cloud deployment.

---

## 🛠️ How to Run Locally

### Prerequisites

- **Python 3.11 (recommended)**
- **Docker** (optional, for containerized setup)
- **Google API Key** (for Google Generative AI)

---

### 1. Clone the Repository


```bash
git clone https://github.com/mukeshmaurya23/RAG-Powered-Knowledge-Assistant
cd RAG-Powered-Knowledge-Assistant
```


---

### 2. Set Up Environment Variables

Create a `.env` file in the root directory:

GOOGLE_API_KEY=your_api_key_here

---

### 3. Bootstrap (Recommended)

```bash
chmod +x scripts/bootstrap.sh
./scripts/bootstrap.sh
```

This creates `.venv` with Python 3.11 and installs backend + frontend dependencies.
The repository includes `.python-version` pinned to `3.11` for pyenv users.


---

### 4. Install Dependencies (Manual)

#### For the Backend

```bash
cd api
pip install -r requirements.txt
```

#### For the Frontend

```bash
cd app
pip install -r requirements.txt
```


---

### 5. Run the Backend

```bash
cd api
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 6. Run the Frontend

```bash
cd app
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
```

## 🔒 Privacy Note

By default, all users share the same document and chat storage. For production or private use, add user authentication and filter data by user or session.

---

## Project Structure

```bash
langchain-rag-chatbot/
├── api/
│   ├── main.py                # FastAPI backend
│   ├── requirements.txt       # Backend dependencies
│   ├── chroma_db/             # Vector database (ignored in git)
│   ├── rag_app.db             # SQLite database (ignored in git)
│   └── ...                    # Other backend files
├── app/
│   ├── streamlit_app.py       # Streamlit frontend
│   ├── requirements.txt       # Frontend dependencies
│   └── ...                    # Other frontend files
├── docker-compose.yml         # Docker Compose config
├── Dockerfile                 # (Optional) Frontend Dockerfile
├── .env                       # Environment variables (ignored in git)
└── README.md                  # This file
```
---

## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first.

