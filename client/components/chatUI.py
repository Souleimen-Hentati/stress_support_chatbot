import streamlit as st
from utils.api import ask_question, ask_question_rag_compare
from datetime import datetime


def render_chat_ui():
    """
    Main chat interface function that creates the chatbot UI in Streamlit.
    Manages chat history, message display, and user interactions.
    """
    st.subheader("💬 Stress Support Chat")

    # Initialize session state for chat management
    # Session state persists data across Streamlit reruns (every user interaction)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}  # Dictionary: {chat_id: [list of messages]}
        st.session_state.current_chat_id = None  # Tracks which chat is currently active
        st.session_state.chat_counter = 0  # Counter to generate unique chat IDs

    # =========================
    # SIDEBAR: CHAT MANAGEMENT
    # =========================
    with st.sidebar:
        chat_mode = st.radio(
            "Response mode",
            ["Standard", "RAG Strategy Compare"],
            help="Standard returns one answer. Compare runs RAG chain and RAG agent side by side.",
        )
        st.markdown("---")
        st.subheader("📋 Chat History")
        
        # NEW CHAT BUTTON - Creates a fresh conversation
        # When clicked:
        # 1. Increments chat_counter to generate unique ID (chat_1, chat_2, etc)
        # 2. Creates new empty message list for this chat
        # 3. Sets it as the current active chat
        # 4. st.rerun() refreshes the app UI to show empty chat
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.chat_counter += 1
            chat_id = f"chat_{st.session_state.chat_counter}"
            st.session_state.current_chat_id = chat_id
            st.session_state.chat_history[chat_id] = []
            st.rerun()
        
        # AUTO-CREATE DEFAULT CHAT
        # If this is first visit (no current_chat_id), automatically create a default chat
        # This prevents showing empty UI to new users
        if st.session_state.current_chat_id is None:
            st.session_state.chat_counter += 1
            chat_id = f"chat_{st.session_state.chat_counter}"
            st.session_state.current_chat_id = chat_id
            st.session_state.chat_history[chat_id] = []
        
        # DISPLAY PREVIOUS CHATS
        # Shows all past conversations in sidebar with:
        # - Preview of first message (max 30 chars)
        # - Click button to switch to that chat
        # - Delete button to remove that chat
        if st.session_state.chat_history:
            st.write("**Previous Chats:**")
            # reversed() shows newest chats at top, oldest at bottom
            for chat_id in reversed(list(st.session_state.chat_history.keys())):
                messages = st.session_state.chat_history[chat_id]
                if messages:
                    # Get first message and use first 30 chars as preview
                    # .replace('\n', ' ') removes line breaks from preview
                    preview = messages[0]["content"][:30].replace('\n', ' ') + "..."
                    is_current = chat_id == st.session_state.current_chat_id
                    
                    # Create two columns: wider one for chat preview, narrow one for delete button
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        # Click this button to switch to the chat (sets it as current_chat_id)
                        if st.button(f"🔹 {preview}", use_container_width=True, key=f"chat_{chat_id}"):
                            st.session_state.current_chat_id = chat_id
                            st.rerun()
                    
                    with col2:
                        # Delete button - removes this chat from history
                        if st.button("🗑️", key=f"delete_{chat_id}"):
                            del st.session_state.chat_history[chat_id]
                            # If we deleted the current chat, switch to last available chat
                            if st.session_state.current_chat_id == chat_id:
                                chats = list(st.session_state.chat_history.keys())
                                st.session_state.current_chat_id = chats[-1] if chats else None
                            st.rerun()
    
    # =========================
    # MAIN CHAT AREA
    # =========================
    # Get all messages from the currently active chat
    # If no chat exists, return empty list as default
    current_messages = st.session_state.chat_history.get(st.session_state.current_chat_id, [])
    
    # DISPLAY EXISTING MESSAGES
    # Loop through all messages in current chat and render them as chat bubbles
    # st.chat_message() handles formatting:
    # - User messages: right-aligned, blue background
    # - Assistant messages: left-aligned, gray background
    for message in current_messages:
        st.chat_message(message["role"]).markdown(message["content"])
        if message["role"] == "assistant" and message.get("sources"):
            with st.expander("Sources", expanded=False):
                for src in message["sources"]:
                    source = src.get("source", "unknown")
                    page = src.get("page")
                    if page is None:
                        st.markdown(f"- `{source}`")
                    else:
                        st.markdown(f"- `{source}` (page {page})")
    
    # =========================
    # USER INPUT & RESPONSE HANDLING
    # =========================
    # Create chat input box at bottom of screen
    # Returns None if empty, returns user's text when they press Enter
    user_input = st.chat_input("Share what feels stressful right now...")
    
    if user_input:
        # IMMEDIATELY DISPLAY USER MESSAGE
        # Shows user's message as chat bubble right away (good UX)
        st.chat_message("user").markdown(user_input)
        # Add message to current chat history
        current_messages.append({"role": "user", "content": user_input})
        
        # SEND TO BACKEND
        # Show loading spinner while waiting for API response
        # Spinner text explains what's happening: "Searching medical documents..."
        with st.spinner("🫶 Preparing supportive response..."):
            try:
                if chat_mode == "RAG Strategy Compare":
                    response = ask_question_rag_compare(user_input)
                else:
                    # Call API function from utils/api.py that makes HTTP POST to backend
                    # Sends: POST /ask_questions with question parameter
                    response = ask_question(user_input)
            except Exception as e:
                # If backend is unreachable or crashes, show error and stop
                st.error(f"❌ Backend unavailable: {e}")
                return
        
        # PROCESS BOT RESPONSE
        # Check if API call was successful (HTTP 200 = OK)
        if response.status_code == 200:
            # Parse JSON response from backend
            # Backend returns: {"response": "bot's answer here", "sources": [...]}
            data = response.json()
            sources = data.get("sources", [])

            if chat_mode == "RAG Strategy Compare":
                results = data.get("results", [])
                mode = data.get("mode", "rag-strategy-compare")

                if not results:
                    st.error("❌ No comparison results returned by backend.")
                    return

                # Build a compact text version to keep history export compatible.
                answer_parts = [f"Mode: {mode}", ""]
                for item in results:
                    strategy = item.get("strategy", "unknown")
                    if item.get("error"):
                        answer_parts.append(f"[{strategy}] ERROR: {item['error']}")
                    else:
                        answer_parts.append(f"[{strategy}] {item.get('response', '')}")
                        strategy_sources = item.get("sources", [])
                        if strategy_sources:
                            answer_parts.append("Sources:")
                            for src in strategy_sources:
                                source = src.get("source", "unknown")
                                page = src.get("page")
                                if page is None:
                                    answer_parts.append(f"- {source}")
                                else:
                                    answer_parts.append(f"- {source} (page {page})")
                    answer_parts.append("")

                combined_answer = "\n".join(answer_parts).strip()

                st.chat_message("assistant").markdown("### Strategy Comparison")
                columns = st.columns(2)
                for idx, item in enumerate(results[:2]):
                    with columns[idx]:
                        strategy = item.get("strategy", "unknown")
                        st.markdown(f"**{strategy}**")
                        if item.get("error"):
                            st.error(item["error"])
                        else:
                            st.markdown(item.get("response", ""))
                            strategy_sources = item.get("sources", [])
                            if strategy_sources:
                                with st.expander(f"Sources ({strategy})", expanded=False):
                                    for src in strategy_sources:
                                        source = src.get("source", "unknown")
                                        page = src.get("page")
                                        if page is None:
                                            st.markdown(f"- `{source}`")
                                        else:
                                            st.markdown(f"- `{source}` (page {page})")

                current_messages.append(
                    {
                        "role": "assistant",
                        "content": combined_answer,
                        "sources": [],
                    }
                )
                st.session_state.chat_history[st.session_state.current_chat_id] = current_messages
                return

            answer = data["response"]
            
            # DISPLAY ASSISTANT MESSAGE
            # Show bot's response as chat bubble
            st.chat_message("assistant").markdown(answer)
            if sources:
                with st.expander("Sources", expanded=False):
                    for src in sources:
                        source = src.get("source", "unknown")
                        page = src.get("page")
                        if page is None:
                            st.markdown(f"- `{source}`")
                        else:
                            st.markdown(f"- `{source}` (page {page})")
            # Add to message history
            current_messages.append({"role": "assistant", "content": answer, "sources": sources})
            
            # SAVE CHAT HISTORY
            # Update the session state so messages persist during this session
            st.session_state.chat_history[st.session_state.current_chat_id] = current_messages
        else:
            # If API returned error (not 200), show error message
            st.error(f"❌ Error: {response.text}")