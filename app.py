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

# --- 2. SESSION STATE (DASHBOARD STORAGE) ---
if 'sequence' not in st.session_state: st.session_state.sequence = ""
if 'history_log' not in st.session_state: st.session_state.history_log = []
if 'streak' not in st.session_state: st.session_state.streak = 0
if 'next_pred' not in st.session_state: st.session_state.next_pred = None
if 'total_wins' not in st.session_state: st.session_state.total_wins = 0

# --- 3. LOGIC ENGINE ---
def get_details(val):
    try:
        clean = str(val).split('->')[0].strip()
        if clean in ['B', 'S', 'R', 'G', 'SR', 'SG', 'BR', 'BG']:
            m = {'B': 'BIG', 'S': 'SMALL', 'R': 'RED', 'G': 'GREEN', 'SR': 'SMALL RED', 'SG': 'SMALL GREEN', 'BR': 'BIG RED', 'BG': 'BIG GREEN'}
            return m.get(clean, clean)
        n = int(clean)
        return f"{n} {'BIG' if n >= 5 else 'SMALL'} {'RED' if n % 2 == 0 else 'GREEN'}"
    except: return str(val)

def find_match():
    if df_patterns is None: return None
    seq = st.session_state.sequence
    sb_seq = "".join(['B' if int(n) >= 5 else 'S' for n in seq])
    rg_seq = "".join(['R' if int(n) % 2 == 0 else 'G' for n in seq])
    best_match = None
    for _, row in df_patterns.iterrows():
        p_val = str(row['Pattern'])
        stream = str(row['Stream'])
        target = sb_seq if "S/B" in stream else rg_seq if "R/G" in stream else seq
        if target.endswith(p_val):
            if best_match is None or len(p_val) > len(str(best_match['Pattern'])):
                best_match = row
    return best_match

def handle_input(num):
    if st.session_state.next_pred:
        pred = st.session_state.next_pred['display']
        actual = get_details(num)
        # Match logic based on Small/Big
        is_win = ("BIG" in pred and num >= 5) or ("SMALL" in pred and num <= 4)
        
        if is_win:
            st.session_state.streak = 1 if st.session_state.streak < 0 else st.session_state.streak + 1
            st.session_state.total_wins += 1
        else:
            st.session_state.streak = -1 if st.session_state.streak > 0 else st.session_state.streak - 1
            
        st.session_state.history_log.insert(0, {
            "Entry": num, "Prediction": pred, "Result": actual, "Status": "✅ WIN" if is_win else "❌ LOSS"
        })
    else:
        st.session_state.history_log.insert(0, {
            "Entry": num, "Prediction": "No Match", "Result": get_details(num), "Status": "SKIP"
        })

    st.session_state.sequence += str(num)
    match = find_match()
    if match is not None:
        st.session_state.next_pred = {"display": get_details(match['Next result']), "model": match['Model'], "pattern": match['Pattern']}
    else: st.session_state.next_pred = None

# --- 4. DASHBOARD UI ---
st.title("📊 Prediction Dashboard")

# Top Dashboard Stats
t1, t2, t3 = st.columns(3)
total_games = len([x for x in st.session_state.history_log if x['Status'] != "SKIP"])
win_rate = (st.session_state.total_wins / total_games * 100) if total_games > 0 else 0

t1.metric("Current Streak", st.session_state.streak)
t2.metric("Win Rate", f"{win_rate:.1f}%")
t3.metric("Total Games", total_games)

# Colored Input Keypad
st.write("### ⌨️ Input Panel")
cols = st.columns(5)
for i in range(10):
    # Even = Red (🔴), Odd = Green (🟢)
    label = f"🔴 {i}" if i % 2 == 0 else f"🟢 {i}"
    if cols[i % 5].button(label, use_container_width=True, key=f"btn_{i}"):
        handle_input(i)
        st.rerun()

# Live Prediction
st.divider()
if st.session_state.next_pred:
    p = st.session_state.next_pred
    st.success(f"### 🎯 NEXT PREDICTION: {p['display']}")
    st.caption(f"Pattern: {p['pattern']} | {p['model']}")
else:
    st.warning("Awaiting Match... Enter more numbers.")

# History Table
if st.session_state.history_log:
    st.write("### 📝 History Maintenance")
    df_hist = pd.DataFrame(st.session_state.history_log)
    st.table(df_hist)
    
    # Download History
    csv = df_hist.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download History Report", csv, "history.csv", "text/csv")

if st.button("Reset Dashboard"):
    for key in st.session_state.keys(): del st.session_state[key]
    st.rerun()
