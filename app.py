import streamlit as st
import pandas as pd
import os

# --- 1. CONFIG & ULTRA-COMPACT CSS ---
st.set_page_config(page_title="Live Predictor Pro", layout="wide")

st.markdown("""
    <style>
    /* Force 2x2 side-by-side layout on mobile */
    [data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
    }
    /* Eliminate padding for single-screen view */
    .block-container { padding-top: 0.2rem; padding-bottom: 0rem; padding-left: 0.3rem; padding-right: 0.3rem; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }
    
    /* Tiny Metrics */
    div[data-testid="stMetric"] { background: #111827; padding: 1px 3px; border-radius: 4px; border: 1px solid #1f2937; margin-bottom: 1px; }
    div[data-testid="stMetricValue"] { font-size: 0.8rem !important; line-height: 1 !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.55rem !important; }
    
    /* VERY SMALL BUTTONS (Single Column) */
    button { 
        height: 22px !important; 
        font-size: 10px !important; 
        margin-top: -10px !important;
        margin-bottom: -15px !important; 
        padding: 0px !important; 
        line-height: 1 !important;
    }
    
    /* Micro Table Font */
    .stTable, td, th { font-size: 8.5px !important; padding: 0px 2px !important; line-height: 1 !important; }
    
    /* Section Headers */
    h3 { font-size: 0.75rem !important; margin: 2px 0px !important; color: #fbbf24; }
    .stAlert { padding: 0.2rem !important; margin-bottom: 0.2rem !important; }
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

# --- 4. LOGIC ENGINE ---
def get_details(val):
    try:
        clean = str(val).split('->')[0].strip()
        mapping = {'SG': 'S-G', 'SR': 'S-R', 'BG': 'B-G', 'BR': 'B-R', 'S': 'SML', 'B': 'BIG', 'R': 'RED', 'G': 'GRN'}
        if clean in mapping: return mapping[clean]
        n = int(clean)
        return f"{n}{'B' if n >= 5 else 'S'}{'R' if n % 2 == 0 else 'G'}"
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
        is_win = ("BIG" in pred_text and num >= 5) or ("SML" in pred_text and num <= 4) or ("B" in pred_text and num >= 5) or ("S" in pred_text and num <= 4)
        if is_win:
            st.session_state.streak = 1 if st.session_state.streak < 0 else st.session_state.streak + 1
            st.session_state.total_wins += 1
            st.session_state.max_win = max(st.session_state.max_win, st.session_state.streak)
        else:
            st.session_state.streak = -1 if st.session_state.streak > 0 else st.session_state.streak - 1
            st.session_state.max_loss = max(st.session_state.max_loss, abs(st.session_state.streak))
        st.session_state.history_log.insert(0, {"#": num, "P": pred_text[:3], "St": "W" if is_win else "L"})
    else:
        st.session_state.history_log.insert(0, {"#": num, "P": "-", "St": "-"})
    st.session_state.sequence += str(num)
    match = find_match()
    if match is not None:
        st.session_state.next_pred = {"display": get_details(match['Next result'])}
    else: st.session_state.next_pred = None

# --- 5. 2x2 UI ARRANGEMENT ---
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.write("### 📊 DASH")
    v_cnt = len([x for x in st.session_state.history_log if x['St'] != "-"])
    wp = (st.session_state.total_wins / max(1, v_cnt)) * 100
    st.metric("Streak", st.session_state.streak)
    st.metric("Win%", f"{wp:.0f}")
    st.metric("MaxW", st.session_state.max_win)
    st.metric("MaxL", st.session_state.max_loss)

with row1_col2:
    st.write("### 🎯 NEXT")
    if st.session_state.next_pred:
        st.success(f"**{st.session_state.next_pred['display']}**")
    else:
        st.info("Wait")

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.write("### ⌨️ IN")
    # Single vertical column of tiny buttons
    for i in range(10):
        c = "🔴" if i % 2 == 0 else "🟢"
        if st.button(f"{c}{i}", use_container_width=True, key=f"b_{i}"):
            handle_input(i)
            st.rerun()

with row2_col2:
    st.write("### 📝 HIST")
    if st.session_state.history_log:
        st.table(pd.DataFrame(st.session_state.history_log).head(13))
    
    if st.button("CLR", use_container_width=True):
        st.session_state.clear()
        st.rerun()
