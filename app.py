import streamlit as st
from google import genai
from PIL import Image
import json
import urllib.parse
from auth import sign_up, sign_in


# Page setup
st.set_page_config(
    page_title="FoodScope AI",
    page_icon="🍽️",
    layout="wide"
)


# Load custom CSS
def load_css():
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )


load_css()


# Login gate - Sign Up / Sign In before showing the app
if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "user_phone" not in st.session_state:
    st.session_state.user_phone = None

if not st.session_state.user_name or not st.session_state.user_phone:

    st.markdown(
        """<div class="food-header">
        <h1>🍽️ FoodScope AI</h1>
        <p>Sign in to get started</p>
        </div>""",
        unsafe_allow_html=True
    )

    tab_signin, tab_signup = st.tabs(["Sign In", "Sign Up"])

    with tab_signin:
        with st.form("signin_form"):
            si_phone = st.text_input(
                "WhatsApp Number",
                placeholder="e.g. 918871032753",
                key="si_phone"
            )
            si_password = st.text_input(
                "Password",
                type="password",
                key="si_password"
            )
            si_submitted = st.form_submit_button("Sign In")

            if si_submitted:
                cleaned_phone = si_phone.strip().replace("+", "").replace(" ", "").replace("-", "")

                if not cleaned_phone or not si_password:
                    st.error("Please enter your number and password.")
                else:
                    success, result = sign_in(cleaned_phone, si_password)
                    if success:
                        st.session_state.user_name = result
                        st.session_state.user_phone = cleaned_phone
                        st.rerun()
                    else:
                        st.error(result)

    with tab_signup:
        with st.form("signup_form"):
            su_name = st.text_input("Your Name", key="su_name")
            su_phone = st.text_input(
                "WhatsApp Number",
                placeholder="e.g. 918871032753",
                key="su_phone"
            )
            su_password = st.text_input(
                "Create Password",
                type="password",
                key="su_password"
            )
            su_submitted = st.form_submit_button("Sign Up")

            if su_submitted:
                cleaned_phone = su_phone.strip().replace("+", "").replace(" ", "").replace("-", "")

                if not su_name.strip():
                    st.error("Please enter your name.")
                elif not cleaned_phone.isdigit() or len(cleaned_phone) < 10:
                    st.error("Please enter a valid WhatsApp number with country code, no + or spaces.")
                elif len(su_password) < 4:
                    st.error("Password must be at least 4 characters.")
                else:
                    success, message = sign_up(su_name.strip(), cleaned_phone, su_password)
                    if success:
                        st.success(message + " Please sign in now.")
                    else:
                        st.error(message)

    st.stop()


# App session state (stores data between reruns)
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "nutrition_data" not in st.session_state:
    st.session_state.nutrition_data = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "summary_text" not in st.session_state:
    st.session_state.summary_text = None


# Gemini API client
client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


# Models to try, in order (falls back if one is busy/unavailable)
MODELS_TO_TRY = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash",
    "gemini-3.8-flash"
]


def generate_with_fallback(contents):
    # Try each model until one works
    last_error = None

    for model_name in MODELS_TO_TRY:
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config={
                    "http_options": {
                        "timeout": 30000
                    }
                }
            )
        except Exception as e:
            last_error = e

    raise last_error


# App header
st.markdown(
f"""<div class="food-header">
<h1>🍽️ FoodScope AI</h1>
<p>👋 Hi {st.session_state.user_name} • 📸 Scan your food • 🤖 AI nutrition analysis</p>
</div>""",
unsafe_allow_html=True
)


# Scan section intro
st.markdown(
'<div class="section-title">📸 Scan your food</div>',
unsafe_allow_html=True
)

st.markdown(
"""<div class="scan-card">
<div class="scan-title">
Take a photo or upload your food
</div>

<div class="scan-subtitle">
AI will identify the food and estimate calories, protein,
carbohydrates and fat.
</div>
</div>""",
unsafe_allow_html=True
)


# Camera and upload tabs
tab1, tab2 = st.tabs(
    ["📷 Take Photo", "📁 Upload Photo"]
)

camera_photo = None
uploaded_file = None


with tab1:
    camera_photo = st.camera_input(
        "Take a live photo of your food"
    )


with tab2:
    uploaded_file = st.file_uploader(
        "Upload a food photo",
        type=["jpg", "jpeg", "png"]
    )


# Pick whichever image source was used
selected_image = None

