import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Live Predictor Pro", layout="wide")

# Custom CSS for compact mobile view
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    div[data-testid="stVerticalBlock"] { gap: 0.5rem; }
    .stMetric { background: #1e293b; padding: 5px; border-radius: 10px; border: 1px solid #334155; }
    button { height: 40px !important; font-size: 14px !important; margin-bottom: -5px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. DATA LOADING ENGINE ---
@st.cache_data
def load_full_database():
    file_path = 'deterministic_patterns_full_analysis.csv'
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df.columns = [c.strip() for c in df.columns]
        return df
    return None

df_patterns = load_full_database()

# --- 2. SESSION STATE INITIALIZATION ---
if 'sequence' not in st.session_state: st.session_state.sequence = ""
if 'history_log' not in st.session_state: st.session_state.history_log = []
if 'streak' not in st.session_state: st.session_state.streak = 0
if 'max_win' not in st.session_state: st.session_state.max_win = 0
if 'max_loss' not in st.session_state: st.session_state.max_loss = 0
if 'total_wins' not in st.session_state: st.session_state.total_wins = 0
if 'next_pred' not in st.session_state: st.session_state.next_pred = None

# --- 3. LOGIC FUNCTIONS ---
def get_details(val):
    try:
        clean = str(val).split('->')[0].strip()
        mapping = {
            'SG': 'S-G', 'SR': 'S-R', 'BG': 'B-G', 'BR': 'B-R',
            'S': 'SMALL', 'B': 'BIG', 'R': 'RED', 'G': 'GREEN'
        }
        if clean in mapping: return mapping[clean]
        n = int(clean)
        size = "BIG" if n >= 5 else "SMALL"
        color = "RED" if n % 2 == 0 else "GREEN"
        return f"{n} {size} {color}"
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
        if target.endswith(p_val) and p_val != "" and p_val != "nan":
            if best_match is None or len(p_val) > len(str(best_match['Pattern'])):
                best_match = row
    return best_match

def handle_input(num):
    if st.session_state.next_pred:
        pred_text = st.session_state.next_pred['display']
        actual_text = get_details(num)
        is_win = ("BIG" in pred_text and num >= 5) or ("SMALL" in pred_text and num <= 4)
        
        if is_win:
            st.session_state.streak = 1 if st.session_state.streak < 0 else st.session_state.streak + 1
            st.session_state.total_wins += 1
            st.session_state.max_win = max(st.session_state.max_win, st.session_state.streak)
        else:
            st.session_state.streak = -1 if st.session_state.streak > 0 else st.session_state.streak - 1
            st.session_state.max_loss = max(st.session_state.max_loss, abs(st.session_state.streak))
            
        st.session_state.history_log.insert(0, {
            "Entry": num, "Prediction": pred_text, "Status": "WIN" if is_win else "LOSS"
        })
    else:
        st.session_state.history_log.insert(0, {
            "Entry": num, "Prediction": "N/A", "Status": "-"
        })

    st.session_state.sequence += str(num)
    match = find_match()
    if match is not None:
        st.session_state.next_pred = {
            "display": get_details(match['Next result']),
            "model": match['Model'],
            "pattern": match['Pattern'] if pd.notna(match['Pattern']) else match.get('Pattern Structure', 'N/A'),
            "count": match['Occurrence count']
        }
    else:
        st.session_state.next_pred = None

# --- 4. 2X2 ARRANGEMENT UI ---

# Split screen into two main columns
top_col1, top_col2 = st.columns(2)

# --- PART 1: DASHBOARD (Top Left) ---
with top_col1:
    st.markdown("### 📊 DASHBOARD")
    m1, m2 = st.columns(2)
    m3, m4 = st.columns(2)
    
    valid_games = [x for x in st.session_state.history_log if x['Status'] != "-"]
    win_rate = (st.session_state.total_wins / len(valid_games) * 100) if valid_games else 0
    
    m1.metric("Streak", st.session_state.streak)
    m2.metric("Win %", f"{win_rate:.0f}%")
    m3.metric("Max W", st.session_state.max_win)
    m4.metric("Max L", st.session_state.max_loss)

# --- PART 2: SHOW RESULT (Top Right) ---
with top_col2:
    st.markdown("### 🎯 PREDICTION")
    if st.session_state.next_pred:
        p = st.session_state.next_pred
        st.success(f"**NEXT: {p['display']}**")
        st.caption(f"Count: {p['count']} | Model: {p['model']}")
    else:
        st.warning("Waiting for data...")

st.divider()

# Split bottom screen into two main columns
bot_col1, bot_col2 = st.columns(2)

# --- PART 3: INPUT NUMBERS (Bottom Left) ---
with bot_col1:
    st.markdown("### ⌨️ INPUT")
    # Horizontal grid for inputs 0-9 to save vertical space
    k_row1 = st.columns(5)
    k_row2 = st.columns(5)
    for i in range(10):
        btn_label = f"R{i}" if i % 2 == 0 else f"G{i}"
        target_row = k_row1 if i < 5 else k_row2
        if target_row[i % 5].button(btn_label, use_container_width=True, key=f"btn_{i}"):
            handle_input(i)
            st.rerun()

# --- PART 4: HISTORY (Bottom Right) ---
with bot_col2:
    st.markdown("### 📝 HISTORY")
    if st.session_state.history_log:
        # Show only top 5 for compact view
        st.table(pd.DataFrame(st.session_state.history_log).head(6))
    else:
        st.write("No history yet.")

# Reset Button at the bottom center
st.divider()
if st.button("Reset All", use_container_width=True):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()
