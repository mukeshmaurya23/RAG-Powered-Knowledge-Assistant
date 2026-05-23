import streamlit as st
import requests
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def fetch_analytics():
    try:
        response = requests.get(f"{API_BASE_URL}/analytics", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def display_analytics():
    st.markdown("### Usage Analytics")
    st.caption("Real-time insights into your RAG Chatbot usage")

    if st.button("Refresh Analytics"):
        st.rerun()

    data = fetch_analytics()
    if not data:
        st.warning("Could not fetch analytics. Make sure the backend is running.")
        return

    # -- KPI Row --
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Queries", data.get("total_queries", 0))
    with col2:
        st.metric("Documents", data.get("total_documents", 0))
    with col3:
        st.metric("Sessions", data.get("total_sessions", 0))
    with col4:
        st.metric("Avg Queries / Session", data.get("avg_queries_per_session", 0))

    st.divider()

    # -- Charts --
    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown("#### Queries Over Time")
        queries_per_day = data.get("queries_per_day", [])
        if queries_per_day:
            import pandas as pd
            df = pd.DataFrame(queries_per_day)
            df["date"] = pd.to_datetime(df["date"])
            st.area_chart(df.set_index("date")["count"], color="#667eea")
        else:
            st.info("No query data yet. Start chatting to see trends.")

    with right_col:
        st.markdown("#### Activity by Hour")
        queries_per_hour = data.get("queries_per_hour", [])
        if queries_per_hour:
            import pandas as pd
            df = pd.DataFrame(queries_per_hour)
            all_hours = pd.DataFrame({"hour": range(24)})
            df = all_hours.merge(df, on="hour", how="left").fillna(0)
            df["count"] = df["count"].astype(int)
            df["hour_label"] = df["hour"].apply(lambda h: f"{h:02d}:00")
            st.bar_chart(df.set_index("hour_label")["count"], color="#764ba2")
        else:
            st.info("No activity data yet.")

    st.divider()

    left_col2, right_col2 = st.columns(2)

    with left_col2:
        st.markdown("#### Model Usage")
        model_usage = data.get("model_usage", [])
        if model_usage:
            for item in model_usage:
                name = item.get("model", "Unknown")
                count = item.get("count", 0)
                total = max(data.get("total_queries", 1), 1)
                st.markdown(f"**{name}**: {count} queries")
                st.progress(min(count / total, 1.0))
        else:
            st.info("No model usage data yet.")

    with right_col2:
        st.markdown("#### Recent Uploads")
        recent_uploads = data.get("recent_uploads", [])
        if recent_uploads:
            for upload in recent_uploads:
                ext = upload["filename"].rsplit(".", 1)[-1].upper() if "." in upload["filename"] else ""
                ts = upload.get("upload_timestamp", "")
                if ts:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(str(ts))
                        ts = dt.strftime("%b %d, %H:%M")
                    except Exception:
                        pass
                st.caption(f"{upload['filename']}  |  {ext}  |  {ts}")
        else:
            st.info("No documents uploaded yet.")
