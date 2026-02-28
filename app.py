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
        # Standardize column names to match your CSV exactly
        df.columns = [c.strip() for c in df.columns]
        return df
    else:
        return None

df_patterns = load_full_database()

# --- 2. SESSION STATE (HISTORY MAINTENANCE) ---
if 'sequence' not in st.session_state: st.session_state.sequence = ""
if 'history_log' not in st.session_state: st.session_state.history_log = []
if 'streak' not in st.session_state: st.session_state.streak = 0
if 'next_pred' not in st.session_state: st.session_state.next_pred = None

# --- 3. RULE ENGINE (The "Translator") ---
def get_details(val):
    """Applies your game rules: 0-4 Small, 5-9 Big | Even Red, Odd Green"""
    try:
        # Handle cycle results like "4 -> 3"
        clean = str(val).split('->')[0].strip()
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
    """Matches history against Numbers, S/B, and R/G rules in the CSV"""
    if df_patterns is None: return None
    
    seq = st.session_state.sequence
    # Internal Translation for comparison
    sb_seq = "".join(['B' if int(n) >= 5 else 'S' for n in seq])
    rg_seq = "".join(['R' if int(n) % 2 == 0 else 'G' for n in seq])
    
    best_match = None
    
    for _, row in df_patterns.iterrows():
        p_val = str(row['Pattern'])
        stream = str(row['Stream'])
        
        # Determine which sequence to check based on the 'Stream' column in CSV
        if "S/B" in stream or "Category" in stream:
            target = sb_seq
        elif "R/G" in stream:
            target = rg_seq
        else:
            target = seq # Numbers or Combined
            
        if target.endswith(p_val):
            # Prioritize the longest matching pattern for accuracy
            if best_match is None or len(p_val) > len(str(best_match['Pattern'])):
                best_match = row
                
    return best_match

def handle_input(num):
    # 1. Record Result of the PREVIOUS prediction
    if st.session_state.next_pred:
        pred = st.session_state.next_pred['display']
        actual = get_details(num)
        
        # WIN/LOSS logic based on Small/Big match
        is_win = False
        if ("BIG" in pred and num >= 5) or ("SMALL" in pred and num <= 4):
            is_win = True
        
        # Update Streak
        if is_win:
            st.session_state.streak = 1 if st.session_state.streak < 0 else st.session_state.streak + 1
        else:
            st.session_state.streak = -1 if st.session_state.streak > 0 else st.session_state.streak - 1
            
        st.session_state.history_log.insert(0, {
            "Entry": num,
            "Prediction": pred,
            "Result": actual,
            "Status": "✅ WIN" if is_win else "❌ LOSS"
        })
    else:
        st.session_state.history_log.insert(0, {
            "Entry": num, "Prediction": "No Match", "Result": get_details(num), "Status": "SKIP"
        })

    # 2. Add to sequence and find NEXT
    st.session_state.sequence += str(num)
    match = find_match()
    if match is not None:
        st.session_state.next_pred = {
            "display": get_details(match['Next result']),
            "model": match['Model'],
            "pattern": match['Pattern']
        }
    else:
        st.session_state.next_pred = None

# --- 4. USER INTERFACE ---
st.title("🎯 Live Prediction Engine")

if df_patterns is None:
    st.error("CSV File NOT FOUND! Please upload 'deterministic_patterns_full_analysis.csv' to GitHub.")
else:
    # Stats
    streak = st.session_state.streak
    st.subheader(f"Current Streak: :{'green' if streak >= 0 else 'red'}[{streak}]")

    # Keypad
    st.write("### Input Latest Number")
    cols = st.columns(5)
    for i in range(10):
        if cols[i % 5].button(str(i), use_container_width=True, key=f"k_{i}"):
            handle_input(i)
            st.rerun()

    # Next Target
    st.divider()
    if st.session_state.next_pred:
        p = st.session_state.next_pred
        st.success(f"### NEXT PREDICTION: {p['display']}")
        st.caption(f"Based on Model: {p['model']} | Pattern: {p['pattern']}")
    else:
        st.warning("No pattern match found. Keep entering numbers...")

    # History & Download
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
