import sqlite3
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "rag_app.db")

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_application_logs():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS application_logs
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     session_id TEXT,
                     user_query TEXT,
                     gpt_response TEXT,
                     model TEXT,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()

def insert_application_logs(session_id, user_query, gpt_response, model):
    conn = get_db_connection()
    conn.execute('INSERT INTO application_logs (session_id, user_query, gpt_response, model) VALUES (?, ?, ?, ?)',
                 (session_id, user_query, gpt_response, model))
    conn.commit()
    conn.close()

def get_chat_history(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_query, gpt_response FROM application_logs WHERE session_id = ? ORDER BY created_at', (session_id,))
    messages = []
    for row in cursor.fetchall():
        messages.extend([
            {"role": "human", "content": row['user_query']},
            {"role": "ai", "content": row['gpt_response']}
        ])
    conn.close()
    return messages

def create_document_store():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS document_store
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     filename TEXT,
                     upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()

def insert_document_record(filename):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO document_store (filename) VALUES (?)', (filename,))
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return file_id

def delete_document_record(file_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM document_store WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()
    return True

def get_all_documents():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, filename, upload_timestamp FROM document_store ORDER BY upload_timestamp DESC')
    documents = cursor.fetchall()
    conn.close()
    return [dict(doc) for doc in documents]

def get_analytics_data():
    """Gather usage statistics for the analytics dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total queries
    cursor.execute('SELECT COUNT(*) as count FROM application_logs')
    total_queries = cursor.fetchone()['count']

    # Total documents
    cursor.execute('SELECT COUNT(*) as count FROM document_store')
    total_documents = cursor.fetchone()['count']

    # Unique sessions
    cursor.execute('SELECT COUNT(DISTINCT session_id) as count FROM application_logs')
    total_sessions = cursor.fetchone()['count']

    # Queries per day (last 30 days)
    cursor.execute('''
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM application_logs
        WHERE created_at >= DATE('now', '-30 days')
        GROUP BY DATE(created_at)
        ORDER BY date
    ''')
    queries_per_day = [dict(row) for row in cursor.fetchall()]

    # Model usage distribution
    cursor.execute('''
        SELECT model, COUNT(*) as count
        FROM application_logs
        GROUP BY model
    ''')
    model_usage = [dict(row) for row in cursor.fetchall()]

    # Recent uploads
    cursor.execute('''
        SELECT filename, upload_timestamp
        FROM document_store
        ORDER BY upload_timestamp DESC
        LIMIT 10
    ''')
    recent_uploads = [dict(row) for row in cursor.fetchall()]

    # Average queries per session
    cursor.execute('''
        SELECT AVG(query_count) as avg_queries FROM (
            SELECT session_id, COUNT(*) as query_count
            FROM application_logs
            GROUP BY session_id
        )
    ''')
    avg_queries_per_session = cursor.fetchone()['avg_queries'] or 0

    # Queries per hour (activity heatmap)
    cursor.execute('''
        SELECT CAST(strftime('%H', created_at) AS INTEGER) as hour, COUNT(*) as count
        FROM application_logs
        GROUP BY hour
        ORDER BY hour
    ''')
    queries_per_hour = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "total_queries": total_queries,
        "total_documents": total_documents,
        "total_sessions": total_sessions,
        "avg_queries_per_session": round(avg_queries_per_session, 1),
        "queries_per_day": queries_per_day,
        "model_usage": model_usage,
        "recent_uploads": recent_uploads,
        "queries_per_hour": queries_per_hour,
    }


def get_chat_history_for_export(session_id):
    """Get full chat history with timestamps for export."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_query, gpt_response, model, created_at
        FROM application_logs
        WHERE session_id = ?
        ORDER BY created_at
    ''', (session_id,))
    messages = []
    for row in cursor.fetchall():
        messages.append({
            "user_query": row['user_query'],
            "ai_response": row['gpt_response'],
            "model": row['model'],
            "timestamp": row['created_at'],
        })
    conn.close()
    return messages


# Initialize the database tables
create_application_logs()
create_document_store()
