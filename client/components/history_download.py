import streamlit as st


def render_history_download():
    """
    Renders download and clear buttons for the current chat conversation.
    Allows users to export chat history as a text file and clear the current chat.
    Only displays if there are active conversations in session state.
    """
    # CHECK IF CHAT HISTORY EXISTS
    # Only show download/clear buttons if user has created at least one chat
    if st.session_state.get("chat_history"):
        # Get the currently active chat ID
        current_chat_id = st.session_state.get("current_chat_id")
        
        # VERIFY CURRENT CHAT HAS MESSAGES
        # Make sure the current chat exists and has messages (not empty)
        if current_chat_id and st.session_state.chat_history.get(current_chat_id):
            # Get all messages from current chat
            messages = st.session_state.chat_history[current_chat_id]
            
            # FORMAT CHAT FOR EXPORT
            # Convert messages to readable text format:
            # "USER: Your question\n\nASSISTANT: Bot's answer\n\n..."
            # \n\n separates each message pair with blank lines for readability
            chat_text = "\n\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in messages])
            
            # ADD DIVIDER IN SIDEBAR
            st.sidebar.markdown("---")
            
            # CREATE TWO COLUMNS FOR BUTTONS
            # col1 for Download, col2 for Clear (50/50 split)
            col1, col2 = st.sidebar.columns(2)
            
            # DOWNLOAD BUTTON COLUMN
            with col1:
                # st.download_button creates a button that triggers file download
                # When clicked, browser downloads the chat_text as "chat_history.txt"
                st.download_button(
                    "📥 Download Chat",  # Button label with download icon
                    chat_text,  # Data to export
                    file_name=f"chat_history.txt",  # Downloaded filename
                    mime="text/plain",  # File type (plain text)
                    use_container_width=True  # Make button fill available width
                )
            
            # CLEAR CHAT BUTTON COLUMN
            with col2:
                # Clear button - wipes all messages from current chat
                if st.button("🧹 Clear Chat", use_container_width=True):
                    # Empty the messages list for current chat
                    st.session_state.chat_history[current_chat_id] = []
                    # st.rerun() refreshes the entire app, removing messages from display
                    st.rerun()
        