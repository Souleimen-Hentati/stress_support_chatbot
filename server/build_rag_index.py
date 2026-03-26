from modules.rag import build_rag_index

if __name__ == "__main__":
    success = build_rag_index()
    if success:
        print("RAG index build completed.")
    else:
        print("RAG index build skipped or failed. Add docs to uploaded_docs and retry.")
