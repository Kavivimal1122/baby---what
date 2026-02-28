import streamlit as st
import pandas as pd
import os

# --- 1. CONFIG & CSS (FORCED 2x2 ON MOBILE) ---
st.set_page_config(page_title="Live Predictor Pro", layout="wide")

st.markdown("""
    <style>
    /* Force columns to stay side-by-side on mobile */
    [data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
    }
    /* Compact spacing */
    .block-container { padding-top: 0.5rem; padding-bottom: 0rem; padding-left: 0.5rem; padding-right: 0.5rem; }
    div[data-testid="stVerticalBlock"] { gap: 0.1rem !important; }
    
    /* Metrics Styling */
    div[data-testid="stMetric"] { background: #1e293b; padding: 2px 5px; border-radius: 5px; border: 1px solid #334155; }
    div[data-testid="stMetricValue"] { font-size: 1.1rem !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.7rem !important; }
    
    /* Tiny buttons to fit 10 in one column */
    button { height: 28px !important; font-size: 11px !important; margin-bottom: -18px !important; padding: 0px !important; }
    
    /* Table font size */
    .stTable, td, th { font-size: 10px !important; padding: 2px !important; }
    
    /* Section Headers */
    h3 { font-size: 0.9rem !important; margin-top: 5px !important; margin-bottom: 2px !important; color: #fbbf24; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADING ---
@st.cache_data
def load_full_database():
    file_path = 'deterministic_patterns_full_analysis.csv'
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df.columns = [c.strip() for c in df.columns]
        return df
    return None

df_patterns = load_full_database()

# --- 3. SESSION STATE ---
if 'sequence' not in st.session_state: st.session_state.sequence = ""
if 'history_log' not in st.session_state: st.session_state.history_log = []
if 'streak' not in st.session_state: st.session_state.streak = 0
if 'max_win' not in st.session_state: st.session_state.max_win = 0
if 'max_loss' not in st.session_state: st.session_state.max_loss = 0
if 'total_wins' not in st.session_state: st.session_state.total_wins = 0
if 'next_pred' not in st.session_state: st.session_state.next_pred = None

# --- 4. LOGIC FUNCTIONS ---
def get_details(val):
    try:
        clean = str(val).split('->')[0].strip()
        mapping = {'SG':'S-G','SR':'S-R','BG':'B-G','BR':'B-R','S':'SMALL','B':'BIG','R':'RED','G':'GREEN'}
        if clean in mapping: return mapping[clean]
        n = int(clean)
        return f"{n} {'B' if n >= 5 else 'S'} {'R' if n % 2 == 0 else 'G'}"
    except: return str(val)

def find_match():
    if df_patterns is None: return None
    seq = st.session_state.sequence
    sb_seq = "".join(['B' if int(n) >= 5 else 'S' for n in seq])
    rg_seq = "".join(['R' if int(n) % 2 == 0 else 'G' for n in seq])
    best_match = None
    for _, row in df_patterns.iterrows():
        p_val = str(row['Pattern']) if pd.notna(row['Pattern']) else str(row.get('Pattern Structure', ''))
        stream = str(row['Stream'])
        target = sb_seq if "S/B" in stream else rg_seq if "R/G" in stream else seq
        if target.endswith(p_val) and p_val not in ["", "nan"]:
            if best_match is None or len(p_val) > len(str(best_match['Pattern'])):
                best_match = row
    return best_match

def handle_input(num):
    if st.session_state.next_pred:
        pred_text, actual_text = st.session_state.next_pred['display'], get_details(num)
        is_win = ("BIG" in pred_text and num >= 5) or ("SMALL" in pred_text and num <= 4)
        if is_win:
            st.session_state.streak = 1 if st.session_state.streak < 0 else st.session_state.streak + 1
            st.session_state.total_wins += 1
            st.session_state.max_win = max(st.session_state.max_win, st.session_state.streak)
        else:
            st.session_state.streak = -1 if st.session_state.streak > 0 else st.session_state.streak - 1
            st.session_state.max_loss = max(st.session_state.max_loss, abs(st.session_state.streak))
        st.session_state.history_log.insert(0, {"#": num, "P": pred_text[:5], "Res": "WIN" if is_win else "LOSE"})
    else:
        st.session_state.history_log.insert(0, {"#": num, "P": "N/A", "Res": "-"})
    st.session_state.sequence += str(num)
    match = find_match()
    if match is not None:
        st.session_state.next_pred = {"display": get_details(match['Next result']), "m": match['Model'], "p": match['Pattern']}
    else: st.session_state.next_pred = None

# --- 5. 2X2 DASHBOARD ARRANGEMENT ---

# TOP ROW
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.write("### 📊 DASH")
    m1, m2 = st.columns(2)
    m3, m4 = st.columns(2)
    m1.metric("Str", st.session_state.streak)
    m2.metric("MaxW", st.session_state.max_win)
    m3.metric("MaxL", st.session_state.max_loss)
    m4.metric("Win%", f"{(st.session_state.total_wins/max(1,len(st.session_state.history_log))*100):.0f}%")

with row1_col2:
    st.write("### 🎯 NEXT")
    if st.session_state.next_pred:
        st.success(f"**{st.session_state.next_pred['display']}**")
    else:
        st.info("Input 5+ digits")

# BOTTOM ROW
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.write("### ⌨️ INPUT")
    # Vertical column of 10 buttons
    for i in range(10):
        label = f"🔴 {i}" if i % 2 == 0 else f"🟢 {i}"
        if st.button(label, use_container_width=True, key=f"btn_{i}"):
            handle_input(i)
            st.rerun()

with row2_col2:
    st.write("### 📝 HISTORY")
    if st.session_state.history_log:
        st.table(pd.DataFrame(st.session_state.history_log).head(10))
    
    if st.button("Reset", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
