import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from api_utils import get_api_response


# ── Voice Input (rendered via st.components.v1.html) ────────────────

VOICE_INPUT_HTML = """
<div id="voice-container" style="display:inline-flex;align-items:center;gap:8px;font-family:sans-serif;">
    <button id="voice-btn" onclick="toggleVoice()" style="
        background:#334155; border:1px solid #475569; border-radius:6px; color:#e2e8f0;
        padding:6px 14px; cursor:pointer; font-size:13px;
        display:inline-flex; align-items:center; gap:6px;
    ">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="23"/>
            <line x1="8" y1="23" x2="16" y2="23"/>
        </svg>
        <span id="voice-text">Voice Input</span>
    </button>
    <span id="voice-status" style="font-size:12px;color:#94a3b8;"></span>
</div>
<script>
let recognition=null, isListening=false;
function toggleVoice(){
    if(!('webkitSpeechRecognition' in window)&&!('SpeechRecognition' in window)){
        document.getElementById('voice-status').textContent='Not supported in this browser';return;
    }
    if(isListening){recognition.stop();return;}
    const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
    recognition=new SR();
    recognition.continuous=false;recognition.interimResults=true;recognition.lang='en-US';
    recognition.onstart=()=>{
        isListening=true;
        document.getElementById('voice-btn').style.background='#dc2626';
        document.getElementById('voice-btn').style.borderColor='#dc2626';
        document.getElementById('voice-text').textContent='Listening...';
        document.getElementById('voice-status').textContent='Speak now...';
    };
    recognition.onresult=(e)=>{
        let t='';for(let i=0;i<e.results.length;i++)t+=e.results[i][0].transcript;
        document.getElementById('voice-status').textContent=t;
        if(e.results[0].isFinal){
            navigator.clipboard.writeText(t).then(()=>{
                document.getElementById('voice-status').textContent='"'+t+'" copied. Paste in chat box (Ctrl+V).';
            });
        }
    };
    recognition.onend=()=>{
        isListening=false;
        document.getElementById('voice-btn').style.background='#334155';
        document.getElementById('voice-btn').style.borderColor='#475569';
        document.getElementById('voice-text').textContent='Voice Input';
    };
    recognition.onerror=(e)=>{
        document.getElementById('voice-status').textContent='Error: '+e.error;
        isListening=false;
    };
    recognition.start();
}
</script>
"""


# ── Text-to-Speech (rendered via components.html to avoid raw HTML leak) ──

def render_tts_button(text, key_suffix=""):
    """Render a TTS play button using st.components.v1.html so JS actually executes."""
    safe = text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    safe = safe.replace("</script>", "<\\/script>")
    safe = safe.replace("\n", " ").replace("\r", "")
    if len(safe) > 3000:
        safe = safe[:3000]

    html = f"""
    <div style="margin:4px 0;">
        <button id="tts-btn-{key_suffix}" data-playing="false" style="
            background:transparent; border:1px solid #475569; border-radius:4px;
            padding:4px 12px; cursor:pointer; font-size:12px; color:#94a3b8;
            font-family:sans-serif;
        ">Play Response</button>
    </div>
    <script>
    document.getElementById('tts-btn-{key_suffix}').addEventListener('click', function() {{
        if('speechSynthesis' in window) {{
            const btn = this;
            if(btn.dataset.playing === 'true') {{
                window.speechSynthesis.cancel();
                btn.dataset.playing = 'false';
                btn.textContent = 'Play Response';
                return;
            }}
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(`{safe}`);
            u.rate = 0.95; u.pitch = 1;
            u.onend = () => {{ btn.dataset.playing = 'false'; btn.textContent = 'Play Response'; }};
            btn.dataset.playing = 'true';
            btn.textContent = 'Stop';
            window.speechSynthesis.speak(u);
        }}
    }});
    </script>
    """
    components.html(html, height=45)


# ── Confidence Display ──────────────────────────────────────────────

