import streamlit as st
import os
import io
import json
from utils.pin_text import generate_pins
from streamlit_javascript import st_javascript

st.set_page_config(
    page_title="📌 Pin Generator",
    page_icon="📌",
    layout="wide"
)

PINS_CACHE = "last_pins.json"

def save_pins(pins, analysis, amazon_url):
    with open(PINS_CACHE, "w") as f:
        json.dump({"pins": pins, "analysis": analysis, "amazon_url": amazon_url}, f)

def load_pins():
    if os.path.exists(PINS_CACHE):
        with open(PINS_CACHE, "r") as f:
            data = json.load(f)
            return data.get("pins"), data.get("analysis"), data.get("amazon_url", "")
    return None, None, ""

# ── SESSION STATE ────────────────────────
if "image_bytes_list" not in st.session_state:
    st.session_state.image_bytes_list = []
if "pins" not in st.session_state:
    saved_pins, saved_analysis, saved_url = load_pins()
    st.session_state.pins = saved_pins
    st.session_state.analysis = saved_analysis
    st.session_state.saved_url = saved_url
if "groq_key" not in st.session_state:
    st.session_state.groq_key = ""
if "changing_key" not in st.session_state:
    st.session_state.changing_key = False

# ── LOAD API KEY ─────────────────────────
# Priority: Streamlit Secrets → localStorage → manual input
def get_key():
    # 1. try streamlit secrets first
    try:
        key = st.secrets["GROQ_API_KEY"]
        if key:
            return key, "secrets"
    except:
        pass
    # 2. try session state (from localStorage or manual)
    if st.session_state.groq_key:
        return st.session_state.groq_key, "stored"
    return "", "none"

groq_key, key_source = get_key()

# read from localStorage as backup
stored_key = st_javascript("localStorage.getItem('groq_key') || ''")
if stored_key and stored_key != 0 and not groq_key:
    st.session_state.groq_key = stored_key
    groq_key = stored_key
    key_source = "stored"

# ── HEADER ──────────────────────────────
st.title("📌 Pinterest Pin Generator")
st.markdown("---")

# ── API KEY SECTION ──────────────────────
with st.expander("🔑 API Key", expanded=(key_source == "none" or st.session_state.changing_key)):

    if key_source == "secrets":
        st.success("✅ API Key loaded from Streamlit Secrets — no action needed")

    elif groq_key and not st.session_state.changing_key:
        st.success("✅ API Key loaded from phone memory")
        if st.button("🔄 Change Key"):
            st.session_state.changing_key = True
            st.session_state.groq_key = ""
            st_javascript("localStorage.removeItem('groq_key')")
            st.rerun()
    else:
        st.markdown("Paste your Groq API key — saved automatically to this phone.")
        new_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
        if st.button("💾 Save Key to Phone", use_container_width=True):
            if new_key:
                st.session_state.groq_key = new_key
                st.session_state.changing_key = False
                groq_key = new_key
                st_javascript(f"localStorage.setItem('groq_key', '{new_key}')")
                st.success("✅ Key saved!")
                st.rerun()
            else:
                st.error("Please paste your key first.")

# ── SIDEBAR ──────────────────────────────
with st.sidebar:
    st.header("📦 Product Info")

    amazon_url = st.text_input(
        "Amazon URL",
        placeholder="https://www.amazon.in/...",
        value=st.session_state.get("saved_url", "")
    )

    uploaded_files = st.file_uploader(
        "Upload Product Images",
        type=None,
        accept_multiple_files=True
    )

    if uploaded_files:
        st.session_state.image_bytes_list = [f.read() for f in uploaded_files]
        for f in uploaded_files:
            f.seek(0)

    if st.session_state.image_bytes_list:
        st.success(f"{len(st.session_state.image_bytes_list)} image(s) ready")
        for img_bytes in st.session_state.image_bytes_list:
            st.image(img_bytes, use_container_width=True)

    if st.button("🗑️ Clear Images", use_container_width=True):
        st.session_state.image_bytes_list = []
        st.rerun()

