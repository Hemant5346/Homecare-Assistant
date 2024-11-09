import streamlit as st
import os
from chat_with_gpt import chat_with_gpt
from langchain_community.chat_models import ChatOpenAI
from config import MAX_HISTORY, MAX_MESSAGES
from PIL import Image
import base64
from openai import OpenAI

@st.cache_resource
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return OpenAI(api_key=api_key)
    return None

def encode_image_to_base64(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def get_image_prompt_and_triggers(bot_type):
    bot_configs = {
        "Plumbing and Water Systems": {
            "prompt": "Please analyze this image of the plumbing system or water-related issue. Identify any visible problems, leaks, or maintenance concerns. Provide specific recommendations for repairs or maintenance."
        },
        "HVAC (Heating, Ventilation, and Air Conditioning)": {
            "prompt": "Please analyze this image of the HVAC system or component. Identify any visible issues, maintenance needs, or potential problems. Provide specific recommendations for optimization or repairs."
        },
        "Appliance Maintenance and Repairs": {
            "prompt": "Please analyze this image of the appliance. Identify any visible issues, error indicators, or maintenance needs. Provide specific recommendations for repairs or maintenance."
        },
        "Pest and Bug Control": {
            "prompt": "Please analyze this image and identify any pest or bug issues. Describe what you see and provide relevant recommendations for treatment or control."
        },
        "Roofing, Gutter, and Exterior Maintenance": {
            "prompt": "Please analyze this image of the roof, gutter, or exterior issue. Identify any visible damage, maintenance needs, or potential problems. Provide specific recommendations for repairs or maintenance."
        }
    }
    return bot_configs.get(bot_type, {"prompt": "Please analyze this image and provide relevant recommendations."})

def analyze_image_with_openai(image, bot_type):
    client = get_openai_client()
    try:
        base64_image = encode_image_to_base64(image)
        bot_config = get_image_prompt_and_triggers(bot_type)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": bot_config["prompt"]
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

def chatbot_interface(bot_type):
    st.header(f"{bot_type} Chatbot")

    # Initialize OpenAI client
    client = get_openai_client()

    # Initialize session state for messages and image analysis
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'image_analyzed' not in st.session_state:
        st.session_state.image_analyzed = False

    # Create columns for layout: one for the chat and one for the image
    col1, col2 = st.columns([3, 1])

    # Image upload section (fixed in the right column)
    with col2:
        st.subheader("Upload an Image for Analysis")
        uploaded_image = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])
        
        if uploaded_image and not st.session_state.image_analyzed:
            st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
        
            with st.spinner("Analyzing the image..."):
                analysis_result = analyze_image_with_openai(uploaded_image, bot_type)
                st.session_state.messages.append({"role": "assistant", "content": analysis_result})
                st.session_state.image_analyzed = True

    # Chat section (left column)
    with col1:
        # Create a container for the chat
        chat_container = st.container()
        
        # Display message count and input box
        message_count = len(st.session_state.messages) // 2
        st.sidebar.write(f"Message Count: {message_count}/{MAX_MESSAGES}")

        # Input area at the bottom
        if message_count >= MAX_MESSAGES:
            st.warning(f"You have reached the maximum limit of {MAX_MESSAGES} messages. Please start a new session.")
        else:
            prompt = st.chat_input(f"Ask {bot_type} a question", key="chat_input")
            if prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                with st.spinner(f"The {bot_type} is thinking..."):
                    response = chat_with_gpt(client, prompt, st.session_state.messages, bot_type=bot_type)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()  # Rerun to update the chat display

        # Display messages in the correct order (oldest to newest)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

    # Add reset button to clear the image and chat history
    if st.sidebar.button("Start New Session"):
        st.session_state.messages = []
        st.session_state.image_analyzed = False
        st.session_state.selected_bot = None
        st.rerun()