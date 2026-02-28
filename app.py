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

# --- 2. SESSION STATE (DASHBOARD & STATS) ---
if 'sequence' not in st.session_state: st.session_state.sequence = ""
if 'history_log' not in st.session_state: st.session_state.history_log = []
if 'streak' not in st.session_state: st.session_state.streak = 0
if 'max_win_streak' not in st.session_state: st.session_state.max_win_streak = 0
if 'max_loss_streak' not in st.session_state: st.session_state.max_loss_streak = 0
if 'total_wins' not in st.session_state: st.session_state.total_wins = 0
if 'next_pred' not in st.session_state: st.session_state.next_pred = None

# --- 3. LOGIC ENGINE ---
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
        if target.endswith(p_val) and p_val != "":
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
            # Update Max Win Count
            if st.session_state.streak > st.session_state.max_win_streak:
                st.session_state.max_win_streak = st.session_state.streak
        else:
            st.session_state.streak = -1 if st.session_state.streak > 0 else st.session_state.streak - 1
            # Update Max Loss Count (streak is negative, so we use absolute value)
            if abs(st.session_state.streak) > st.session_state.max_loss_streak:
                st.session_state.max_loss_streak = abs(st.session_state.streak)
            
        st.session_state.history_log.insert(0, {
            "Entry": num, "Prediction": pred_text, "Result": actual_text, "Status": "✅ WIN" if is_win else "❌ LOSS"
        })

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
    else: st.session_state.next_pred = None

# --- 4. DASHBOARD UI ---
st.title("📊 Pro Prediction Dashboard")

# TOP DASHBOARD STATS
m1, m2, m3, m4 = st.columns(4)
valid_games = [x for x in st.session_state.history_log if x['Status'] != "SKIP"]
win_rate = (st.session_state.total_wins / len(valid_games) * 100) if valid_games else 0

m1.metric("Current Streak", st.session_state.streak)
m2.metric("Win Rate", f"{win_rate:.1f}%")
m3.metric("Max Win Streak", st.session_state.max_win_streak, delta_color="normal")
m4.metric("Max Loss Streak", st.session_state.max_loss_streak, delta_color="inverse")

# SEQUENCE BAR
st.code(f"Current Sequence: {st.session_state.sequence[-20:] if st.session_state.sequence else 'Empty'}", language="text")

st.divider()

# NEXT PREDICTION
if st.session_state.next_pred:
    p = st.session_state.next_pred
    st.success(f"### 🎯 NEXT TARGET: {p['display']}")
    
    with st.expander("View Pattern Details"):
        meta_df = pd.DataFrame({
            "Property": ["Model", "Pattern", "Length", "Occurrence", "Raw Result"],
            "Details": [p['model'], p['pattern'], p['length'], p['count'], p['raw_next']]
        })
        st.table(meta_df)
else:
    st.warning("Awaiting Pattern Match...")

# INPUT PANEL
st.write("### ⌨️ Select Game Result")
cols = st.columns(5)
for i in range(10):
    label = f"🔴 {i}" if i % 2 == 0 else f"🟢 {i}"
    if cols[i % 5].button(label, use_container_width=True, key=f"btn_{i}"):
        handle_input(i)
        st.rerun()

# HISTORY
if st.session_state.history_log:
    st.write("### 📝 History Maintenance")
    st.table(pd.DataFrame(st.session_state.history_log))
    csv = pd.DataFrame(st.session_state.history_log).to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download History", csv, "history.csv", "text/csv")

if st.button("Reset Dashboard"):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()
