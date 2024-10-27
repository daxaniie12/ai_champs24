import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import requests
from bs4 import BeautifulSoup
import re
from utility import check_password

load_dotenv()

hide_github_icon = """
#GithubIcon {
  visibility: hidden;
}
"""
st.markdown(hide_github_icon, unsafe_allow_html=True)


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "suggestions" not in st.session_state:
    st.session_state.suggestions = [
        "What is the purpose of CPF?",
        "Can you use your CPF for investments?",
        "How does CPF helps in your retirement?",
    ]

# Streamlit Page Configuration
st.set_page_config(page_title="CPF Q&A Bot", page_icon=":robot_face:")

# Do not continue if check_password is not True.
if not check_password():
    st.stop()

# Add the disclaimer using st.expander
with st.expander("IMPORTANT NOTICE"):
    st.write("""
    **IMPORTANT NOTICE:** This web application is a prototype developed for educational purposes only.
    The information provided here is **NOT** intended for real-world usage and should not be relied upon for making any decisions,
    especially those related to financial, legal, or healthcare matters.

    Furthermore, please be aware that the LLM may generate inaccurate or incorrect information.
    You assume full responsibility for how you use any generated output.

    **Always consult with qualified professionals** for accurate and personalized advice.
    """)

# Create a navigation menu with pages
page = st.sidebar.selectbox("Navigation", ["Chat", "About This App", "Methodology"])

# Function to load content from the specified website
def load_website_content():
    url = "https://blog.seedly.sg/about-central-provident-fund-cpf/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        content = [p.get_text() for p in soup.find_all('p')]
        return ' '.join(content)
    except Exception as e:
        st.error(f"Error loading website content: {str(e)}")
        return None

st.session_state.content_data = load_website_content()

bto_keywords = ["CPF", "Central Provident Fund", "interest rate", "contributions", "retirement", "payout", "Ordinary Account",
"Special Account", "Medisave", "Retirement Account"]

def classify_topic(user_input, website_content):
    user_input_lower = user_input.lower()
    if any(keyword in user_input_lower for keyword in bto_keywords):
        return "CPF_RELATED"
    # The rest of your classification logic


    prompt = f"""
    Classify the following user input as either 'CPF_RELATED' or 'OFF_TOPIC':
    
    User Input: {user_input}
    
    If the input is related to Singapore's CPF (Central Provident Fund), Ordinary Account (OA), Special Account (SA), Medisave Account (MA), Retirement Account (RA), using CPF for investment or any aspect of CPF, classify it as 'CPF_RELATED'.
    Otherwise, classify it as 'OFF_TOPIC'."""
    
    classification = get_completion(prompt).strip()
    return classification


def classify_granular_topic(user_input, website_content):
    user_input_lower = user_input.lower()


    prompt = f"""
    Classify the following user input into different CPF topics such as CPF for housing, CPF for retirement, CPF for hospitalisation, CPF for family planning , CPF for investment etc:
    
    User Input: {user_input}
    
    """
    
    classification = get_completion(prompt).strip()
    return classification


# Access the OpenAI API key
openai_api_key = st.secrets["general"]["OPENAI_API_KEY"]


def sanitize_input(user_input):
    sanitized = re.sub(r'ignore .* prompt', '', user_input, flags=re.IGNORECASE)
    sanitized = re.sub(r'forget .* instruction', '', sanitized, flags=re.IGNORECASE)
    return sanitized

def get_completion(prompt):
    llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-4o-mini", temperature=0)
    response = llm.invoke(prompt)
    return response.content

def get_response(user_input, chat_history, website_content):
    sanitized_input = sanitize_input(user_input)
    topic_classification = classify_topic(sanitized_input, website_content)
    
    # This is the additional message with the link
    additional_info_message = """
    For more detailed information on CPF and related topics, please visit the official CPF website: [CPF Official Website](https://www.cpf.gov.sg/member).
    """
    
    if topic_classification == 'CPF_RELATED':
        prompt = f"""
        You are an AI assistant specialized in Singapore's CPF (Central Provident Fund).
        Your role is to provide accurate and helpful information about CPF, CPF accounts such as Ordinary Account (OA), Special Account (SA), Retirement Account (RA) using CPF for investments, and related topics.

        Here's some context information from the article:
        {website_content}

        Previous conversation:
        {' '.join([msg.content for msg in chat_history])}

        Respond to the following user query about CPF:
        {sanitized_input}

        Your response should follow this structure:
        1. Direct answer to the query (3-4 sentences)
        2. Additional relevant information (4-5 sentences, over 2 paragraphs. use bullet points if it's easier to understand)
        3. {additional_info_message}
        """
    else:
        prompt = f"""
        You are an AI assistant specialized in Singapore's CPF (Central Provident Fund).
        The user has asked a question that is not related to CPF.

        User query: {sanitized_input}

        Respond with the following structure:
        1. Polite acknowledgment that the query is not about CPF
        2. Brief explanation of what CPF is
        3. Suggestion for a CPF-related question the user could ask instead
        4. {additional_info_message}
        """
    
    return get_completion(prompt)


