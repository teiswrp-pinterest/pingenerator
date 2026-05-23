import os
import base64
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def images_to_base64(image_files):
    encoded = []
    for img_file in image_files:
        encoded.append(base64.b64encode(img_file.read()).decode("utf-8"))
        img_file.seek(0)
    return encoded

# ─────────────────────────────────────────
# STEP 1: Deep visual analysis of product
# ─────────────────────────────────────────
def analyze_product_images(image_files):

    encoded_images = images_to_base64(image_files)

    content = []
    for b64 in encoded_images:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
        })

    content.append({
        "type": "text",
        "text": """
Analyze this product image in detail. Return ONLY a JSON object, no extra text:

{
  "product_name": "what the product is",
  "colors": "exact colors you see - primary and accent colors",
  "material_feel": "does it look premium, matte, glossy, fabric, plastic, metal etc",
  "shape_form": "describe the physical shape and size feel",
  "mood": "what mood does this product give - minimal, bold, playful, premium, sporty etc",
  "background_in_photo": "describe the background style in the uploaded image",
  "lighting_style": "soft, harsh, studio, natural, dramatic etc",
  "key_visual_features": "2-3 most visually striking things about this product",
  "target_feel": "who does this product visually speak to - students, professionals, athletes etc"
}
"""
    })

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": content}],
        temperature=0.3
    )

    raw = response.choices[0].message.content.strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    analysis = json.loads(raw[start:end])
    return analysis


# ─────────────────────────────────────────
# STEP 2: Generate pins using visual analysis
# ─────────────────────────────────────────
def generate_pins_from_analysis(analysis, amazon_url, user_idea):

    analysis_text = json.dumps(analysis, indent=2)

    prompt = f"""
You are an expert Pinterest content strategist and visual designer.

Here is a detailed visual analysis of the product:
{analysis_text}

Amazon URL for reference: {amazon_url if amazon_url else "Not provided"}
User's pin idea: {user_idea}

Using the EXACT visual details from the analysis above, create 3 Pinterest pin variations.
Each pin should target a DIFFERENT angle as suggested by the user.

For each pin return:
1. pin_angle: the specific angle (e.g. "Budget Pick", "Gym Use", "Travel Essential")
2. title: hook-style title under 10 words, use 1-2 relevant emoticons, make people stop scrolling
3. description: 2-3 sentences, hook then reveal style, sprinkle 2-3 emoticons naturally, end with soft CTA that has an emoticon
4. bullet_points: 3-4 key product highlights as short punchy phrases with emoticons
5. rating_tip: one sentence using Amazon ratings angle with an emoticon
6. image_prompt: a highly detailed prompt grounded in the ACTUAL product visuals from the analysis.
   Must include:
   - exact product colors and materials from analysis
   - specific background style matching the pin angle
   - lighting mood matching the angle
   - where text overlay should go and what it should say
   - Pinterest 2:3 ratio mention
   - overall aesthetic feel for that specific angle
   Make this so specific that Gemini or GPT generates something very close to the actual product.

Return ONLY a valid JSON array, no extra text:
[
  {{
    "pin_angle": "",
    "title": "",
    "description": "",
    "bullet_points": ["", "", ""],
    "rating_tip": "",
    "image_prompt": ""
  }},
  {{
    "pin_angle": "",
    "title": "",
    "description": "",
    "bullet_points": ["", "", ""],
    "rating_tip": "",
    "image_prompt": ""
  }},
  {{
    "pin_angle": "",
    "title": "",
    "description": "",
    "bullet_points": ["", "", ""],
    "rating_tip": "",
    "image_prompt": ""
  }}
]
"""

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        temperature=0.85
    )

    raw = response.choices[0].message.content.strip()
    start = raw.find("[")
    end = raw.rfind("]") + 1
    pins = json.loads(raw[start:end])
    return pins


# ─────────────────────────────────────────
# MAIN FUNCTION called from app.py
# ─────────────────────────────────────────
def generate_pins(image_files, amazon_url, user_idea):
    analysis = analyze_product_images(image_files)
    pins = generate_pins_from_analysis(analysis, amazon_url, user_idea)
    return pins, analysis