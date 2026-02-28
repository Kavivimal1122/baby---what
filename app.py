import streamlit as st
import pandas as pd

# Set page to dark mode style
st.set_page_config(page_title="Live Predictor Pro", layout="centered")

# --- 1. EMBEDDED PATTERN DATABASE ---
@st.cache_data
def load_patterns():
    # This is the structured data from your CSV
    data = [
        {"Model": "Model 1", "Pattern": "9955", "Next": "6", "Stream": "Numbers"},
        {"Model": "Model 3 (Cycle)", "Pattern": "SSBBBSSBBSB", "Next": "B", "Stream": "S/B"},
        {"Model": "Model 1", "Pattern": "BGSGBRSR", "Next": "SR", "Stream": "Combined"},
        # IMPORTANT: Paste all your CSV rows here in this format
    ]
    return pd.DataFrame(data)

patterns_df = load_patterns()

# --- 2. INITIALIZE SESSION STATE (For History Maintenance) ---
if 'sequence' not in st.session_state:
    st.session_state.sequence = ""
if 'history_log' not in st.session_state:
    st.session_state.history_log = []
if 'current_streak' not in st.session_state:
    st.session_state.current_streak = 0
if 'next_pred' not in st.session_state:
    st.session_state.next_pred = None

# --- 3. HELPER FUNCTIONS ---
def get_details(val):
    """Calculates Big/Small and Red/Green for any number."""
    try:
        # Handle cycle strings like '4 -> 3'
        clean_val = str(val).split('->')[0].strip()
        if clean_val in ['B', 'S', 'R', 'G', 'SR', 'SG', 'BR', 'BG']:
            mapping = {'B': 'BIG', 'S': 'SMALL', 'R': 'RED', 'G': 'GREEN'}
            return mapping.get(clean_val, clean_val)
        
        n = int(clean_val)
        size = "BIG" if n >= 5 else "SMALL"
        color = "RED" if n % 2 == 0 else "GREEN"
        return f"{n} {size} {color}"
    except:
        return val

def run_prediction_engine():
    """Matches the current sequence against the 100% database."""
    seq = st.session_state.sequence
    # Translations for S/B and R/G streams
    sb_seq = "".join(['B' if int(n) >= 5 else 'S' for n in seq])
    rg_seq = "".join(['R' if int(n) % 2 == 0 else 'G' for n in seq])
    
    best_match = None
    for _, row in patterns_df.iterrows():
        p = str(row['Pattern'])
        stream = row['Stream']
        
        # Determine which stream to check
        target = sb_seq if stream == 'S/B' else rg_seq if stream == 'R/G' else seq
        
        if target.endswith(p):
            if best_match is None or len(p) > len(str(best_match['Pattern'])):
                best_match = row
                
    if best_match is not None:
        st.session_state.next_pred = {
            "display": get_details(best_match['Next']),
            "raw": best_match['Next'],
            "model": best_match['Model']
        }
    else:
        st.session_state.next_pred = None

def handle_click(num):
    """Processes the new number, records history, and updates streak."""
    # A. Validate previous prediction before adding new number
    if st.session_state.next_pred:
        pred = st.session_state.next_pred['display']
        actual = get_details(num)
        
        # Win Logic (Checks if 'BIG' or 'SMALL' matches)
        is_win = False
        if ("BIG" in pred and "BIG" in actual) or ("SMALL" in pred and "SMALL" in actual):
            is_win = True
            
        # Update Streak
        if is_win:
            st.session_state.current_streak = 1 if st.session_state.current_streak < 0 else st.session_state.current_streak + 1
        else:
            st.session_state.current_streak = -1 if st.session_state.current_streak > 0 else st.session_state.current_streak - 1
            
        # Add to History List
        st.session_state.history_log.insert(0, {
            "Entry": num,
            "Predicted": pred,
            "Result": actual,
            "Status": "✅ WIN" if is_win else "❌ LOSS"
        })
    else:
        # Just log the entry if there was no prediction
        st.session_state.history_log.insert(0, {
            "Entry": num, "Predicted": "No Pattern", "Result": get_details(num), "Status": "SKIP"
        })

    # B. Add to sequence and find next prediction
    st.session_state.sequence += str(num)
    run_prediction_engine()

# --- 4. USER INTERFACE ---
st.title("🎯 Live Pattern Engine")

# Streak Display
streak = st.session_state.current_streak
color = "green" if streak >= 0 else "red"
st.subheader(f"Current Streak: :{color}[{streak}]")

# Keypad 0-9
st.write("### Select Game Result")
btn_cols = st.columns(5)
for i in range(10):
    if btn_cols[i % 5].button(str(i), use_container_width=True, key=f"btn_{i}"):
        handle_click(i)
        st.rerun()

# Prediction Output
st.divider()
if st.session_state.next_pred:
    p = st.session_state.next_pred
    st.success(f"### NEXT PREDICTION: {p['display']}")
    st.caption(f"Model: {p['model']}")
else:
    st.warning("Waiting for pattern match... Enter more numbers.")

# History Table
if st.session_state.history_log:
    st.write("### 📝 History Tracker")
    df_history = pd.DataFrame(st.session_state.history_log)
    st.table(df_history)
    
    # CSV Download
    csv_data = df_history.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download History", csv_data, "history.csv", "text/csv")

if st.button("Reset Game"):
    st.session_state.sequence = ""
    st.session_state.history_log = []
    st.session_state.current_streak = 0
    st.session_state.next_pred = None
    st.rerun()