if "current_topic" not in st.session_state:
    st.session_state.current_topic = None

def generate_new_suggestions(current_topic):
    prompt = f"""
    <Instruction>
    Based on the current topic of conversation: "{current_topic}"
    Generate 3 relevant follow-up questions or prompts that a user might want to ask next.
    </Instruction>

    Create 3 concise and diverse questions or prompts related to the topic above.
    These should cover different aspects of the topic and encourage further exploration.

    Remember, you are generating questions about CPF.

    Format your response as a Python list of strings, of the 3 different questions. Only return the list.
    E.g. of a response: ["What is the purpose of CPF?","Can you use your CPF for investments?","How does CPF helps in your retirement?"]
    """
    
    try:
        response = get_completion(prompt)
        return eval(response)
    except:
        return [
            "What is the purpose of CPF?",
            "Can you use your CPF for investments?",
            "How does CPF helps in your retirement?"
        ]

# Page Logic
if page == "Chat":
    st.title("Ask Me Anything About CPF Bot")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message("Human" if isinstance(message, HumanMessage) else "AI"):
            st.markdown(message.content)

    # Display clickable suggestions
    st.write("Suggested questions:")
    clicked_suggestion = None
    for suggestion in st.session_state.suggestions:
        if st.button(suggestion):
            clicked_suggestion = suggestion  # Store the clicked suggestion

    # Process either the clicked suggestion or user input from chat box
    if clicked_suggestion:
        user_input = clicked_suggestion
    else:
        user_input = st.chat_input("Your message")

    if user_input:
        sanitized_input = sanitize_input(user_input)
        
        # Classify the topic to decide if suggestions need updating
        topic_classification = classify_granular_topic(sanitized_input, st.session_state.content_data)

        # Update suggestions only if the topic changes
        if topic_classification != st.session_state.current_topic:
            st.session_state.suggestions = generate_new_suggestions(sanitized_input)
            st.session_state.current_topic = topic_classification

        st.session_state.chat_history.append(HumanMessage(sanitized_input))

        with st.chat_message("Human"):
            st.markdown(sanitized_input)

        with st.chat_message("AI"):
            ai_response = get_response(sanitized_input, st.session_state.chat_history, st.session_state.content_data)
            st.markdown(ai_response)
        
        st.session_state.chat_history.append(AIMessage(ai_response))

        # Trigger rerun to refresh interface with new suggestions if topic changed
        st.rerun()



elif page == "About This App":
    st.title("About This App")
    st.write("""
    ### Project Scope:
    This project provides a web-based FAQ chatbot that allows users to ask questions about Singapore CPF policies 
    
    ### Objectives:
    - Deliver up-to-date information regarding CPF policies, how does it works and what it can be used for like retirement, home purchase and other financing knowledge.
    - Offer proposals on how to better use your CPF funds
    - Enable interactive conversations with users to understand more about CPF
    
    ### Data Sources:
    The data source is abstracted from the Official CPF website
    
    ### Features:
    - Facilitate interactive conversations where users can ask questions and receive responses tailored to their inquiries about CPF
    - Scrape relevant content from an official CPF website to provide detailed answers to user queries.
    - Generate suggestions for follow-up questions based on the user's current topic of inquiry
    """)

elif page == "Methodology":
    st.title("Methodology")
    st.write("""
    The methodology of this app application includes several steps:
    1.  Using web scraping methods to obtain information from official CPF website
    2.  Using Natural Language Processing to comprehend user questions and deliver relevant answers.
    3.  Creating an intuitive interface to enhance conversation and facilitate information access.
    4.  Regularly assessing the assistant’s performance and making continuous improvements based on user feedback.

    Please see the flow chart below.

    """)
    
    st.image("flowchart.png")  # Replace with the path to your flowchart image
