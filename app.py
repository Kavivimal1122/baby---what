import streamlit as st
import pandas as pd
import os

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Live Predictor", layout="centered")

# Custom CSS to force compact layout and hide extra padding
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    div[data-testid="stMetric"] { padding: 5px; border: 1px solid #333; border-radius: 5px; }
    button { height: 45px !important; font-weight: bold !important; margin-bottom: -10px !important; }
    .stTable { font-size: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADING ---
@st.cache_data
def load_db():
    f = 'deterministic_patterns_full_analysis.csv'
    if os.path.exists(f):
        df = pd.read_csv(f)
        df.columns = [c.strip() for c in df.columns]
        return df
    return None

df_patterns = load_db()

# --- 3. STATE ---
if 'sequence' not in st.session_state: st.session_state.sequence = ""
if 'history_log' not in st.session_state: st.session_state.history_log = []
if 'streak' not in st.session_state: st.session_state.streak = 0
if 'max_win' not in st.session_state: st.session_state.max_win = 0
if 'max_loss' not in st.session_state: st.session_state.max_loss = 0
if 'next_pred' not in st.session_state: st.session_state.next_pred = None

# --- 4. ENGINE ---
def get_details(val):
    try:
        clean = str(val).split('->')[0].strip()
        mapping = {'SG':'S-G', 'SR':'S-R', 'BG':'B-G', 'BR':'B-R', 'S':'SMALL', 'B':'BIG'}
        if clean in mapping: return mapping[clean]
        n = int(clean)
        return f"{n} {'BIG' if n >= 5 else 'SMALL'} {'RED' if n % 2 == 0 else 'GREEN'}"
    except: return str(val)

def find_match():
    if df_patterns is None: return None
    seq = st.session_state.sequence
    sb = "".join(['B' if int(n) >= 5 else 'S' for n in seq])
    rg = "".join(['R' if int(n) % 2 == 0 else 'G' for n in seq])
    best = None
    for _, row in df_patterns.iterrows():
        p, s = str(row['Pattern']), str(row['Stream'])
        target = sb if "S/B" in s else rg if "R/G" in s else seq
        if target.endswith(p) and p not in ["", "nan"]:
            if best is None or len(p) > len(str(best['Pattern'])): best = row
    return best

def handle_input(num):
    if st.session_state.next_pred:
        pred, act = st.session_state.next_pred['display'], get_details(num)
        win = ("BIG" in pred and num >= 5) or ("SMALL" in pred and num <= 4)
        st.session_state.streak = (1 if st.session_state.streak < 0 else st.session_state.streak + 1) if win else (-1 if st.session_state.streak > 0 else st.session_state.streak - 1)
        st.session_state.max_win = max(st.session_state.max_win, st.session_state.streak)
        st.session_state.max_loss = max(st.session_state.max_loss, abs(st.session_state.streak))
        st.session_state.history_log.insert(0, {"#": num, "P": pred[:5], "Stat": "W" if win else "L"})
    else:
        st.session_state.history_log.insert(0, {"#": num, "P": "N/A", "Stat": "-"})
    st.session_state.sequence += str(num)
    m = find_match()
    st.session_state.next_pred = {"display": get_details(m['Next result']), "m": m['Model'], "p": m['Pattern']} if m is not None else None

# --- 5. COMPACT MOBILE UI ---
# Row 1: Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Str", st.session_state.streak)
m2.metric("W%", f"{(st.session_state.streak/max(1,len(st.session_state.history_log))*100):.0f}%")
m3.metric("MW", st.session_state.max_win)
m4.metric("ML", st.session_state.max_loss)

# Row 2: Prediction
if st.session_state.next_pred:
    st.success(f"**NEXT: {st.session_state.next_pred['display']}**")
else:
    st.info("Waiting for Pattern...")

# Row 3: Grid Keypad (5x2)
st.write("### Input")
k1, k2, k3, k4, k5 = st.columns(5)
for i in range(10):
    label = f"R{i}" if i % 2 == 0 else f"G{i}"
    target_col = [k1, k2, k3, k4, k5][i % 5]
    if target_col.button(label, use_container_width=True):
        handle_input(i)
        st.rerun()

# Row 4: History (Limited height table)
if st.session_state.history_log:
    st.write("### History")
    # Show only last 5 rows to save space
    st.dataframe(pd.DataFrame(st.session_state.history_log).head(5), use_container_width=True, hide_index=True)

if st.button("Reset"):
    st.session_state.clear()
    st.rerun()
