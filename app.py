"""
Streamlit Application for the AI-Powered Student Query Assistant.

Provides a redesigned, premium Student Workstation Dashboard:
- Cyberpunk dark palette with glowing neon accents
- Dual-column layout: Left Chat Column, Right Information & Action Panel
- Interactive click-to-run prompt suggestions
- Floating tab selectors for focus tracks
- Downloader, Cacher, and Session Logger integrations
"""

import os
import json
import hashlib
import streamlit as st
from streamlit_mic_recorder import mic_recorder
from dotenv import load_dotenv

# Load modular components
from modules.logger import logger
import modules.auth as auth
import modules.chatbot as chatbot
import modules.cache as cache
import modules.voice as voice
import modules.utils as utils

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 1. Page Configuration & Custom Styling
st.set_page_config(
    page_title="Student Workstation Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Cyberpunk Neon Stylesheet
st.markdown(
    """
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', sans-serif;
        background-color: #06070a !important;
        color: #e2e8f0 !important;
    }
    
    .stApp {
        background-image: radial-gradient(circle at 5% 5%, rgba(139, 92, 246, 0.12) 0%, transparent 50%),
                          radial-gradient(circle at 95% 95%, rgba(6, 182, 212, 0.1) 0%, transparent 50%);
        background-attachment: fixed;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Custom Headers */
    .dashboard-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #a855f7 0%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .dashboard-subtitle {
        font-size: 1rem;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }

    /* Container Styling (styled as glass-cards) */
    div[data-testid="stContainer"] {
        background: rgba(15, 23, 42, 0.4) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5) !important;
        margin-bottom: 1.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="stContainer"]:hover {
        border-color: rgba(168, 85, 247, 0.25) !important;
        box-shadow: 0 10px 30px -5px rgba(168, 85, 247, 0.08) !important;
    }
    
    /* Premium Buttons */
    div.stButton > button {
        background: rgba(30, 41, 59, 0.5) !important;
        color: #cbd5e1 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 8px 18px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100%;
        text-align: left;
    }
    
    div.stButton > button:hover {
        background: linear-gradient(135deg, #7c3aed 0%, #0891b2 100%) !important;
        border-color: rgba(6, 182, 212, 0.4) !important;
        color: #ffffff !important;
        box-shadow: 0 0 15px rgba(6, 182, 212, 0.3) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Tab Buttons - Active styling helper classes */
    .active-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: #06b6d4;
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 8px #06b6d4;
    }
    
    /* Custom CSS for User & Assistant chat alignment */
    .user-bubble {
        background: rgba(99, 102, 241, 0.12) !important;
        border-left: 4px solid #6366f1 !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin-bottom: 1rem !important;
    }
    
    .bot-bubble {
        background: rgba(6, 182, 212, 0.08) !important;
        border-left: 4px solid #06b6d4 !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin-bottom: 1rem !important;
    }
    
    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.1);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(168, 85, 247, 0.3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(168, 85, 247, 0.5);
    }
    
    /* Audio Container wrapper */
    .audio-wrapper {
        background: rgba(15, 23, 42, 0.3);
        border: 1px dashed rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 1rem;
    }
    
    /* Static custom cards */
    .custom-card {
        background: rgba(15, 23, 42, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 1.2rem;
    }
    
    /* Sidebar custom styling */
    section[data-testid="stSidebar"] {
        background-color: #090a0f !important;
        border-right: 1px solid rgba(255, 255, 255, 0.03) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 2. Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "active_track" not in st.session_state:
    st.session_state.active_track = "Programming"

# Initialize conversation history dict per track
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {
        "Programming": [],
        "AI/ML": [],
        "Career Guidance": [],
        "Interview Preparation": []
    }

# Session settings & preferences
if "bypass_cache" not in st.session_state:
    st.session_state.bypass_cache = False
if "api_key_override" not in st.session_state:
    st.session_state.api_key_override = ""
if "openai_key_override" not in st.session_state:
    st.session_state.openai_key_override = ""
if "model_selection" not in st.session_state:
    st.session_state.model_selection = chatbot.DEFAULT_GEMINI_MODEL
if "temperature" not in st.session_state:
    st.session_state.temperature = chatbot.DEFAULT_TEMPERATURE
if "clicked_suggestion" not in st.session_state:
    st.session_state.clicked_suggestion = None

# Track Metadata Definitions
TRACK_METADATA = {
    "Programming": {
        "icon": "💻",
        "color": "#00f0ff",
        "description": "Master clean coding, data structures, algorithm syntax, and PEP 8 guidelines. Resolve complex bugs and write structured code.",
        "milestones": [
            "Write readable, PEP 8 compliant code",
            "Understand Python decorators & generators",
            "Optimize loops & memory complexity",
            "Build robust multi-threaded applications"
        ],
        "prompts": [
            "Explain Python decorators.",
            "What is a list comprehension?",
            "Difference between a list and a tuple in Python?"
        ]
    },
    "AI/ML": {
        "icon": "🧠",
        "color": "#bd00ff",
        "description": "Explore machine learning paradigms, statistical foundations, regression models, neural networks, PyTorch, and NLP architectures.",
        "milestones": [
            "Build regression and classification models",
            "Formulate mathematical optimization equations",
            "Develop neural network graphs in PyTorch",
            "Train transformers & attention models"
        ],
        "prompts": [
            "How do I learn Machine Learning?",
            "Explain supervised vs unsupervised learning.",
            "How does the Attention mechanism work?"
        ]
    },
    "Career Guidance": {
        "icon": "🚀",
        "color": "#00ff87",
        "description": "Chart your path into Software Engineering, Data Science, DevOps, or Product Management. Plan projects, portfolio reviews, and internships.",
        "milestones": [
            "Select specialized career pathways",
            "Draft high-impact capstone project outlines",
            "Design developer portfolio websites",
            "Find and apply for tech internships"
        ],
        "prompts": [
            "How should I prepare for placements?",
            "What projects should I build for a Web Developer portfolio?",
            "How do I structure my resume for an AI intern?"
        ]
    },
    "Interview Preparation": {
        "icon": "🎯",
        "color": "#ff9f00",
        "description": "Prepare for technical interviews: Data Structures & Algorithms, Big-O analysis, system designs, and behavioral STAR interviews.",
        "milestones": [
            "Resolve core LeetCode DSA questions",
            "Understand Big-O time & space complexities",
            "Formulate STAR behavioral answers",
            "Design scalable system architectures"
        ],
        "prompts": [
            "Explain Big O notation.",
            "What is the STAR method?",
            "Give me a mock DSA question."
        ]
    }
}


# --- AUTHENTICATION SCREEN ---
if not st.session_state.authenticated:
    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
    
    # Outer Columns for centering
    col_l, col_c, col_r = st.columns([1, 1.8, 1])
    with col_c:
        st.markdown(
            """
            <div style='text-align: center; margin-bottom: 1.5rem;'>
                <span style='font-size: 3.5rem; text-shadow: 0 0 20px rgba(168, 85, 247, 0.4);'>🎓</span>
                <h1 class='dashboard-title' style='font-size: 2.4rem;'>Student Workstation</h1>
                <p style='color: #94a3b8; font-size: 0.95rem; margin-top: 0.3rem;'>
                    Secure Portal for AI-Guided Academic & Career Support.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        with st.container(border=True):
            tab_login, tab_signup = st.tabs(["🔐 Sign In", "📝 Create Account"])
            
            with tab_login:
                st.markdown("<h4 style='margin-bottom: 1rem;'>Enter Credentials</h4>", unsafe_allow_html=True)
                login_user = st.text_input("Username", key="login_username", placeholder="e.g., student123")
                login_pass = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")
                
                st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
                if st.button("Sign In", use_container_width=True, key="signin_btn"):
                    if not login_user or not login_pass:
                        st.warning("Please fill in all credentials.")
                    else:
                        if auth.verify_user(login_user, login_pass):
                            st.session_state.authenticated = True
                            st.session_state.username = login_user.lower().strip()
                            st.success("Successfully logged in!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")
                            
            with tab_signup:
                st.markdown("<h4 style='margin-bottom: 1rem;'>Create Profile</h4>", unsafe_allow_html=True)
                reg_user = st.text_input("Choose Username", key="reg_username", placeholder="e.g., student123")
                reg_pass = st.text_input("Choose Password", type="password", key="reg_password", placeholder="Min 6 characters")
                reg_pass_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm", placeholder="••••••••")
                
                st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
                if st.button("Create Account", use_container_width=True, key="signup_btn"):
                    reg_user_clean = reg_user.strip()
                    if not reg_user_clean or not reg_pass:
                        st.warning("All fields are required.")
                    elif len(reg_pass) < 6:
                        st.warning("Password should be at least 6 characters long.")
                    elif reg_pass != reg_pass_confirm:
                        st.error("Passwords do not match.")
                    else:
                        if auth.register_user(reg_user_clean, reg_pass):
                            st.success("Profile created! You can now sign in.")
                        else:
                            st.error("Username is already taken.")
    st.stop()


# --- AUTHENTICATED PANEL ---

# SIDEBAR: Configurations, storage, API settings
with st.sidebar:
    st.markdown(
        """
        <div class='logo-container'>
            <span style='font-size: 2.2rem;'>🎓</span>
            <div class='logo-text'>STUDENT WORKSTATION</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(f"**Active Session:** `@{st.session_state.username}`")
    st.divider()
    
    st.markdown("### 🔑 API Access Tokens")
    # Gemini configurations
    has_gemini = bool(GEMINI_API_KEY)
    if has_gemini:
        st.success("✅ Gemini Key Configured (.env)")
        api_key_override = st.text_input(
            "Override Gemini Key",
            type="password",
            value=st.session_state.api_key_override,
            help="Enter a key here to override the .env configuration."
        )
    else:
        st.warning("⚠️ Gemini Key Missing")
        api_key_override = st.text_input(
            "Enter Gemini API Key",
            type="password",
            value=st.session_state.api_key_override,
            help="Enter your Gemini API key to activate the assistant."
        )
    if api_key_override != st.session_state.api_key_override:
        st.session_state.api_key_override = api_key_override

    # OpenAI configurations
    has_openai = bool(OPENAI_API_KEY)
    if has_openai:
        st.success("✅ OpenAI Key Configured (.env)")
        openai_key_override = st.text_input(
            "Override OpenAI Key",
            type="password",
            value=st.session_state.openai_key_override,
            help="Enter an OpenAI key to override the .env configuration."
        )
    else:
        st.info("ℹ️ OpenAI Key Missing (Optional)")
        openai_key_override = st.text_input(
            "Enter OpenAI API Key",
            type="password",
            value=st.session_state.openai_key_override,
            help="Enter an OpenAI API key to enable fallback model checks."
        )
    if openai_key_override != st.session_state.openai_key_override:
        st.session_state.openai_key_override = openai_key_override

    st.divider()
    
    # Model configuration parameters
    st.markdown("### 🎛️ Model Hyperparameters")
    st.session_state.model_selection = "gemini-2.5-flash"
    st.info("⚡ Enforced: **gemini-2.5-flash**")
    
    temp = st.slider("Temperature (Creativity)", 0.0, 1.0, float(st.session_state.temperature), step=0.1)
    st.session_state.temperature = temp

    st.divider()
    
    # Logout action
    st.markdown("<div class='logout-btn'>", unsafe_allow_html=True)
    if st.button("🚪 Close Session", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.chat_histories = {
            "Programming": [],
            "AI/ML": [],
            "Career Guidance": [],
            "Interview Preparation": []
        }
        st.success("Session closed successfully.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# --- DASHBOARD HEADER ---
st.markdown("<h1 class='dashboard-title'>🎓 Student Assistant Workstation</h1>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-subtitle'>A dual-column glassmorphic workstation dashboard representing code tutoring, AI/ML paradigms, career paths, and interview preps.</div>", unsafe_allow_html=True)

# Interactive Tab Selector (glowing columns instead of standard radio buttons)
st.markdown("### 🛡️ Selected Workstation Profile")
tab_cols = st.columns(4)
tracks = ["Programming", "AI/ML", "Career Guidance", "Interview Preparation"]
for idx, track_name in enumerate(tracks):
    with tab_cols[idx]:
        meta = TRACK_METADATA[track_name]
        is_active = (st.session_state.active_track == track_name)
        label_btn = f"{meta['icon']} {track_name}"
        if is_active:
            label_btn = f"⚡ {meta['icon']} {track_name}"
            
        # Draw active indicator above button
        if is_active:
            st.markdown(f"<div style='border-top: 3px solid {meta['color']}; margin-bottom: -5px;'></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='border-top: 3px solid transparent; margin-bottom: -5px;'></div>", unsafe_allow_html=True)
            
        if st.button(label_btn, key=f"track_tab_{idx}", use_container_width=True):
            st.session_state.active_track = track_name
            st.rerun()

active_track = st.session_state.active_track
track_meta = TRACK_METADATA[active_track]
track_color = track_meta["color"]


# --- DUAL COLUMN WORKSPACE ---
col_chat, col_dash = st.columns([2.2, 1.0], gap="large")

# --- LEFT COLUMN: Chat Workstation ---
with col_chat:
    st.markdown(f"### 💬 Interactive Chat Feed — <span style='color: {track_color};'>{active_track}</span>", unsafe_allow_html=True)
    
    # Container with glass styling for Chat history
    chat_container = st.container(border=True)
    with chat_container:
        chat_history = st.session_state.chat_histories[active_track]
        
        if not chat_history:
            st.markdown(
                f"""
                <div style='text-align: center; padding: 3rem 1rem; color: #94a3b8;'>
                    <span style='font-size: 3rem;'>💬</span>
                    <h4 style='margin-top: 1rem;'>Workspace Feed Empty</h4>
                    <p style='font-size: 0.85rem; margin-top: 0.3rem;'>
                        Select a track suggestion in the right panel or type/speak a query to initiate your learning session.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            for message in chat_history:
                bubble_class = "user-bubble" if message["role"] == "user" else "bot-bubble"
                sender_label = f"🎓 student_@{st.session_state.username}" if message["role"] == "user" else "🤖 assistant_ai"
                st.markdown(
                    f"""
                    <div class="{bubble_class}">
                        <div style='font-size: 0.8rem; font-weight: 700; color: #94a3b8; margin-bottom: 0.4rem;'>{sender_label}</div>
                        <div>{message["content"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
    # --- Resolve API keys for voice & chat ---
    resolved_gemini = st.session_state.api_key_override or GEMINI_API_KEY
    resolved_openai = st.session_state.openai_key_override or OPENAI_API_KEY

    # --- Voice Input: mic_recorder → Gemini STT ---
    voice_container = st.container(border=True)
    with voice_container:
        st.markdown("##### 🎙️ Voice Input")
        audio = mic_recorder(
            start_prompt="🎙️ Start Recording",
            stop_prompt="🛑 Stop Recording",
            key=f"voice_rec_{active_track}"
        )

    # Process recorded audio through Gemini STT
    voice_query_text = None
    if audio and audio.get("bytes"):
        audio_bytes = audio["bytes"]
        audio_hash = hashlib.md5(audio_bytes).hexdigest()

        # Only process new recordings (avoid re-processing on rerun)
        if st.session_state.get("_last_audio_hash") != audio_hash:
            st.session_state["_last_audio_hash"] = audio_hash
            with st.spinner("Transcribing with Gemini 2.5 Flash..."):
                try:
                    transcription = voice.transcribe_audio_bytes(
                        audio_bytes=audio_bytes,
                        mime_type="audio/webm",
                        gemini_key=resolved_gemini,
                        openai_key=resolved_openai
                    )
                    if transcription and transcription.strip():
                        voice_query_text = transcription.strip()
                        st.session_state["_last_voice_text"] = voice_query_text
                    else:
                        st.warning("No speech detected. Please try again.")
                except Exception as e:
                    st.error(f"Transcription error: {e}")
        else:
            # Rerun with same audio — use cached text
            voice_query_text = st.session_state.get("_last_voice_text")

    if voice_query_text:
        st.info(f"🗣️ **Transcribed:** \"{voice_query_text}\"")

    # --- Text Chat Input ---
    user_query = st.chat_input(f"Send a query to the {active_track} assistant...")

    # --- Determine final query (clicked suggestion > voice > text) ---
    final_query = None
    if st.session_state.get("clicked_suggestion"):
        final_query = st.session_state.clicked_suggestion
        st.session_state.clicked_suggestion = None
    elif voice_query_text:
        final_query = voice_query_text
        # Clear so we don't re-send on next rerun
        st.session_state["_last_voice_text"] = None
    elif user_query:
        final_query = user_query

    # --- Execute query → response lifecycle ---
    if final_query:
        final_query = final_query.strip()

        # 1. Validate
        is_valid, err_msg = utils.validate_query(final_query)
        if not is_valid:
            st.error(f"⚠️ {err_msg}")
        else:
            # 2. Append user message
            st.session_state.chat_histories[active_track].append({"role": "user", "content": final_query})

            # 3. Generate response
            with st.spinner("Generating response with Gemini 2.5 Flash..."):
                response_text, is_cached_hit = cache.get_cached_response(
                    query=final_query,
                    track=active_track,
                    chat_history=chat_history,
                    gemini_key=resolved_gemini,
                    openai_key=resolved_openai,
                    model_name=st.session_state.model_selection,
                    temperature=st.session_state.temperature,
                    bypass_cache=st.session_state.bypass_cache
                )

            # 4. Append response
            st.session_state.chat_histories[active_track].append({"role": "assistant", "content": response_text})

            # 5. Persist log
            utils.log_conversation(
                username=st.session_state.username,
                track=active_track,
                query=final_query,
                response=response_text
            )

            st.rerun()


# --- RIGHT COLUMN: Workspace Info & Actions ---
with col_dash:
    st.markdown("### 🛡️ Dashboard Panel")
    
    # 1. Workstation Focus Card
    st.markdown(
        f"""
        <div style='border: 1px solid rgba(255,255,255,0.06); background: rgba(30,41,59,0.35); border-radius: 16px; padding: 18px; margin-bottom: 1.2rem; border-left: 4px solid {track_color};'>
            <h4 style='color: {track_color}; margin-top:0;'>Focus Profile: {active_track}</h4>
            <p style='font-size: 0.85rem; color: #cbd5e1; line-height: 1.4; margin-bottom:0;'>{track_meta['description']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 2. Learning Milestones Card
    milestones_html = "".join(f"<li style='margin-bottom: 6px;'>{m}</li>" for m in track_meta["milestones"])
    st.markdown(
        f"""
        <div style='border: 1px solid rgba(255,255,255,0.06); background: rgba(30,41,59,0.25); border-radius: 16px; padding: 18px; margin-bottom: 1.2rem;'>
            <h4 style='color: #f1f5f9; margin-top:0;'>🎯 Core Learning Milestones</h4>
            <ul style='font-size: 0.82rem; color: #cbd5e1; padding-left: 20px; margin-bottom:0;'>
                {milestones_html}
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 3. Interactive Quick suggestions
    st.markdown("### 💡 Clickable Suggestions")
    with st.container(border=True):
        st.markdown("<p style='font-size: 0.8rem; color: #94a3b8; margin-top:0;'>Click to run prompt immediately:</p>", unsafe_allow_html=True)
        for i, prompt in enumerate(track_meta["prompts"]):
            if st.button(prompt, key=f"sug_prompt_{i}"):
                st.session_state.clicked_suggestion = prompt
                st.rerun()

    # 4. Storage and cache controls
    st.markdown("### 🎛️ Session Controls")
    with st.container(border=True):
        use_cache = st.toggle("Response Cache (lru)", value=not st.session_state.bypass_cache)
        st.session_state.bypass_cache = not use_cache
        
        col_clear_c, col_clear_h = st.columns(2)
        with col_clear_c:
            if st.button("Flush Cache", key="flush_cache_btn"):
                cache.clear_response_cache()
                st.success("Wiped!")
        with col_clear_h:
            if st.button("Wipe Chat", key="wipe_chat_btn"):
                st.session_state.chat_histories[active_track] = []
                st.success("Wiped!")
                st.rerun()
                
        # Download Chat History
        if chat_history:
            chat_json_str = json.dumps(chat_history, indent=2)
            st.download_button(
                label="📥 Export Chat History (JSON)",
                data=chat_json_str,
                file_name=f"chat_history_{active_track.lower().replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True
            )

    # 5. Administrative logs review
    with st.expander("👁️ View Logs History"):
        logs = utils.get_conversation_history(st.session_state.username, limit=5)
        if logs:
            for l in logs:
                st.markdown(f"**[{l['track']}]** *{l['timestamp']}*")
                st.markdown(f"**Q:** {l['user']}")
                st.markdown(f"**A:** {l['assistant'][:50]}...")
                st.divider()
            if st.button("Clear Log History", key="clear_log_btn"):
                if utils.clear_conversation_history(st.session_state.username):
                    st.success("Logs Wiped!")
                    st.rerun()
        else:
            st.info("No logs on server.")
