import streamlit as st

from securdocs.database import initialize_user_database, verify_user_credentials

SAMPLE_QUESTIONS = [
    "What is the primary tech stack for our frontend and backend microservices?",
    "What were our primary growth metrics and marketing spend in Q1 2024?",
    "What are the statutory employee benefits and leave entitlement policies?",
    "What was the total revenue, gross margin, and net income for FY 2024?",
]

st.set_page_config(
    page_title="SecurDocs.AI", page_icon=":material/lock:", layout="wide"
)
initialize_user_database()


def render_login() -> None:
    st.title("SecurDocs.AI")
    st.caption("Sign in to access role-authorized company documents.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")

    if submitted:
        is_valid, role = verify_user_credentials(username.strip(), password.strip())
        if is_valid and role:
            st.session_state.user = {"username": username.strip(), "role": role}
            st.session_state.messages = []
            st.rerun()
        else:
            st.error("Invalid username or password.")


def render_chat() -> None:
    user = st.session_state.user

    with st.sidebar:
        st.title("SecurDocs.AI")
        st.caption("Role-authorized document assistant")
        st.subheader("Sample questions")
        for question_index, question in enumerate(SAMPLE_QUESTIONS):
            if st.button(
                question,
                key=f"sample_question_{question_index}",
                width="stretch",
            ):
                st.session_state.pending_prompt = question

        st.divider()
        st.markdown(f"**{user['username']}**  \nRole: `{user['role']}`")
        if st.button("Sign out", width="stretch"):
            for key in ("user", "messages", "pending_prompt"):
                st.session_state.pop(key, None)
            st.rerun()

    st.title("SecurDocs.AI Assistant")
    st.caption(
        "Ask about engineering specifications, finance, marketing, and HR policies."
    )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Ask a question about your authorized documents",
        submit_mode="disable",
    )
    if prompt is None:
        prompt = st.session_state.pop("pending_prompt", None)
    if not prompt or not prompt.strip():
        return

    prompt = prompt.strip()
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            from securdocs.rag import query_rag_pipeline

            answer = st.write_stream(
                query_rag_pipeline(user_role=user["role"], query_text=prompt)
            )
        except Exception as error:
            answer = f"Unable to generate a response: {error}"
            st.error(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})


if "user" not in st.session_state:
    render_login()
else:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    render_chat()
