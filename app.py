import streamlit as st
import os
import io
import json
from utils.pin_text import generate_pins

st.set_page_config(
    page_title="📌 Pin Generator",
    page_icon="📌",
    layout="wide"
)

PINS_CACHE = "last_pins.json"

# ── AUTO LOAD API KEY FROM SECRETS ──────
def get_groq_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except:
        return st.session_state.get("groq_key", "")

# ── SAVE / LOAD PINS FROM FILE ──────────
def save_pins(pins, analysis):
    with open(PINS_CACHE, "w") as f:
        json.dump({"pins": pins, "analysis": analysis}, f)

def load_pins():
    if os.path.exists(PINS_CACHE):
        with open(PINS_CACHE, "r") as f:
            data = json.load(f)
            return data.get("pins"), data.get("analysis")
    return None, None

# ── SESSION STATE INIT ───────────────────
if "image_bytes_list" not in st.session_state:
    st.session_state.image_bytes_list = []
if "pins" not in st.session_state:
    saved_pins, saved_analysis = load_pins()
    st.session_state.pins = saved_pins
    st.session_state.analysis = saved_analysis

# ── HEADER ──────────────────────────────
st.title("📌 Pinterest Pin Generator")

groq_key = get_groq_key()

# show key input only if not found in secrets
if not groq_key:
    st.warning("Groq API key not found in secrets. Enter it below.")
    manual_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    if manual_key:
        st.session_state.groq_key = manual_key
        groq_key = manual_key
else:
    st.success("✅ API Key loaded automatically")

st.markdown("---")

# ── SIDEBAR ─────────────────────────────
with st.sidebar:
    st.header("📦 Product Info")

    amazon_url = st.text_input(
        "Amazon URL (optional)",
        placeholder="https://www.amazon.in/..."
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

# ── MAIN INPUT ──────────────────────────
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
        st.error("Groq API key missing.")
    elif not st.session_state.image_bytes_list:
        st.error("Please upload at least one image.")
    elif not user_idea:
        st.error("Please describe your pin idea.")
    else:
        with st.spinner("Analyzing product and generating pins..."):
            try:
                os.environ["GROQ_API_KEY"] = groq_key
                image_files = [
                    io.BytesIO(b)
                    for b in st.session_state.image_bytes_list
                ]
                pins, analysis = generate_pins(image_files, amazon_url, user_idea)
                st.session_state.pins = pins
                st.session_state.analysis = analysis
                save_pins(pins, analysis)
                st.success("✅ Pins generated and saved!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ── RESULTS ─────────────────────────────
if st.session_state.pins:
    pins = st.session_state.pins
    analysis = st.session_state.analysis

    st.markdown("---")

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

    for i, (col, pin) in enumerate(zip(cols, pins)):
        with col:
            st.markdown(f"### 🎯 Pin {i+1}: {pin['pin_angle']}")

            st.markdown("**🪝 Title**")
            st.info(pin['title'])

            st.markdown("**📝 Description**")
            st.write(pin['description'])

            st.markdown("**✅ Key Points**")
            for point in pin['bullet_points']:
                st.markdown(f"• {point}")

            st.markdown("**⭐ Rating Angle**")
            st.success(pin['rating_tip'])

            st.markdown("**🎨 Image Prompt**")
            st.code(pin['image_prompt'], language=None)

            content = (
                f"PIN {i+1}: {pin['pin_angle']}\n\n"
                f"TITLE:\n{pin['title']}\n\n"
                f"DESCRIPTION:\n{pin['description']}\n\n"
                f"KEY POINTS:\n" +
                "\n".join([f"• {p}" for p in pin['bullet_points']]) +
                f"\n\nRATING TIP:\n{pin['rating_tip']}\n\n"
                f"IMAGE PROMPT:\n{pin['image_prompt']}"
            )

            st.download_button(
                label=f"⬇️ Download Pin {i+1}",
                data=content,
                file_name=f"pin_{i+1}.txt",
                mime="text/plain"
            )

    # download all pins together
    all_content = ""
    for i, pin in enumerate(pins):
        all_content += (
            f"PIN {i+1}: {pin['pin_angle']}\n\n"
            f"TITLE:\n{pin['title']}\n\n"
            f"DESCRIPTION:\n{pin['description']}\n\n"
            f"KEY POINTS:\n" +
            "\n".join([f"• {p}" for p in pin['bullet_points']]) +
            f"\n\nRATING TIP:\n{pin['rating_tip']}\n\n"
            f"IMAGE PROMPT:\n{pin['image_prompt']}\n\n"
            f"{'='*50}\n\n"
        )

    st.markdown("---")
    st.download_button(
        label="⬇️ Download All 3 Pins Together",
        data=all_content,
        file_name="all_pins.txt",
        mime="text/plain",
        use_container_width=True
    )