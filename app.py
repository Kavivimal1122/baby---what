import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Live Predictor Pro", layout="centered")

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
            'SG': 'SMALL GREEN', 'SR': 'SMALL RED', 'BG': 'BIG GREEN', 'BR': 'BIG RED',
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
    # Process Previous Prediction
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
            "Entry": num, "Prediction": pred_text, "Result": actual_text, "Status": "✅ WIN" if is_win else "❌ LOSS"
        })
    else:
        st.session_state.history_log.insert(0, {
            "Entry": num, "Prediction": "No Match", "Result": get_details(num), "Status": "SKIP"
        })

    # Update Sequence and Find Next
    st.session_state.sequence += str(num)
    match = find_match()
    if match is not None:
        st.session_state.next_pred = {
            "display": get_details(match['Next result']),
            "model": match['Model'],
            "pattern": match['Pattern'] if pd.notna(match['Pattern']) else match.get('Pattern Structure', 'N/A'),
            "length": match['Length'],
            "count": match['Occurrence count'],
            "raw_next": match['Next result']
        }
    else:
        st.session_state.next_pred = None

# --- 4. UI DASHBOARD ---
st.title("📊 Prediction Dashboard")

# Top Stats Row
m1, m2, m3, m4 = st.columns(4)
valid_games = [x for x in st.session_state.history_log if x['Status'] != "SKIP"]
win_rate = (st.session_state.total_wins / len(valid_games) * 100) if valid_games else 0

m1.metric("Streak", st.session_state.streak)
m2.metric("Win %", f"{win_rate:.1f}%")
m3.metric("Max Win", st.session_state.max_win)
m4.metric("Max Loss", st.session_state.max_loss)

st.divider()

# Prediction Display
if st.session_state.next_pred:
    p = st.session_state.next_pred
    st.success(f"### 🎯 NEXT: {p['display']}")
    with st.expander("Show Pattern Data"):
        st.write(f"**Model:** {p['model']}")
        st.write(f"**Pattern:** {p['pattern']}")
        st.write(f"**Occurrence Count:** {p['count']}")
else:
    st.warning("Enter numbers to match patterns...")

# MOBILE-OPTIMIZED VERTICAL KEYPAD
st.write("### ⌨️ Select Number")
# This creates a vertical list of buttons 0 to 9 as requested
for i in range(10):
    btn_label = f"🔴 {i}" if i % 2 == 0 else f"🟢 {i}"
    if st.button(btn_label, use_container_width=True, key=f"mobile_btn_{i}"):
        handle_input(i)
        st.rerun()

# PERSISTENT HISTORY TABLE
st.divider()
if st.session_state.history_log:
    st.write("### 📝 History Maintenance")
    # Using st.table for clearer mobile visibility of pasted history
    st.table(pd.DataFrame(st.session_state.history_log))
    
    # Download Button
    csv = pd.DataFrame(st.session_state.history_log).to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download History", csv, "history.csv", "text/csv")

if st.button("Reset All Records"):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()
