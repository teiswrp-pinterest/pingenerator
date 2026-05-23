import streamlit as st
import os
from utils.pin_text import generate_pins

st.set_page_config(
    page_title="Pinterest Pin Generator",
    page_icon="📌",
    layout="wide"
)

# initialise session state
if "groq_key" not in st.session_state:
    st.session_state.groq_key = ""
if "pins" not in st.session_state:
    st.session_state.pins = None
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "image_bytes_list" not in st.session_state:
    st.session_state.image_bytes_list = []
if "image_names" not in st.session_state:
    st.session_state.image_names = []

st.title("📌 Pinterest Pin Generator")
st.markdown("Upload product screenshots, give your idea — get 3 ready-to-use pins with image prompts.")

# ── SIDEBAR ──────────────────────────────
with st.sidebar:
    st.header("⚙️ Setup")

    key_input = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        value=st.session_state.groq_key
    )
    if key_input:
        st.session_state.groq_key = key_input

    st.markdown("---")
    st.header("📦 Product Info")

    amazon_url = st.text_input(
        "Amazon URL (optional)",
        placeholder="https://www.amazon.in/..."
    )

    st.markdown("**Upload Screenshots**")
    uploaded_files = st.file_uploader(
        "Choose from files",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="file_uploader"
    )

    st.markdown("**Or take a photo 📷**")
    camera_photo = st.camera_input("Take product photo")

    # store uploaded file bytes in session state
    if uploaded_files:
        st.session_state.image_bytes_list = [f.read() for f in uploaded_files]
        st.session_state.image_names = [f.name for f in uploaded_files]
        for f in uploaded_files:
            f.seek(0)

    # add camera photo to list
    if camera_photo:
        cam_bytes = camera_photo.read()
        if cam_bytes not in st.session_state.image_bytes_list:
            st.session_state.image_bytes_list.append(cam_bytes)
            st.session_state.image_names.append("camera_photo.jpg")

    # show stored images
    if st.session_state.image_bytes_list:
        st.success(f"{len(st.session_state.image_bytes_list)} image(s) ready")
        for img_bytes in st.session_state.image_bytes_list:
            st.image(img_bytes, use_container_width=True)

    if st.button("🗑️ Clear Images", use_container_width=True):
        st.session_state.image_bytes_list = []
        st.session_state.image_names = []
        st.rerun()

# ── MAIN AREA ─────────────────────────────
st.markdown("### 💡 Your Pin Idea")
user_idea = st.text_area(
    "Describe your 3 pin angles in rough words",
    placeholder="e.g. earphones - pin1 for budget buyers, pin2 for gym use, pin3 for travel",
    height=100
)

generate_btn = st.button(
    "🚀 Generate 3 Pins",
    type="primary",
    use_container_width=True
)

if generate_btn:
    if not st.session_state.groq_key:
        st.error("Please enter your Groq API key in the sidebar.")
    elif not st.session_state.image_bytes_list:
        st.error("Please upload at least one product screenshot.")
    elif not user_idea:
        st.error("Please describe your pin idea.")
    else:
        with st.spinner("Analyzing product and generating pins..."):
            try:
                os.environ["GROQ_API_KEY"] = st.session_state.groq_key

                # convert stored bytes back to file-like objects
                import io
                image_files = [
                    io.BytesIO(b)
                    for b in st.session_state.image_bytes_list
                ]

                pins, analysis = generate_pins(image_files, amazon_url, user_idea)
                st.session_state.pins = pins
                st.session_state.analysis = analysis

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")

# ── RESULTS ───────────────────────────────
if st.session_state.pins:
    pins = st.session_state.pins
    analysis = st.session_state.analysis

    st.markdown("---")

    with st.expander("🔍 Product Visual Analysis (what the AI saw)"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Product:** {analysis.get('product_name','')}")
            st.markdown(f"**Colors:** {analysis.get('colors','')}")
            st.markdown(f"**Material Feel:** {analysis.get('material_feel','')}")
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

            st.markdown("**🎨 Image Prompt for Gemini/GPT**")
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