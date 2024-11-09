import time
from dotenv import load_dotenv, find_dotenv
import streamlit as st
from chatbot_interface import chatbot_interface
from PIL import Image

# Load environment variables
load_dotenv(find_dotenv(".env"))

def main():
    st.set_page_config(page_title="Multi-Chatbot Application", layout="wide")

    # Load and display the logo
    logo = Image.open("logo.jpg")

    st.markdown("""
    <style>
    .logo-img {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #ffffff;
        box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
    }
    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
        height: 100px;
        font-size: 24px;
        margin-bottom: 20px;
    }
    .stHeader {
        font-size: 40px;
        font-weight: bold;
        margin-bottom: 30px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # Display the logo in a circular design
    st.markdown('<div class="logo-container"><img src="data:image/png;base64,{}" class="logo-img"></div>'.format(image_to_base64(logo)), unsafe_allow_html=True)

    if 'selected_bot' not in st.session_state:
        st.session_state.selected_bot = None

    if st.session_state.selected_bot is None:
        st.markdown("<h1 class='stHeader'>Choose Your Chatbot</h1>", unsafe_allow_html=True)
        col1, col2 ,col3, col4,col5= st.columns(5)
        
        with col1:
            if st.button("Plumbing and Water Systems"):
                st.session_state.selected_bot = "Plumbing and Water Systems"
                st.rerun()
        
        with col2:
            if st.button("HVAC (Heating, Ventilation, and Air Conditioning)"):
                st.session_state.selected_bot = "HVAC (Heating, Ventilation, and Air Conditioning)"
                st.rerun()
        with col3:
            if st.button("Appliance Maintenance and Repairs"):
                st.session_state.selected_bot = "Appliance Maintenance and Repairs"
                st.rerun()
        with col4:
            if st.button("Pest and Bug Control"):
                st.session_state.selected_bot = "Pest and Bug Control"
                st.rerun()
        with col5:
            if st.button("Roofing, Gutter, and Exterior Maintenance"):
                st.session_state.selected_bot = "Roofing, Gutter, and Exterior Maintenance"
                st.rerun()
        
    
    else:
        chatbot_interface(st.session_state.selected_bot)

    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"session-{int(time.time())}"

    if "messages" not in st.session_state:
        st.session_state.messages = []

def image_to_base64(image):
    import base64
    from io import BytesIO

    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

if __name__ == "__main__":
    main()