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

def analyze_image_with_openai(image):
    client = get_openai_client()
    try:
        # Convert the image to base64
        base64_image = encode_image_to_base64(image)
        
        # Create message with the image
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please analyze this image and identify any pest or bug issues. Describe what you see and provide relevant recommendations for treatment or control."
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
        
        # Extract the response content
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

def chatbot_interface(bot_type):
    st.header(f"{bot_type} Chatbot")

    # Initialize session state for image request flag if not exists
    if 'waiting_for_image' not in st.session_state:
        st.session_state.waiting_for_image = False
    
    # Initialize OpenAI client
    client = get_openai_client()

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    message_count = len(st.session_state.messages) // 2

    # Check if we're waiting for an image upload
    if st.session_state.waiting_for_image:
        st.info("Please upload an image of the bug or pest to help me better assist you.")
        uploaded_image = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])
        
        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
            
            with st.spinner("Analyzing the image..."):
                analysis_result = analyze_image_with_openai(uploaded_image)
                
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
                # For pest control related queries, trigger image upload
                if any(word in prompt.lower() for word in ['bug', 'pest', 'insect', 'rodent', 'creature']):
                    response = "To better assist you, could you please provide a picture of the bug or pest you're dealing with? This will help me identify the species and provide more specific advice for control and treatment."
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