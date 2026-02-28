import streamlit as st
import pandas as pd
import os

# --- 1. CONFIG & MOBILE STYLING ---
st.set_page_config(page_title="Live Predictor Pro", layout="wide")

st.markdown("""
    <style>
    /* Force columns to stay side-by-side even on small mobile screens */
    [data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
    }
    /* Reduce padding to fit one screen */
    .block-container { padding-top: 0.5rem; padding-bottom: 0rem; padding-left: 0.5rem; padding-right: 0.5rem; }
    div[data-testid="stVerticalBlock"] { gap: 0.2rem !important; }
    
    /* Small Metrics */
    div[data-testid="stMetric"] { background: #1e293b; padding: 2px 5px; border-radius: 5px; border: 1px solid #334155; margin-bottom: 2px; }
    div[data-testid="stMetricValue"] { font-size: 0.9rem !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.6rem !important; }
    
    /* Compact Buttons */
    button { height: 32px !important; font-size: 12px !important; margin-bottom: -15px !important; padding: 0px !important; }
    
    /* Table font size */
    .stTable, td, th { font-size: 9px !important; padding: 1px !important; }
    
    /* Section Headers */
    h3 { font-size: 0.8rem !important; margin-top: 2px !important; margin-bottom: 2px !important; color: #fbbf24; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADING ENGINE ---
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
        mapping = {'SG': 'S-G', 'SR': 'S-R', 'BG': 'B-G', 'BR': 'B-R', 'S': 'SMALL', 'B': 'BIG', 'R': 'RED', 'G': 'GREEN'}
        if clean in mapping: return mapping[clean]
        n = int(clean)
        size = "B" if n >= 5 else "S"
        color = "R" if n % 2 == 0 else "G"
        return f"{n} {size}{color}"
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
        pred_text = st.session_state.next_pred['display']
        is_win = ("BIG" in pred_text and num >= 5) or ("SMALL" in pred_text and num <= 4) or ("B" in pred_text and num >= 5) or ("S" in pred_text and num <= 4)
        if is_win:
            st.session_state.streak = 1 if st.session_state.streak < 0 else st.session_state.streak + 1
            st.session_state.total_wins += 1
            st.session_state.max_win = max(st.session_state.max_win, st.session_state.streak)
        else:
            st.session_state.streak = -1 if st.session_state.streak > 0 else st.session_state.streak - 1
            st.session_state.max_loss = max(st.session_state.max_loss, abs(st.session_state.streak))
        st.session_state.history_log.insert(0, {"#": num, "P": pred_text[:4], "Res": "W" if is_win else "L"})
    else:
        st.session_state.history_log.insert(0, {"#": num, "P": "-", "Res": "-"})
    st.session_state.sequence += str(num)
    match = find_match()
    if match is not None:
        st.session_state.next_pred = {"display": get_details(match['Next result']), "m": match['Model'], "p": match['Pattern']}
    else: st.session_state.next_pred = None

# --- 5. 2x2 UI ARRANGEMENT ---

row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.write("### 📊 DASH")
    # Single column stack for dashboard metrics
    valid_count = len([x for x in st.session_state.history_log if x['Res'] != "-"])
    win_p = (st.session_state.total_wins / max(1, valid_count)) * 100
    st.metric("Streak", st.session_state.streak)
    st.metric("Win%", f"{win_p:.0f}%")
    st.metric("MaxW", st.session_state.max_win)
    st.metric("MaxL", st.session_state.max_loss)

with row1_col2:
    st.write("### 🎯 NEXT")
    if st.session_state.next_pred:
        st.success(f"**{st.session_state.next_pred['display']}**")
    else:
        st.info("Wait...")

st.divider()

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.write("### ⌨️ INPUT")
    # Vertical single column of buttons
    for i in range(10):
        label = f"🔴 {i}" if i % 2 == 0 else f"🟢 {i}"
        if st.button(label, use_container_width=True, key=f"btn_{i}"):
            handle_input(i)
            st.rerun()

with row2_col2:
    st.write("### 📝 HIST")
    if st.session_state.history_log:
        st.table(pd.DataFrame(st.session_state.history_log).head(12))
    
    if st.button("Reset", use_container_width=True):
        st.session_state.clear()
        st.rerun()
