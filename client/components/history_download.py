import streamlit as st


def render_history_download():
    
    if st.session_state.get("chat_history"):
        current_chat_id = st.session_state.get("current_chat_id")
        
        if current_chat_id and st.session_state.chat_history.get(current_chat_id):
            messages = st.session_state.chat_history[current_chat_id]
            
            chat_text = "\n\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in messages])
            st.sidebar.markdown("---")
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                st.download_button(
                    "📥 Download Chat", 
                    chat_text,  
                    file_name=f"chat_history.txt",  
                    mime="text/plain",  
                    use_container_width=True  
                )
            
            with col2:
                if st.button("🧹 Clear Chat", use_container_width=True):
                    # Empty the messages list for current chat
                    st.session_state.chat_history[current_chat_id] = []
                    # st.rerun() refreshes the entire app, removing messages from display
                    st.rerun()
        
