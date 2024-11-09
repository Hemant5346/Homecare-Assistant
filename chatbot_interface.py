import streamlit as st
import os
from chat_with_gpt import chat_with_gpt
from langchain.chains import ConversationalRetrievalChain
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
    """Return specialized prompts and trigger words for each bot type"""
    
    bot_configs = {
        "Plumbing and Water Systems": {
            "prompt": "Please analyze this image of the plumbing system or water-related issue. Identify any visible problems, leaks, or maintenance concerns. Provide specific recommendations for repairs or maintenance.",
            "triggers": ['leak', 'pipe', 'water', 'drain', 'faucet', 'toilet', 'sink', 'plumbing'],
            "upload_message": "Please upload an image of the plumbing issue to help me better assist you."
        },
        "HVAC (Heating, Ventilation, and Air Conditioning)": {
            "prompt": "Please analyze this image of the HVAC system or component. Identify any visible issues, maintenance needs, or potential problems. Provide specific recommendations for optimization or repairs.",
            "triggers": ['ac', 'heat', 'ventilation', 'cooling', 'furnace', 'thermostat', 'filter', 'duct'],
            "upload_message": "Please upload an image of your HVAC system or component to help me better assist you."
        },
        "Appliance Maintenance and Repairs": {
            "prompt": "Please analyze this image of the appliance. Identify any visible issues, error indicators, or maintenance needs. Provide specific recommendations for repairs or maintenance.",
            "triggers": ['washer', 'dryer', 'dishwasher', 'refrigerator', 'oven', 'microwave', 'appliance', 'machine'],
            "upload_message": "Please upload an image of your appliance to help me better assist you."
        },
        "Pest and Bug Control": {
            "prompt": "Please analyze this image and identify any pest or bug issues. Describe what you see and provide relevant recommendations for treatment or control.",
            "triggers": ['bug', 'pest', 'insect', 'rodent', 'creature', 'ant', 'spider', 'mouse'],
            "upload_message": "Please upload an image of the pest or bug to help me better assist you."
        },
        "Roofing, Gutter, and Exterior Maintenance": {
            "prompt": "Please analyze this image of the roof, gutter, or exterior issue. Identify any visible damage, maintenance needs, or potential problems. Provide specific recommendations for repairs or maintenance.",
            "triggers": ['roof', 'gutter', 'leak', 'shingle', 'exterior', 'siding', 'damage', 'crack'],
            "upload_message": "Please upload an image of the exterior issue to help me better assist you."
        }
    }
    
    return bot_configs.get(bot_type, {
        "prompt": "Please analyze this image and provide relevant recommendations.",
        "triggers": ['issue', 'problem', 'help'],
        "upload_message": "Please upload an image to help me better assist you."
    })

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

    # Initialize session states
    if 'waiting_for_image' not in st.session_state:
        st.session_state.waiting_for_image = False
    
    # Get bot-specific configuration
    bot_config = get_image_prompt_and_triggers(bot_type)
    
    # Initialize OpenAI client
    client = get_openai_client()

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    message_count = len(st.session_state.messages) // 2

    # Handle image upload state
    if st.session_state.waiting_for_image:
        st.info(bot_config["upload_message"])
        uploaded_image = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])
        
        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
            
            with st.spinner("Analyzing the image..."):
                analysis_result = analyze_image_with_openai(uploaded_image, bot_type)
                
                # Add the analysis to the chat
                st.chat_message("assistant").markdown(analysis_result)
                st.session_state.messages.append({"role": "assistant", "content": analysis_result})
                
                # Reset the waiting flag
                st.session_state.waiting_for_image = False
                st.rerun()

    if message_count >= MAX_MESSAGES:
        st.warning(f"You have reached the maximum limit of {MAX_MESSAGES} messages. Please start a new session.")
    else:
        prompt = st.chat_input(f"Ask {bot_type} a question", key="chat_input")
        if prompt:
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.spinner(f"The {bot_type} is thinking..."):
                # Check if any trigger words are in the prompt
                if any(word in prompt.lower() for word in bot_config["triggers"]):
                    response = f"To better assist you with this {bot_type.lower()} issue, could you please provide a picture? This will help me provide more specific advice."
                    st.session_state.waiting_for_image = True
                else:
                    response = chat_with_gpt(client, prompt, st.session_state.messages, bot_type=bot_type)
                
                st.chat_message("assistant").markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

            if st.session_state.waiting_for_image:
                st.rerun()

    st.sidebar.write(f"Message Count: {message_count}/{MAX_MESSAGES}")

    if st.sidebar.button("Start New Session"):
        st.session_state.messages = []
        st.session_state.selected_bot = None
        st.session_state.waiting_for_image = False
        st.rerun()