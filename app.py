import streamlit as st
import pandas as pd
import base64

st.set_page_config(page_title="Live Predictor Pro", layout="centered")

# --- EMBEDDED DATABASE (No CSV Required) ---
# To keep this message clean, I am using the structure. 
# You can paste your full pattern list here.
@st.cache_data
def get_patterns():
    data = [
        {"Model": "Model 1", "Pattern": "9955", "Next": "6", "Stream": "Numbers"},
        {"Model": "Model 3 (Cycle)", "Pattern": "SSBBBSSBBSB", "Next": "B -> S", "Stream": "S/B"},
        {"Model": "Model 1", "Pattern": "BGSGBRSR", "Next": "SR", "Stream": "Combined"},
        # Paste all remaining patterns from your CSV here inside this list
    ]
    return pd.DataFrame(data)

patterns = get_patterns()

# --- APP STATE ---
if 'seq' not in st.session_state: st.session_state.seq = ""
if 'history' not in st.session_state: st.session_state.history = []
if 'streak' not in st.session_state: st.session_state.streak = 0
if 'last_pred' not in st.session_state: st.session_state.last_pred = None

# --- LOGIC FUNCTIONS ---
def get_props(n_str):
    try:
        n = int(n_str.split('->')[0].strip())
        size = "BIG" if n >= 5 else "SMALL"
        color = "RED" if n % 2 == 0 else "GREEN"
        return {"val": n, "size": size, "color": color, "text": f"{n} {size} {color}"}
    except: return {"val": n_str, "size": n_str, "color": "", "text": n_str}

def translate_h(h):
    sb = "".join(['B' if int(n) >= 5 else 'S' for n in h])
    rg = "".join(['R' if int(n) % 2 == 0 else 'G' for n in h])
    return sb, rg

def process_input(num):
    # 1. Track Win/Loss of PREVIOUS prediction
    if st.session_state.last_pred:
        p = st.session_state.last_pred
        actual = get_props(num)
        win = (str(actual['size']) == str(p['size']))
        
        # Update Streak
        if win:
            st.session_state.streak = 1 if st.session_state.streak < 0 else st.session_state.streak + 1
        else:
            st.session_state.streak = -1 if st.session_state.streak > 0 else st.session_state.streak - 1
            
        st.session_state.history.insert(0, {
            "Entry": num,
            "Prediction": p['text'],
            "Result": actual['text'],
            "Status": "WIN" if win else "LOSS"
        })

    # 2. Update sequence and find NEXT prediction
    st.session_state.seq += num
    sb_h, rg_h = translate_h(st.session_state.seq)
    
    best = None
    for _, row in patterns.iterrows():
        p_val = str(row['Pattern'])
        stream = row['Stream']
        target = sb_h if stream == 'S/B' else rg_h if stream == 'R/G' else st.session_state.seq
        if target.endswith(p_val):
            if best is None or len(p_val) > len(str(best['Pattern'])):
                best = row

    if best is not None:
        st.session_state.last_pred = get_props(str(best['Next']))
    else:
        st.session_state.last_pred = None

# --- UI UI ---
st.title("🎯 Live Pattern Engine")

# Streak Display
s_color = "green" if st.session_state.streak >= 0 else "red"
st.markdown(f"### Current Streak: :{s_color}[{st.session_state.streak}]")

# 0-9 Keypad
st.write("### Input Result")
cols = st.columns(5)
for i in range(10):
    if cols[i % 5].button(str(i), use_container_width=True):
        process_input(str(i))
        st.rerun()

# Prediction Output
st.divider()
if st.session_state.last_pred:
    p = st.session_state.last_pred
    st.success(f"## NEXT PREDICTION: {p['text']}")
else:
    st.warning("No Pattern Match. Enter more numbers...")

# History Table
if st.session_state.history:
    st.write("### Game History")
    df_hist = pd.DataFrame(st.session_state.history)
    st.table(df_hist)
    
    # Download Button
    csv = df_hist.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download History CSV",
        data=csv,
        file_name='game_history.csv',
        mime='text/csv',
    )

if st.button("Reset Everything"):
    st.session_state.seq = ""
    st.session_state.history = []
    st.session_state.streak = 0
    st.session_state.last_pred = None
    st.rerun()
