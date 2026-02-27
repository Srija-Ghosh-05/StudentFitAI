import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
from PIL import Image
from dotenv import load_dotenv

# Load the secret key from the .env file
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

if not GOOGLE_API_KEY:
    st.error("API Key not found. Please add it to your .env file.")
else:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

st.set_page_config(page_title="Student Fitness AI", layout="wide")

# --- THEME STATE MANAGEMENT ---
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
col_title, col_space, col_toggle = st.columns([10, 1, 2])
with col_title:
    st.title("🎓 StudentFitAI: AI-Powered Personalized Workout & Diet Planner 💪")
with col_toggle:
    col_light, col_checkbox, col_dark = st.columns([3, 2, 3])
    with col_light:
        st.write("☀️ Light Mode")
    with col_checkbox:
        st.session_state.dark_mode = st.toggle("", value=st.session_state.dark_mode)
    with col_dark:
        st.write("🌙 Dark Mode")

if st.session_state.dark_mode:
    # DARK THEME
    bg_color = "#0e1117"
    text_color = "#ffffff"
    card_bg = "#1d2129"
    dl_btn_bg = "#1d2129"
    dl_btn_text = "#ffffff"
else:
    # LIGHT THEME
    bg_color = "#ffffff"
    text_color = "#31333F"
    card_bg = "#ffffff"
    dl_btn_bg = "#ffffff"
    dl_btn_text = "#31333f"