# ── MAIN INPUT ───────────────────────────
st.markdown("### 💡 Your Pin Idea")
user_idea = st.text_area(
    "Describe your 3 pin angles",
    placeholder="e.g. earphones - pin1 budget, pin2 gym, pin3 travel",
    height=100
)

generate_btn = st.button(
    "🚀 Generate 3 Pins",
    type="primary",
    use_container_width=True
)

if generate_btn:
    if not groq_key:
        st.error("API key missing. Please add it above.")
    elif not st.session_state.image_bytes_list:
        st.error("Please upload at least one image.")
    elif not user_idea:
        st.error("Please describe your pin idea.")
    else:
        with st.spinner("Analyzing product and generating pins..."):
            try:
                os.environ["GROQ_API_KEY"] = groq_key
                image_files = [io.BytesIO(b) for b in st.session_state.image_bytes_list]
                pins, analysis = generate_pins(image_files, amazon_url, user_idea)
                st.session_state.pins = pins
                st.session_state.analysis = analysis
                st.session_state.saved_url = amazon_url
                save_pins(pins, analysis, amazon_url)
                st.success("✅ Pins generated!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ── RESULTS ──────────────────────────────
if st.session_state.pins:
    pins     = st.session_state.pins
    analysis = st.session_state.analysis
    url      = st.session_state.get("saved_url", "")

    st.markdown("---")

    # Amazon URL display
    if url:
        st.markdown("### 🛒 Product Link")
        st.markdown(f"[{url}]({url})")

    # analysis expander
    if analysis:
        with st.expander("🔍 Product Visual Analysis"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Product:** {analysis.get('product_name','')}")
                st.markdown(f"**Colors:** {analysis.get('colors','')}")
                st.markdown(f"**Mood:** {analysis.get('mood','')}")
            with col2:
                st.markdown(f"**Lighting:** {analysis.get('lighting_style','')}")
                st.markdown(f"**Key Features:** {analysis.get('key_visual_features','')}")
                st.markdown(f"**Speaks To:** {analysis.get('target_feel','')}")

    st.markdown("## 📌 Your 3 Pins")
    cols = st.columns(3)

    all_content = ""
    if url:
        all_content += f"PRODUCT LINK:\n{url}\n\n{'='*50}\n\n"

    for i, (col, pin) in enumerate(zip(cols, pins)):
        bullet_text = "\n".join([f"• {p}" for p in pin['bullet_points']])

        with col:
            st.markdown(f"### 🎯 Pin {i+1}: {pin['pin_angle']}")

            st.markdown("**🪝 Title**")
            st.code(pin['title'], language=None)

            st.markdown("**📝 Description**")
            st.code(pin['description'], language=None)

            st.markdown("**✅ Key Points**")
            st.code(bullet_text, language=None)

            st.markdown("**⭐ Rating Angle**")
            st.code(pin['rating_tip'], language=None)

            st.markdown("**🎨 Image Prompt**")
            st.code(pin['image_prompt'], language=None)

        # build download content
        all_content += (
            f"PIN {i+1}: {pin['pin_angle']}\n\n"
            f"TITLE:\n{pin['title']}\n\n"
            f"DESCRIPTION:\n{pin['description']}\n\n"
            f"KEY POINTS:\n{bullet_text}\n\n"
            f"RATING TIP:\n{pin['rating_tip']}\n\n"
            f"IMAGE PROMPT:\n{pin['image_prompt']}\n\n"
            f"{'='*50}\n\n"
        )

    # ── SINGLE DOWNLOAD BUTTON ────────────
    st.markdown("---")
    st.download_button(
        label="⬇️ Download All 3 Pins",
        data=all_content,
        file_name="all_pins.txt",
        mime="text/plain",
        use_container_width=True,
        type="primary"
    )