if camera_photo is not None:
    selected_image = Image.open(camera_photo)
elif uploaded_file is not None:
    selected_image = Image.open(uploaded_file)


# Analyze the selected image
if selected_image is not None:

    if selected_image.mode != "RGB":
        selected_image = selected_image.convert("RGB")

    # Resize large images to speed up analysis
    max_size = 1024
    if (
        selected_image.width > max_size
        or selected_image.height > max_size
    ):
        selected_image.thumbnail((max_size, max_size))

    st.image(
        selected_image,
        caption="Your food",
        use_container_width=True
    )

    if st.button("🔍 Analyze Food", key="analyze_food"):

        with st.spinner("🤖 FoodScope AI is analyzing your meal..."):

            prompt = """
You are FoodScope AI, an AI nutrition estimation assistant.

Analyze the food shown in this image.

Identify ALL clearly visible food items and estimate the nutrition
for the visible serving.

Return ONLY valid JSON.

Use exactly this structure:

{
    "food_name": "name of the complete meal",
    "portion": "estimated portion",
    "calories": 450,
    "protein": 15,
    "carbohydrates": 75,
    "fat": 8,
    "fiber": 7
}

IMPORTANT RULES:

1. calories must be a realistic INTEGER representing kcal.
2. protein, carbohydrates, fat and fiber must be numbers representing grams.
3. Do NOT return unrealistically low calories such as 42 for a normal full meal.
4. Check calorie consistency using:
   calories ≈ (protein × 4) + (carbohydrates × 4) + (fat × 9)
5. The calorie value should be reasonably consistent with the macronutrients.
6. Consider the COMPLETE visible meal, not just one ingredient.
7. Estimate the visible portion realistically.
8. If exact portion size cannot be determined from the image, make a reasonable estimate.
9. Do not include Markdown.
10. Return ONLY the JSON object.
"""

            try:
                response = generate_with_fallback([prompt, selected_image])
            except Exception as e:
                st.error(f"⚠️ AI could not analyze the image right now. Error: {e}")
                st.stop()

            result_text = response.text.strip()

            # Parse the AI's JSON response
            try:
                cleaned = (
                    result_text
                    .replace("```json", "")
                    .replace("```", "")
                    .strip()
                )
                nutrition = json.loads(cleaned)
            except Exception:
                st.error("⚠️ AI returned an invalid nutrition result. Please try the image again.")
                st.stop()

            food_name = nutrition.get("food_name", "Unknown food")
            portion = nutrition.get("portion", "Not available")
            calories = nutrition.get("calories", 0)
            protein = nutrition.get("protein", 0)
            carbs = nutrition.get("carbohydrates", 0)
            fat = nutrition.get("fat", 0)
            fiber = nutrition.get("fiber", 0)

            # Double check calories roughly match the macros
            try:
                protein_num = float(protein)
                carbs_num = float(carbs)
                fat_num = float(fat)
                calories_num = float(calories)

                calculated_calories = (
                    protein_num * 4
                    + carbs_num * 4
                    + fat_num * 9
                )

                if (
                    calculated_calories > 0
                    and calories_num < calculated_calories * 0.25
                ):
                    calories = round(calculated_calories)
                else:
                    calories = round(calories_num)
            except Exception:
                calories = calories

            final_result = {
                "food_name": food_name,
                "portion": portion,
                "calories": calories,
                "protein": protein,
                "carbohydrates": carbs,
                "fat": fat,
                "fiber": fiber
            }

            st.session_state.nutrition_data = final_result
            st.session_state.analysis_result = json.dumps(final_result, indent=2)

            # New food analyzed = start a fresh chat
            st.session_state.chat_history = []
            st.session_state.summary_text = None

            st.success("✅ Food analyzed successfully!")


# Show nutrition results
if st.session_state.nutrition_data:

    data = st.session_state.nutrition_data

    st.markdown(
        '<div class="section-title">🥗 Nutrition Analysis</div>',
        unsafe_allow_html=True
    )

    # Food name and portion card
    st.markdown(
f"""<div class="nutrition-card">
<div class="nutrition-title">
🍛 {data["food_name"]}
</div>

<div class="food-name">
📏 Portion: {data["portion"]}
</div>
</div>""",
        unsafe_allow_html=True
    )

    # Calorie circle
    calories_value = data["calories"]

    st.markdown(
f"""<div class="calorie-wrapper">
<div class="calorie-circle">
<div class="calorie-inner">

<div class="calorie-number">
{calories_value}
</div>

<div class="calorie-label">
kcal
</div>

</div>
</div>
</div>""",
        unsafe_allow_html=True
    )

    # Macro nutrient cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
