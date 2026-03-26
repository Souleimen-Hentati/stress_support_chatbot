import streamlit as st
from utils.api import ask_question, ask_question_rag_compare
from datetime import datetime


def render_chat_ui():
    
    st.subheader("💬 Stress Support Chat")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {} 
        st.session_state.current_chat_id = None 
        st.session_state.chat_counter = 0 

    with st.sidebar:
        chat_mode = st.radio(
            "Response mode",
            ["Standard", "RAG Strategy Compare"],
            help="Standard returns one answer. Compare runs RAG chain and RAG agent side by side.",
        )
        st.markdown("---")
        st.subheader("📋 Chat History")
        
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.chat_counter += 1
            chat_id = f"chat_{st.session_state.chat_counter}"
            st.session_state.current_chat_id = chat_id
            st.session_state.chat_history[chat_id] = []
            st.rerun()
        
        if st.session_state.current_chat_id is None:
            st.session_state.chat_counter += 1
            chat_id = f"chat_{st.session_state.chat_counter}"
            st.session_state.current_chat_id = chat_id
            st.session_state.chat_history[chat_id] = []
      
        if st.session_state.chat_history:
            st.write("**Previous Chats:**")
            for chat_id in reversed(list(st.session_state.chat_history.keys())):
                messages = st.session_state.chat_history[chat_id]
                if messages:
                    preview = messages[0]["content"][:30].replace('\n', ' ') + "..."
                    is_current = chat_id == st.session_state.current_chat_id
                    
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if st.button(f"🔹 {preview}", use_container_width=True, key=f"chat_{chat_id}"):
                            st.session_state.current_chat_id = chat_id
                            st.rerun()
                    
                    with col2:
                        if st.button("🗑️", key=f"delete_{chat_id}"):
                            del st.session_state.chat_history[chat_id]
                            if st.session_state.current_chat_id == chat_id:
                                chats = list(st.session_state.chat_history.keys())
                                st.session_state.current_chat_id = chats[-1] if chats else None
                            st.rerun()
    
    current_messages = st.session_state.chat_history.get(st.session_state.current_chat_id, [])
  
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
    
    user_input = st.chat_input("Share what feels stressful right now...")
    
    if user_input:
        st.chat_message("user").markdown(user_input)
        current_messages.append({"role": "user", "content": user_input})
        
        with st.spinner("🫶 Preparing supportive response..."):
            try:
                if chat_mode == "RAG Strategy Compare":
                    response = ask_question_rag_compare(user_input)
                else:
                    response = ask_question(user_input)
            except Exception as e:
                st.error(f"❌ Backend unavailable: {e}")
                return
                
        if response.status_code == 200:
            data = response.json()
            sources = data.get("sources", [])

            if chat_mode == "RAG Strategy Compare":
                results = data.get("results", [])
                mode = data.get("mode", "rag-strategy-compare")

                if not results:
                    st.error("❌ No comparison results returned by backend.")
                    return

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
            current_messages.append({"role": "assistant", "content": answer, "sources": sources})
            
            st.session_state.chat_history[st.session_state.current_chat_id] = current_messages
        else:
            st.error(f"❌ Error: {response.text}")
