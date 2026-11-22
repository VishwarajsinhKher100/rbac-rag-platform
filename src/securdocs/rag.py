from functools import lru_cache
from pathlib import Path
from typing import Iterator, List

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import CSVLoader, PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

CHROMA_STORAGE_DIR = PROJECT_ROOT / "chroma_db"
DOCUMENTS_SOURCE_DIR = PROJECT_ROOT / "data"

DEPARTMENT_ACCESS_PERMISSIONS = {
    "general": ["engineering", "finance", "hr", "marketing", "ceo", "employee"],
    "engineering": ["engineering", "ceo"],
    "finance": ["finance", "ceo"],
    "hr": ["hr", "ceo"],
    "marketing": ["marketing", "ceo"],
}


@lru_cache(maxsize=1)
def get_language_model() -> ChatGroq:
    return ChatGroq(model="openai/gpt-oss-120b")


@lru_cache(maxsize=1)
def get_embedding_model() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def ingest_documents_to_vectorstore() -> Chroma:
    """Load PDFs and CSVs, apply department tags, and persist them to ChromaDB."""
    parsed_document_chunks = []
    text_chunker = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

    if not DOCUMENTS_SOURCE_DIR.exists():
        raise FileNotFoundError(
            f"The '{DOCUMENTS_SOURCE_DIR}' directory does not exist."
        )

    for file_path in DOCUMENTS_SOURCE_DIR.rglob("*"):
        if not file_path.is_file():
            continue

        department_category = file_path.parent.name.lower()

        if file_path.suffix.lower() == ".pdf":
            pdf_chunks = text_chunker.split_documents(
                PyPDFLoader(str(file_path)).load()
            )
            for chunk in pdf_chunks:
                chunk.metadata["department"] = department_category
            parsed_document_chunks.extend(pdf_chunks)
        elif file_path.suffix.lower() == ".csv":
            csv_rows = CSVLoader(file_path=str(file_path), encoding="utf-8").load()
            for row in csv_rows:
                row.metadata["department"] = department_category
            parsed_document_chunks.extend(csv_rows)

    if not parsed_document_chunks:
        raise ValueError(f"No valid documents found in '{DOCUMENTS_SOURCE_DIR}'.")

    return Chroma.from_documents(
        documents=parsed_document_chunks,
        embedding=get_embedding_model(),
        persist_directory=str(CHROMA_STORAGE_DIR),
    )


def get_vectorstore_instance() -> Chroma:
    """Load the existing Chroma vectorstore or build it if missing."""
    if CHROMA_STORAGE_DIR.exists():
        return Chroma(
            persist_directory=str(CHROMA_STORAGE_DIR),
            embedding_function=get_embedding_model(),
        )
    return ingest_documents_to_vectorstore()


def query_rag_pipeline(user_role: str, query_text: str) -> Iterator[str]:
    """Stream an answer using only documents authorized for the user's role."""
    vectorstore_instance = get_vectorstore_instance()
    allowed_departments = [
        department
        for department, authorized_roles in DEPARTMENT_ACCESS_PERMISSIONS.items()
        if user_role in authorized_roles
    ]
    if user_role and user_role not in allowed_departments:
        allowed_departments.append(user_role)

    document_retriever = vectorstore_instance.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4, "filter": {"department": {"$in": allowed_departments}}},
    )

    def format_retrieved_documents(documents: List) -> str:
        if not documents:
            return "No authorized context found."
        return "\n\n".join(
            f"[Source: {doc.metadata.get('source', 'Unknown')} | "
            f"Dept: {doc.metadata.get('department', 'Unknown')}]\n{doc.page_content}"
            for doc in documents
        )

    prompt_template = ChatPromptTemplate.from_template("""
    You are an internal assistant. Answer using ONLY the authorized context below.
    If no context is provided or authorized, state that the user lacks access.
    Context: {context}
    Question: {question}
    Answer:
    """)

    rag_execution_chain = (
        {
            "context": document_retriever | format_retrieved_documents,
            "question": RunnablePassthrough(),
        }
        | prompt_template
        | get_language_model()
        | StrOutputParser()
    )
    return rag_execution_chain.stream(query_text)
