import streamlit as st
import pandas as pd

st.set_page_config(page_title="Live Pattern Predictor", layout="centered")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    df = pd.read_csv('deterministic_patterns_full_analysis.csv')
    return df[df['Accuracy %'] == 100.0]

patterns = load_data()

# --- HELPER FUNCTIONS ---
def get_props(val):
    if val in ['B', 'S', 'R', 'G', 'SR', 'SG', 'BR', 'BG']:
        m = {'B': 'BIG', 'S': 'SMALL', 'R': 'RED', 'G': 'GREEN', 'SR': 'SMALL RED', 'SG': 'SMALL GREEN', 'BR': 'BIG RED', 'BG': 'BIG GREEN'}
        return m.get(val, val)
    try:
        n = int(val)
        return f"{n} ({'BIG' if n >= 5 else 'SMALL'}) ({'RED' if n % 2 == 0 else 'GREEN'})"
    except: return val

def translate(h):
    sb = "".join(['B' if int(n) >= 5 else 'S' for n in h])
    rg = "".join(['R' if int(n) % 2 == 0 else 'G' for n in h])
    return sb, rg

# --- UI DESIGN ---
st.title("🎯 Live Prediction Engine")
st.subheader("100% Deterministic Patterns")

if 'history' not in st.session_state:
    st.session_state.history = ""
if 'logs' not in st.session_state:
    st.session_state.logs = []

# Input Area
user_input = st.text_input("Enter Result (0-9):", key="input_box")

if user_input:
    # Track entry
    st.session_state.history += user_input
    h = st.session_state.history
    sb_h, rg_h = translate(h)
    
    # Matching Engine
    best = None
    for _, row in patterns.iterrows():
        p = str(row['Pattern'])
        stream = row['Stream']
        target = sb_h if stream == 'S/B' else rg_h if stream == 'R/G' else h
        
        if target.endswith(p):
            if best is None or len(p) > len(str(best['Pattern'])):
                best = row

    # Prediction Output
    st.divider()
    if best is not None:
        pred_raw = str(best['Next result']).split('->')[0].strip()
        result_text = get_props(pred_raw)
        st.success(f"### NEXT PREDICTION: {result_text}")
        st.info(f"Model: {best['Model']} | Pattern: {best['Pattern']} | Acc: 100%")
    else:
        st.warning("No 100% Match Found. Keep entering numbers...")

# History Display
st.divider()
st.write("**Sequence History:**", st.session_state.history)
if st.button("Clear History"):
    st.session_state.history = ""
    st.rerun()
