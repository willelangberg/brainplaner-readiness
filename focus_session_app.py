# focus_session_app.py
import streamlit as st
import datetime
import os
import subprocess
import signal
from pathlib import Path
import sys
from supabase import create_client
from dotenv import load_dotenv

# -------------------------------------------------------
# Load environment variables (.env)
# -------------------------------------------------------
load_dotenv("config/.env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------------------------------
# Streamlit page setup
# -------------------------------------------------------
st.set_page_config(page_title="🧠 Brainplaner Focus Session", page_icon="🧠", layout="centered")
st.title("🧠 Brainplaner – Readiness & Focus Session")

st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 1rem;}
.stSlider label {font-size: 1.1rem;}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Step 1: Subjective Readiness Check-in
# -------------------------------------------------------
st.subheader("Step 1️⃣ – Daily Readiness Check-in")

today = datetime.date.today()
st.write(f"**Date:** {today}")

fatigue = st.slider("Mental Fatigue (0=fresh, 10=exhausted)", 0, 10, 5)
motivation = st.slider("Motivation (0=low, 10=high)", 0, 10, 5)
focus = st.slider("Focus (0=poor, 10=excellent)", 0, 10, 5)
mood = st.slider("Mood (0=low, 10=great)", 0, 10, 5)
stress = st.slider("Stress (0=relaxed, 10=stressed)", 0, 10, 5)
sleep_quality = st.slider("Sleep Quality (0=bad, 10=good)", 0, 10, 5)
comment = st.text_input("Notes (optional)")

if "form_saved" not in st.session_state:
    st.session_state.form_saved = False

if st.button("✅ Save Readiness"):
    try:
        response = sb.table("subjective_daily_ratings").insert({
            "date": str(today),
            "fatigue": fatigue,
            "motivation": motivation,
            "focus": focus,
            "mood": mood,
            "stress": stress,
            "sleep_quality": sleep_quality,
            "comment": comment
        }).execute()
        st.session_state.form_saved = True
        st.session_state.form_id = response.data[0].get("id") if response.data else None
        st.success("✅ Readiness saved successfully! You can now start your session.")
    except Exception as e:
        st.error(f"❌ Failed to save readiness: {e}")

st.divider()

# -------------------------------------------------------
# Step 2: Focus Session Control
# -------------------------------------------------------
st.subheader("Step 2️⃣ – Start / Stop Focus Session")

if "session_active" not in st.session_state:
    st.session_state.session_active = False
if "logger_process" not in st.session_state:
    st.session_state.logger_process = None

if not st.session_state.form_saved:
    st.warning("Please complete and save your readiness check-in before starting.")
else:
    if not st.session_state.session_active:
        if st.button("▶️ Start Focus Session"):
            try:
                # Create session in Supabase
                start_time = datetime.datetime.now().isoformat()
                response = sb.table("sessions").insert({
                    "session_start": start_time,
                    "form_id": st.session_state.form_id,
                    "device": "computer"
                }).execute()
                session_id = response.data[0]["id"]
                st.session_state.session_id = session_id
                st.session_state.session_active = True

                # Start the computer logger using absolute paths and the current Python executable
                ROOT = Path(__file__).resolve().parents[2]   # project root (brainplaner)
                SCRIPTS = ROOT / "scripts"
                LOGGER = SCRIPTS / "computer_logger.py"
                DATA_LOGS = ROOT / "data" / "logs"
                DATA_LOGS.mkdir(parents=True, exist_ok=True)
                output_file = str(DATA_LOGS / f"session_{session_id}.csv")
                process = subprocess.Popen(
                    [sys.executable, str(LOGGER), "--session-id", str(session_id), "--output-file", output_file],
                    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
                )
                st.session_state.logger_process = process
                st.success(f"🧠 Session started at {start_time}")
            except Exception as e:
                st.error(f"❌ Failed to start session: {e}")
    else:
        if st.button("⏹ Stop Focus Session"):
            try:
                end_time = datetime.datetime.now().isoformat()
                sb.table("sessions").update({
                    "session_end": end_time
                }).eq("id", st.session_state.session_id).execute()

                # Stop computer logger process
                if st.session_state.logger_process:
                    st.session_state.logger_process.send_signal(signal.SIGINT)
                    st.session_state.logger_process = None

                st.session_state.session_active = False
                st.success(f"✅ Session stopped at {end_time}")
            except Exception as e:
                st.error(f"❌ Failed to stop session: {e}")
