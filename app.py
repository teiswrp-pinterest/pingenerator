import streamlit as st
from utils.pin_text import generate_pins

st.set_page_config(
    page_title="Pinterest Pin Generator",
    page_icon="📌",
    layout="wide"
)

st.title("📌 Pinterest Pin Generator")
st.markdown("Upload product screenshots, give your idea — get 3 ready-to-use pins with image prompts.")

# sidebar
with st.sidebar:
    st.header("⚙️ Setup")
    groq_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    st.markdown("---")
    st.header("📦 Product Info")
    amazon_url = st.text_input("Amazon URL (optional)", placeholder="https://www.amazon.in/...")
    uploaded_files = st.file_uploader(
        "Upload Product Screenshots",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True
    )
    if uploaded_files:
        st.success(f"{len(uploaded_files)} image(s) uploaded")
        for f in uploaded_files:
            #st.image(f, use_column_width=True)
            st.image(f, use_container_width=True)
            f.seek(0)

# main area
st.markdown("### 💡 Your Pin Idea")
user_idea = st.text_area(
    "Describe your 3 pin angles in rough words",
    placeholder="e.g. earphones - pin1 for budget buyers, pin2 for gym use, pin3 for travel",
    height=100
)

generate_btn = st.button("🚀 Generate 3 Pins", type="primary", use_container_width=True)

if generate_btn:
    if not groq_key:
        st.error("Please enter your Groq API key in the sidebar.")
    elif not uploaded_files:
        st.error("Please upload at least one product screenshot.")
    elif not user_idea:
        st.error("Please describe your pin idea.")
    else:
        with st.spinner("Analyzing product and generating pins..."):
            try:
                import os
                os.environ["GROQ_API_KEY"] = groq_key

                #pins = generate_pins(uploaded_files, amazon_url, user_idea)
                pins, analysis = generate_pins(uploaded_files, amazon_url, user_idea)

                st.markdown("---")
                with st.expander("🔍 Product Visual Analysis (what the AI saw in your images)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Product:** {analysis.get('product_name','')}")
                        st.markdown(f"**Colors:** {analysis.get('colors','')}")
                        st.markdown(f"**Material Feel:** {analysis.get('material_feel','')}")
                        st.markdown(f"**Mood:** {analysis.get('mood','')}")
                    with col2:
                        st.markdown(f"**Lighting:** {analysis.get('lighting_style','')}")
                        st.markdown(f"**Key Visual Features:** {analysis.get('key_visual_features','')}")
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

                        st.download_button(
                            label=f"⬇️ Download Pin {i+1} Content",
                            data=f"PIN {i+1}: {pin['pin_angle']}\n\nTITLE:\n{pin['title']}\n\nDESCRIPTION:\n{pin['description']}\n\nKEY POINTS:\n" + "\n".join([f"• {p}" for p in pin['bullet_points']]) + f"\n\nRATING TIP:\n{pin['rating_tip']}\n\nIMAGE PROMPT:\n{pin['image_prompt']}",
                            file_name=f"pin_{i+1}.txt",
                            mime="text/plain"
                        )

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")