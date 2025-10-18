# subjective_form.py
import streamlit as st
import datetime
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables from Streamlit Cloud secrets or local .env
load_dotenv("config/.env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Connect to Supabase
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# Streamlit page setup
st.set_page_config(page_title="Brain Readiness", page_icon="🧠", layout="centered")
st.title("🧠 Daily Readiness Check-in")

st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 1rem;}
.stSlider label {font-size: 1.1rem;}
</style>
""", unsafe_allow_html=True)

# --- Optional: show yesterday's Oura sleep score (if available) ---
try:
    from datetime import date, timedelta
    yesterday = str(date.today() - timedelta(days=1))
    sleep = sb.table("oura_daily_sleep").select("*").eq("day", yesterday).execute().data
    if sleep:
        score = sleep[0]["sleep_score"]
        st.metric("Yesterday's Oura Sleep Score", score)
except Exception as e:
    st.caption("Oura data not available.")

# --- Daily rating form ---
today = datetime.date.today()

st.subheader(f"Date: {today}")

fatigue = st.slider("Mental Fatigue (0=fresh, 10=exhausted)", 0, 10, 5)
motivation = st.slider("Motivation (0=low, 10=high)", 0, 10, 5)
focus = st.slider("Focus (0=poor, 10=excellent)", 0, 10, 5)
mood = st.slider("Mood (0=low, 10=great)", 0, 10, 5)
stress = st.slider("Stress (0=relaxed, 10=stressed)", 0, 10, 5)
sleep_quality = st.slider("Sleep Quality (0=bad, 10=good)", 0, 10, 5)
comment = st.text_input("Notes (optional)")

if st.button("Save"):
    try:
        sb.table("subjective_daily_ratings").upsert({
            "date": str(today),
            "fatigue": fatigue,
            "motivation": motivation,
            "focus": focus,
            "mood": mood,
            "stress": stress,
            "sleep_quality": sleep_quality,
            "comment": comment
        }).execute()
        st.success("✅ Saved to Supabase!")
    except Exception as e:
        st.error(f"Failed to upload: {e}")
