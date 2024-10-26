import streamlit as st  
import hmac  

def check_password():  
    """Returns `True` if the user had the correct password."""  

    def password_entered():  
        """Checks whether a password entered by the user is correct."""  
        # Access the correct key in secrets
        try:
            # Ensure to use the correct path to the password key
            correct_password = st.secrets["general"]["password"]
            if hmac.compare_digest(st.session_state["password"], correct_password):  
                st.session_state["password_correct"] = True  
                del st.session_state["password"]  # Don't store the password.  
            else:  
                st.session_state["password_correct"] = False  
        except KeyError:
            st.error("Error: Password secret not found. Please check your secrets.toml.")
    
    # Return True if the password is validated.  
    if st.session_state.get("password_correct", False):  
        return True  
    
    # Show input for password.  
    st.text_input(  
        "Password", type="password", on_change=password_entered, key="password"  
    )  
    
    if "password_correct" in st.session_state:  
        st.error("😕 Password incorrect")  
    
    return False
