import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Live Predictor Pro", layout="centered")

# ---------------- COMPACT CSS ----------------
st.markdown("""
<style>
.block-container { padding: 5px 10px 5px 10px !important; }

h1 { font-size:18px !important; margin-bottom:5px !important; }
h3 { font-size:14px !important; margin-bottom:3px !important; }

div[data-testid="metric-container"] {
    padding:4px !important;
}

div[data-testid="metric-container"] > div {
    font-size:12px !important;
}

div.stButton > button {
    height:38px !important;
    font-size:14px !important;
    font-weight:600 !important;
    padding:0px !important;
}

.small-history table {
    font-size:10px !important;
}

.stDivider { margin:4px 0px !important; }

</style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data
def load_full_database():
    file_path = 'deterministic_patterns_full_analysis.csv'
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df.columns = [c.strip() for c in df.columns]
        return df
    return None

df_patterns = load_full_database()

# --- SESSION STATE ---
if 'sequence' not in st.session_state: st.session_state.sequence = ""
if 'history_log' not in st.session_state: st.session_state.history_log = []
if 'streak' not in st.session_state: st.session_state.streak = 0
if 'max_win' not in st.session_state: st.session_state.max_win = 0
if 'max_loss' not in st.session_state: st.session_state.max_loss = 0
if 'total_wins' not in st.session_state: st.session_state.total_wins = 0
if 'next_pred' not in st.session_state: st.session_state.next_pred = None

# --- LOGIC FUNCTIONS (UNCHANGED) ---
def get_details(val):
    try:
        clean = str(val).split('->')[0].strip()
        mapping = {
            'SG': 'SMALL GREEN', 'SR': 'SMALL RED', 'BG': 'BIG GREEN', 'BR': 'BIG RED',
            'S': 'SMALL', 'B': 'BIG', 'R': 'RED', 'G': 'GREEN'
        }
        if clean in mapping: return mapping[clean]
        n = int(clean)
        size = "BIG" if n >= 5 else "SMALL"
        color = "RED" if n % 2 == 0 else "GREEN"
        return f"{n} {size} {color}"
    except:
        return str(val)

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
            "Entry": num,
            "Prediction": pred_text,
            "Result": actual_text,
            "Status": "✅ WIN" if is_win else "❌ LOSS"
        })
    else:
        st.session_state.history_log.insert(0, {
            "Entry": num,
            "Prediction": "No Match",
            "Result": get_details(num),
            "Status": "SKIP"
        })

    st.session_state.sequence += str(num)
    match = find_match()
    if match is not None:
        st.session_state.next_pred = {
            "display": get_details(match['Next result']),
            "model": match['Model'],
            "pattern": match['Pattern'],
            "length": match['Length'],
            "count": match['Occurrence count']
        }
    else:
        st.session_state.next_pred = None

# ---------------- UI ----------------

st.title("📊 Predictor")

# Compact Metrics
col1, col2, col3, col4 = st.columns(4)
valid_games = [x for x in st.session_state.history_log if x['Status'] != "SKIP"]
win_rate = (st.session_state.total_wins / len(valid_games) * 100) if valid_games else 0

col1.metric("Streak", st.session_state.streak)
col2.metric("Win %", f"{win_rate:.1f}%")
col3.metric("Max W", st.session_state.max_win)
col4.metric("Max L", st.session_state.max_loss)

# Prediction
if st.session_state.next_pred:
    st.success(f"🎯 {st.session_state.next_pred['display']}")
else:
    st.warning("Waiting...")

# ---------- GRID KEYPAD ----------
st.markdown("### Keypad")

row1 = st.columns(5)
row2 = st.columns(5)

for i in range(5):
    if row1[i].button(str(i), use_container_width=True):
        handle_input(i)
        st.rerun()

for i in range(5, 10):
    if row2[i-5].button(str(i), use_container_width=True):
        handle_input(i)
        st.rerun()

# ---------- COMPACT HISTORY ----------
if st.session_state.history_log:
    st.markdown("### History")
    small_df = pd.DataFrame(st.session_state.history_log[:5])
    st.markdown('<div class="small-history">', unsafe_allow_html=True)
    st.table(small_df)
    st.markdown('</div>', unsafe_allow_html=True)

    csv = pd.DataFrame(st.session_state.history_log).to_csv(index=False).encode('utf-8')
    st.download_button("Download", csv, "history.csv", "text/csv")

if st.button("Reset"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