f"""<div class="macro-card">
<div class="macro-value">
{data["protein"]}g
</div>

<div class="macro-label">
💪 Protein
</div>
</div>""",
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
f"""<div class="macro-card">
<div class="macro-value">
{data["carbohydrates"]}g
</div>

<div class="macro-label">
🌾 Carbs
</div>
</div>""",
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
f"""<div class="macro-card">
<div class="macro-value">
{data["fat"]}g
</div>

<div class="macro-label">
🥑 Fat
</div>
</div>""",
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
f"""<div class="macro-card">
<div class="macro-value">
{data["fiber"]}g
</div>

<div class="macro-label">
🌿 Fiber
</div>
</div>""",
            unsafe_allow_html=True
        )

    # Disclaimer
    st.markdown(
"""<div class="disclaimer">
⚠️ Nutrition values are AI estimates.
Actual nutrition can vary depending on portion size,
ingredients and cooking method.
</div>""",
        unsafe_allow_html=True
    )


    # Chat section
    st.markdown(
"""<div class="chat-card">
<div class="chat-title">
💬 Ask about this meal
</div>
</div>""",
        unsafe_allow_html=True
    )

    # Show past chat messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_question = st.chat_input("Ask something about this meal...")

    if user_question:
        st.session_state.chat_history.append(
            {"role": "user", "content": user_question}
        )

        with st.chat_message("user"):
            st.write(user_question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):

                chat_prompt = f"""
You are FoodScope AI, a friendly nutrition assistant.

Here is the analyzed meal:

{st.session_state.analysis_result}

The user wants to ask a follow-up question.

Answer clearly and concisely.

Do not invent exact nutrition information that is not
supported by the meal analysis.

User question:

{user_question}
"""

                try:
                    chat_response = generate_with_fallback([chat_prompt])
                    answer = chat_response.text
                    st.write(answer)
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": answer}
                    )
                except Exception as e:
                    st.error(f"⚠️ Could not get a response right now. {e}")


    # Summarize conversation
    if len(st.session_state.chat_history) > 0:

        st.markdown(
            '<div class="section-title">📋 Meal Conversation</div>',
            unsafe_allow_html=True
        )

        if st.button("📝 Summarize Conversation", key="summary_button"):

            with st.spinner("Creating your summary..."):

                # Build plain text transcript for the AI prompt
                history_text = ""
                for msg in st.session_state.chat_history:
                    role = "User" if msg["role"] == "user" else "AI"
                    history_text += f"{role}: {msg['content']}\n"

                summary_prompt = f"""
You are FoodScope AI.

Create a short, friendly summary of the conversation
about this meal.

Meal analysis:

{st.session_state.analysis_result}

Conversation:

{history_text}

Include:

- Food eaten
- Approximate calories
- Protein
- Carbohydrates
- Fat
- Important advice discussed

Write 3-5 short sentences.

Make it easy to share on WhatsApp.
"""

                try:
                    summary_response = generate_with_fallback([summary_prompt])
                    st.session_state.summary_text = summary_response.text
                except Exception as e:
                    st.error(f"⚠️ Could not create summary. {e}")


    # Show summary and WhatsApp share button
    if st.session_state.summary_text:

        st.markdown(
"""<div class="summary-card">
<div class="summary-title">
📋 Conversation Summary
</div>
</div>""",
            unsafe_allow_html=True
        )

        st.write(st.session_state.summary_text)

        whatsapp_message = f"""
🍽️ FoodScope AI - Meal Summary

{st.session_state.summary_text}

📸 Analyzed using FoodScope AI
"""

        encoded_message = urllib.parse.quote(whatsapp_message)

        # Sends directly to the user's own saved WhatsApp number
        whatsapp_url = f"https://wa.me/{st.session_state.user_phone}?text={encoded_message}"

        st.markdown(
f"""<a class="whatsapp-button"
href="{whatsapp_url}"
target="_blank">
💬 Share Summary on WhatsApp
</a>""",
            unsafe_allow_html=True
        )


# Footer
st.markdown(
"""<div class="food-footer">
🍽️ FoodScope AI • AI-powered nutrition estimation
</div>""",
    unsafe_allow_html=True
)