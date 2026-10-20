
import os

import requests
import streamlit as st


API_URL = os.getenv("ATLAS_API_URL", "http://127.0.0.1:8000").rstrip("/")
SUPPORTED_TYPES = ["pdf", "docx", "txt", "md"]

st.set_page_config(
    page_title="Atlas RAG",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.2);
    }
    .brand {
        font-size: 1.8rem;
        font-weight: 750;
        letter-spacing: -0.06em;
    }
    .muted {
        color: #888;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "documents" not in st.session_state:
    st.session_state.documents = []

if "messages" not in st.session_state:
    st.session_state.messages = []


def error_message(response):
    try:
        detail = response.json().get("detail")
        if detail:
            return str(detail)
    except (ValueError, AttributeError):
        pass
    return f"Request failed with status {response.status_code}."


def check_backend():
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


# Sidebar
with st.sidebar:
    st.markdown('<div class="brand">◈ Atlas RAG</div>', unsafe_allow_html=True)
    st.caption("Your documents. Searchable knowledge.")

    st.divider()
    st.subheader("System status")

    if check_backend():
        st.success("API connected")
    else:
        st.error("API unavailable")
        st.caption("Start the FastAPI server on port 8000.")

    st.caption(f"API: {API_URL}")

    st.divider()
    st.subheader("Knowledge base")
    st.caption("Upload a document to make its contents searchable.")

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=SUPPORTED_TYPES,
        help="PDF, DOCX, TXT, or Markdown. Maximum size: 10 MB.",
    )

    if st.button(
        "Upload and process",
        type="primary",
        use_container_width=True,
        disabled=uploaded_file is None,
    ):
        try:
            with st.spinner("Processing document and creating embeddings..."):
                response = requests.post(
                    f"{API_URL}/documents/",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type or "application/octet-stream",
                        )
                    },
                    timeout=300,
                )

            if response.ok:
                document = response.json()

                # Avoid duplicate entries in the current session.
                st.session_state.documents = [
                    doc
                    for doc in st.session_state.documents
                    if doc["id"] != document["id"]
                ]
                st.session_state.documents.append(document)

                st.success(
                    f"Processed {document['filename']} "
                    f"({document['chunk_count']} chunks)."
                )
                st.rerun()
            else:
                st.error(error_message(response))

        except requests.RequestException as exc:
            st.error(f"Could not upload the document: {exc}")

    st.divider()
    st.subheader("Document scope")

    documents = st.session_state.documents
    document_options = [None] + [doc["id"] for doc in documents]
    document_lookup = {doc["id"]: doc for doc in documents}

    selected_document_id = st.selectbox(
        "Search in",
        options=document_options,
        format_func=lambda doc_id: (
            "All documents"
            if doc_id is None
            else document_lookup[doc_id]["filename"]
            + f" (ID: {doc_id})"
        ),
    )

    st.caption(f"{len(documents)} document(s) uploaded in this session.")

    if documents and st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# Main chat area
st.title("Ask your documents")
st.markdown(
    "Get answers from your knowledge base, with source passages "
    "to help you verify the results."
)

if not st.session_state.documents:
    st.info(
        "Start by uploading a PDF, DOCX, TXT, or Markdown document "
        "using the sidebar."
    )

# Render chat input before displaying the conversation.
prompt = st.chat_input(
    "Ask a question about your documents...",
    max_chars=2000,
)

if prompt:
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    try:
        with st.spinner("Searching documents and generating an answer..."):
            response = requests.post(
                f"{API_URL}/chat/",
                json={
                    "question": prompt,
                    "limit": 5,
                    "document_id": selected_document_id,
                },
                timeout=180,
            )

        if response.ok:
            result = response.json()
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result.get("answer", "No answer returned."),
                    "sources": result.get("sources", []),
                }
            )
        else:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"Request failed: {error_message(response)}",
                    "sources": [],
                }
            )

    except requests.Timeout:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "The request timed out. Please try again.",
                "sources": [],
            }
        )
    except requests.RequestException:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Could not reach the API. Check that the backend "
                    "is running and try again."
                ),
                "sources": [],
            }
        )

# Display conversation history.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        sources = message.get("sources", [])
        if sources:
            with st.expander(f"View sources ({len(sources)})"):
                for source in sources:
                    page = source.get("page_number")
                    page_label = f" · Page {page}" if page else ""

                    st.markdown(
                        f"**[{source.get('source_id', '?')}] "
                        f"{source.get('filename', 'Unknown document')}**"
                        f"{page_label}"
                    )

                    score = source.get("similarity_score")
                    if score is not None:
                        st.caption(f"Similarity score: {score:.4f}")

                    st.write(source.get("content", ""))
                    st.divider()

st.divider()
st.caption("Atlas RAG · Retrieval-augmented document question answering")