def render_confidence(confidence: str, source_count: int):
    css_class = f"conf-{confidence}" if confidence in ("high", "medium", "low") else "conf-none"
    st.markdown(
        f'<span class="conf-badge {css_class}">{confidence.upper()}</span>'
        f'&nbsp;&nbsp;<span style="color:#94a3b8;font-size:0.8rem;">Sources: {source_count}</span>',
        unsafe_allow_html=True,
    )


# ── Source Rendering ────────────────────────────────────────────────

def render_sources(sources):
    if not sources:
        return
    with st.expander(f"View {len(sources)} retrieved sources"):
        for idx, src in enumerate(sources, start=1):
            name = src.get("source") or "Unknown"
            if "/tmp/" in str(name):
                name = "Uploaded Document"
            page = src.get("page")
            file_id = src.get("file_id")

            parts = [f"**{idx}.** {name}"]
            if page is not None:
                parts.append(f"Page {page}")
            if file_id is not None:
                parts.append(f"Doc #{file_id}")
            st.markdown(" | ".join(parts))

            snippet = src.get("snippet", "")
            if snippet:
                display = snippet[:200] + "..." if len(snippet) > 200 else snippet
                st.markdown(
                    f'<div class="source-item">{display}</div>',
                    unsafe_allow_html=True,
                )


# ── Chat Export ─────────────────────────────────────────────────────

def export_chat_text(messages):
    lines = [
        "=" * 60,
        "RAG CHATBOT - CONVERSATION EXPORT",
        f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60, "",
    ]
    for msg in messages:
        role = "You" if msg["role"] == "user" else "AI"
        lines.append(f"[{role}]")
        lines.append(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            lines.append(f"  (Sources: {msg.get('source_count', 0)} | Confidence: {msg.get('confidence', '-')})")
        lines.append("")
    return "\n".join(lines)


def export_chat_md(messages):
    lines = [
        "# RAG Chatbot - Conversation Export",
        f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "---", "",
    ]
    for msg in messages:
        if msg["role"] == "user":
            lines.append("### You")
        else:
            lines.append("### AI")
        lines.append(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            lines.append(f"\n> Confidence: {msg.get('confidence', '-').upper()} | Sources: {msg.get('source_count', 0)}")
        lines.append("")
    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────

def display_chat_interface():
    # Header row
    header_cols = st.columns([6, 1.5, 1.5])
    with header_cols[0]:
        st.markdown("### Chat with your Documents")
    with header_cols[1]:
        if st.session_state.messages:
            st.download_button(
                "Export .md",
                data=export_chat_md(st.session_state.messages),
                file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True,
            )
    with header_cols[2]:
        if st.session_state.messages:
            st.download_button(
                "Export .txt",
                data=export_chat_text(st.session_state.messages),
                file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

    # Voice input
    components.html(VOICE_INPUT_HTML, height=40)

    # Language indicator
    lang = st.session_state.get("language", "English")
    if lang != "English":
        st.caption(f"Response language: {lang}")

    # -- Render existing messages --
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                render_confidence(
                    message.get("confidence", "low"),
                    message.get("source_count", 0),
                )
            st.markdown(message["content"])
            if message["role"] == "assistant":
                render_tts_button(message["content"], key_suffix=str(id(message)))
                render_sources(message.get("sources", []))

    # -- Chat input --
    if prompt := st.chat_input("Ask a question about your documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                response = get_api_response(
                    prompt,
                    st.session_state.session_id,
                    st.session_state.model,
                    st.session_state.get("active_file_id"),
                    st.session_state.get("language", "English"),
                )

            if response:
                st.session_state.session_id = response.get("session_id")
                answer = response["answer"]
                sources = response.get("sources", [])
                source_count = response.get("source_count", 0)
                confidence = response.get("confidence", "low")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "source_count": source_count,
                    "confidence": confidence,
                })

                render_confidence(confidence, source_count)
                st.markdown(answer)
                render_tts_button(answer, key_suffix="latest")
                render_sources(sources)
            else:
                st.error("Failed to get a response. Check if the backend is running.")
