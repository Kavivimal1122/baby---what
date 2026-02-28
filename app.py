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
    else:
        return None

df_patterns = load_full_database()

# --- 2. SESSION STATE ---
if 'sequence' not in st.session_state: st.session_state.sequence = ""
if 'history_log' not in st.session_state: st.session_state.history_log = []
if 'streak' not in st.session_state: st.session_state.streak = 0
if 'next_pred' not in st.session_state: st.session_state.next_pred = None

# --- 3. RULE ENGINE ---
def get_details(val):
    try:
        clean = str(val).split('->')[0].strip()
        # Handle Category letters
        if clean in ['B', 'S', 'R', 'G', 'SR', 'SG', 'BR', 'BG']:
            m = {'B': 'BIG', 'S': 'SMALL', 'R': 'RED', 'G': 'GREEN', 'SR': 'SMALL RED', 'SG': 'SMALL GREEN', 'BR': 'BIG RED', 'BG': 'BIG GREEN'}
            return m.get(clean, clean)
        
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
        is_win = ("BIG" in pred and num >= 5) or ("SMALL" in pred and num <= 4)
        
        if is_win:
            st.session_state.streak = 1 if st.session_state.streak < 0 else st.session_state.streak + 1
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
        st.session_state.next_pred = {
            "display": get_details(match['Next result']),
            "model": match['Model'], "pattern": match['Pattern']
        }
    else:
        st.session_state.next_pred = None

# --- 4. USER INTERFACE ---
st.title("🎯 Live Prediction Engine")

if df_patterns is None:
    st.error("CSV File NOT FOUND! Please upload 'deterministic_patterns_full_analysis.csv'.")
else:
    streak = st.session_state.streak
    st.subheader(f"Current Streak: :{'green' if streak >= 0 else 'red'}[{streak}]")

    st.write("### Input Latest Number")
    
    # Define Colors: Even = Red, Odd = Green
    cols = st.columns(5)
    for i in range(10):
        # Determine color based on number
        label_color = "🔴" if i % 2 == 0 else "🟢"
        button_label = f"{label_color} {i}"
        
        if cols[i % 5].button(button_label, use_container_width=True, key=f"k_{i}"):
            handle_input(i)
            st.rerun()

    st.divider()
    if st.session_state.next_pred:
        p = st.session_state.next_pred
        st.success(f"### NEXT PREDICTION: {p['display']}")
        st.caption(f"Model: {p['model']} | Pattern: {p['pattern']}")
    else:
        st.warning("No pattern match found. Keep entering numbers...")

    if st.session_state.history_log:
        st.write("### 📝 Game History")
        df_hist = pd.DataFrame(st.session_state.history_log)
        st.table(df_hist)
        csv = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download History CSV", csv, "history.csv", "text/csv")

    if st.button("Reset Game"):
        st.session_state.sequence = ""
        st.session_state.history_log = []
        st.session_state.streak = 0
        st.session_state.next_pred = None
        st.rerun()