# Injecting the styles based on the toggle state
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    
    /* 1. Fix the Upload Box & THE BLUE BROWSE BUTTON */
    [data-testid="stFileUploaderDropzone"] {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border: 2px dashed #4f8bf9 !important;
        border-radius: 12px !important;
    }}

    /* This makes the actual 'Browse files' button Blue */
    [data-testid="stFileUploaderDropzone"] button {{
        background-color: #4f8bf9 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }}

    /* Target the inner white region of the uploader */
    [data-testid="stFileUploaderDropzone"] > div {{
        background-color: {card_bg} !important;
    }}

    /* 2. Repair Corners (Remove 'wired' floating lines) */
    [data-testid="stForm"] {{
        background-color: {card_bg} !important;
        border: 1px solid #4f8bf9 !important;
        border-radius: 12px !important;
        padding: 20px;
    }}

    /* Remove default borders that clash with custom corners */
    .stExpander {{
        border: none !important;
        background-color: transparent !important;
    }}

    /* Use overflow:hidden to force internal white boxes to match rounded blue corners */
    .stExpander > details {{
        border: 1px solid #4f8bf9 !important;
        border-radius: 12px !important;
        background-color: {card_bg} !important;
        overflow: hidden !important;
    }}

    /* 3. Fix internal white backgrounds in Expanders */
    [data-testid="stExpanderDetails"] {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        padding: 15px;
        border-top: 1px solid #4f8bf9 !important;
    }}

    /* 4. Text & Button General Styling */
    .stExpander summary p, .stExpander summary span, .stExpander label {{
        color: {text_color} !important;
    }}

    h1, h2, h3, p, label, span, .stMarkdown {{
        color: {text_color} !important;
    }}
    
    div.stButton > button[kind="primary"] {{
        background-color: #4f8bf9 !important;
        color: white !important;
        border-radius: 8px !important;
    }}

    div.stDownloadButton > button {{
        background-color: {dl_btn_bg} !important;
        border: 1px solid #4f8bf9 !important;
        border-radius: 8px !important;
    }}

    div.stDownloadButton > button p, 
    div.stDownloadButton > button span {{
        color: {dl_btn_text} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# Initialize session state variables for food and room analysis results and images
if 'food_result' not in st.session_state:
    st.session_state.food_result = None
if 'food_image' not in st.session_state:
    st.session_state.food_image = None
if 'room_result' not in st.session_state:
    st.session_state.room_result = None
if 'room_image' not in st.session_state:
    st.session_state.room_image = None
if 'health_profile' not in st.session_state:
    st.session_state.health_profile = ""

# --- Create Tabs ---
tab1, tab2, tab3 = st.tabs(["📋 Plan Generator", "🥗 Food Scanner", "🏋️ Room/Gym Analyzer"])

with tab1:
    col_input, col_display = st.columns([1, 2])

    with col_input:
        # Use a Form to batch all inputs together
        with st.form("user_profile_form"):
            st.subheader("📋 Your Profile")
            
            # Basic Info
            goal = st.selectbox("Fitness Goal", ["Weight Loss", "Weight Gain", "Muscle Gain", "Strength", "Endurance", "General Fitness", "Fat Loss", "Stress Relief", "Improve Energy", "Posture Improvement"])
            budget = st.select_slider("Daily Budget", options=["Hostel/Tight", "Moderate", "High"])
            
            # Health & Medical
            with st.expander("🩺 Health & Medical Conditions"):
                medical = st.text_area("Medical Conditions", placeholder="e.g. Asthma, Knee pain, Type 2 Diabetes")
                dietary_restrictions = st.text_area("Dietary Restrictions", placeholder="e.g. Vegan, Vegetarian, Halal, Gluten-Free, No Nuts, No Dairy")

            # Current Routine & Preferences
            with st.expander("🏃 Lifestyle & Routine"):
                routine = st.radio("Current Activity Level", ["Sedentary", "Lightly Active", "Very Active"])
                activity = st.text_input("Activity Specifications", placeholder="e.g. None, Gym, Walking/Jogging, Yoga, Dance")
                culture = st.text_input("Cultural Food Habits", placeholder="e.g. Mediterranean, South Indian")

            exam_mode = st.checkbox("📚 Exam Week Mode (Quick Workouts & Brain Food)")
            st.markdown("---")

            # Additional Notes
            st.subheader("📝 Personal Requests")
            additional_notes = st.text_area("Anything else?", 
                placeholder="e.g. I want to lose 10kg in 3 months, give me quick meals for busy exam days, I don't have a microwave...")

            # THE SUBMIT BUTTON
            submitted = st.form_submit_button("Generate My Personalized Plan", type="primary", use_container_width=True)

    with col_display:
        st.header("✨ Your AI-Generated Plan")
        if 'plan' not in st.session_state:
            st.session_state.plan = None
        if submitted:
            # SAVE THE PROFILE TO SESSION STATE SO OTHER TABS CAN SEE IT
            st.session_state.health_profile = f"""
            Goal: {goal}, Budget: {budget}, 
            Medical: {medical}, Restrictions: {dietary_restrictions}, 
            Activity: {routine} ({activity}), Culture: {culture}
            """
            with st.spinner("Gemini is analyzing your health profile..."):
                # 1. Create the detailed prompt for the AI
                exam_instructions = ""
                if exam_mode:
                    exam_instructions = """
                    CRITICAL: The user is in EXAM WEEK. 
                    1. Limit all workouts to exactly 15 minutes (HIIT or stretching).
                    2. Focus meals on 'Brain Foods' (Omega-3s, complex carbs, blueberries, nuts).
                    3. Suggest low-caffeine energy boosters to avoid study crashes.
                    4. Keep instructions extremely short and easy to read.
                    """
                prompt = f"""
                You are a professional Fitness & Nutrition Coach. Create a highly personalized 7-day plan.
                {exam_instructions}
                
                USER PROFILE:
                - Goal: {goal}
                - Budget Level: {budget}
                - Medical Conditions: {medical if medical else 'None'}
                - Dietary Restrictions: {dietary_restrictions if dietary_restrictions else 'None'}
                - Activity Level: {routine}
                - Current Activity: {activity if activity else 'General'}
                - Cultural Food Style: {culture if culture else 'Global'}
                - Specific Request: {additional_notes if additional_notes else 'None'}

                OUTPUT REQUIREMENTS:
                1. 🍎 **7-Day Meal Plan**: Specific meals (Breakfast, Lunch, Dinner, Snack) based on {culture} habits and {budget} budget.
                2. 💪 **Workout Plan**: A routine tailored to {goal}, respecting {medical}.
                3. 🛒 **Shopping List**: Categorized and budget-friendly.
                4. 💡 **Pro-Tips**: 3 tips for consistency and time-saving for students.
                
                Format clearly with Markdown and bold headings.
                Finally, provide a 'MACRONUTRIENT RATIO' section in exactly this format:
                PROTEIN: [number]%
                CARBS: [number]%
                FATS: [number]%
                """

                try:
                    # 2. Call the real Gemini Model
                    response = model.generate_content(prompt)
                    st.session_state.plan = response.text
                except Exception as e:
                    st.error(f"AI Error: {e}")
        
        if st.session_state.plan:
            full_text = st.session_state.plan
            # Split the text so we don't show the raw "PROTEIN: XX%" lines to the user
            if "MACRONUTRIENT RATIO" in full_text:
                plan_to_show = full_text.split("MACRONUTRIENT RATIO")[0]
                macro_data = full_text.split("MACRONUTRIENT RATIO")[1]
            else:
                plan_to_show = full_text
                macro_data = ""

            st.markdown(plan_to_show)

            # --- GRAPH LOGIC ---
            if macro_data:
                p_val = int(macro_data.split("PROTEIN:")[1].split("%")[0].strip())
                c_val = int(macro_data.split("CARBS:")[1].split("%")[0].strip())
                f_val = int(macro_data.split("FATS:")[1].split("%")[0].strip())

                st.markdown("### 📊 Your Daily Macro Target")
                chart_data = pd.DataFrame({
                    "Nutrient": ["Protein", "Carbs", "Fats"],
                    "Percentage": [p_val, c_val, f_val]
                })
                st.bar_chart(chart_data.set_index("Nutrient"), color="#4f8bf9")
                st.success("Plan Generated Successfully!")

            # 4. Update the Download Button with real data
            downloadable_text = full_text.replace("### ", "--- ").replace("**", "") # Clean the text for better readability in the .txt file
            st.download_button(
                label="📥 Download My Plan (.txt)",
                data=downloadable_text, # Use the cleaned text here
                file_name="my_fitness_plan.txt",
                mime="text/plain",
                use_container_width=True
            )
with tab2:
    st.header("🥗 AI Food & Nutrition Scanner")
    st.write("Upload a photo of your meal for an instant nutritional breakdown.")
    
    food_file = st.file_uploader("Upload meal photo...", type=["jpg", "jpeg", "png"], key="food_upload")
    
    # Update session state image if a new one is uploaded
    if food_file:
        st.session_state.food_image = Image.open(food_file)
    
    # Layout: Image on left, Results on right
    col_img, col_res = st.columns([1, 1])
    
    with col_img:
        if st.session_state.food_image:
            st.image(st.session_state.food_image, caption="Current Meal", use_container_width=True)
            if st.button("Analyze Nutrition", type="primary", use_container_width=True):
                with st.spinner("Calculating macros..."):
                    try:
                        prompt = f"""
                            Act as a certified nutritionist and AI vision expert. 
                            Analyze the provided image of the meal and cross-reference it with the user's health profile:
                            {st.session_state.health_profile}

                            YOUR TASK:
                            1. IDENTIFY: List every food item and estimated portion size from the image.
                            2. SCIENCE-BACKED BREAKDOWN: Provide a table with Calories, Protein, Carbs, and Fats.
                            3. PERSONALIZED INSIGHTS: How does this specific meal affect the user's current goal or medical conditions?
                            4. RECOMMENDATIONS: Suggest one "Practical Swap" to improve the nutrient density of this specific plate.
                            5. PRECAUTIONS: Highlight any ingredients visible that might conflict with the user's dietary restrictions.

                            Maintain a professional yet supportive tone. Use Markdown for the table.
                            """
                        response = model.generate_content([prompt, st.session_state.food_image])
                        st.session_state.food_result = response.text
                        st.success("Nutrition Analysis Generated Successfully!")
                    except Exception as e:
                        st.error(f"AI Error: {e}")

    with col_res:
        if st.session_state.food_result:
            st.markdown("### 📊 Nutritional Analysis")
            st.markdown(st.session_state.food_result)
            if st.session_state.food_result:
                        st.download_button(
                            label="📥 Save Nutrition Analysis",
                            data=st.session_state.food_result,
                            file_name="meal_analysis.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
        elif st.session_state.food_image:
            st.info("Click 'Analyze Nutrition' to see results.")

    # --- TAB 3: ROOM/GYM ANALYZER ---
with tab3:
    st.header("🏋️ Room & Space Analyzer")
    st.write("Upload a photo of your room or gym to get a personalized workout plan.")
    
    room_file = st.file_uploader("Upload space photo...", type=["jpg", "jpeg", "png"], key="room_upload")
    
    if room_file:
        st.session_state.room_image = Image.open(room_file)
        
    col_img_room, col_res_room = st.columns([1, 1])
    
    with col_img_room:
        if st.session_state.room_image:
            st.image(st.session_state.room_image, caption="Your Workout Space", use_container_width=True)
            if st.button("Find My Workout", type="primary", use_container_width=True):
                with st.spinner("Analyzing space..."):
                    try:
                        prompt = f"""
                            Act as a certified Fitness Coach and Biomechanics Expert. 
                            Analyze the provided image of the user's environment and cross-reference it with their health profile:
                            {st.session_state.health_profile}

                            YOUR TASK:
                            1. ENVIRONMENT AUDIT: Identify all usable fitness equipment OR household furniture (e.g., chairs, wall space, sturdy elevated surfaces) visible in the image.
                            2. CUSTOM CIRCUIT: Design a 15-minute workout circuit tailored to the user's goal. For each exercise, specify which object from the photo to use.
                            3. BIOMECHANICAL ADVANTAGE: Briefly explain why these specific objects are safe and effective for the recommended movements.
                            4. PROGRESSION TIP: Suggest one way to make the workout harder once they master the current routine.
                            5. SAFETY PRECAUTIONS: Highlight any potential hazards in the photo (e.g., slippery floors, unstable furniture) and provide a safety warning based on their medical history.

                            Maintain an encouraging and professional tone. Use Markdown for the workout structure.
                            """
                        response = model.generate_content([prompt, st.session_state.room_image])
                        st.session_state.room_result = response.text
                        st.success("Custom Workout Plan Generated Successfully!")
                    except Exception as e:
                        st.error(f"AI Error: {e}")

    with col_res_room:
        if st.session_state.room_result:
            st.markdown("### 🏠 Custom Workout Plan")
            st.markdown(st.session_state.room_result)
            if st.session_state.room_result:
                        st.download_button(
                            label="📥 Save Custom Workout",
                            data=st.session_state.room_result,
                            file_name="room_workout.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
        elif st.session_state.room_image:
            st.info("Click 'Find My Workout' to see results.")