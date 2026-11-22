# SecurDocs.AI

SecurDocs.AI is a Streamlit document assistant that uses role-based filtering
before retrieving company documents for a RAG response. The application, data,
and Python package live in one project; there is no separate API server or
JavaScript frontend.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- Python 3.12 (uv can install the pinned version)
- A Groq API key

## Setup

From the repository root, create the Python 3.12 virtual environment and install
the project dependencies:

```powershell
uv python install 3.12
uv sync
```

Create a `.env` file in the project root and add your Groq key:

```dotenv
GROQ_API_KEY=your_groq_api_key
```

Run the app:

```powershell
uv run streamlit run app.py
```

Streamlit opens the app at `http://localhost:8501`. On first launch, the app
creates `users.db` and seeds the demo accounts declared in
`src/securdocs/database.py`. Change those credentials before using the app with
real or shared data. The first question may take longer while the local
embedding model and document index are initialized.

## Project layout

```text
app.py                  Streamlit login and chat interface
src/securdocs/          SQLite authentication and RAG pipeline
data/                   Department-scoped source documents
pyproject.toml          Dependencies and Python project configuration
uv.lock                 Resolved dependency versions
```

The `chroma_db/` vector index and `users.db` SQLite database are generated
locally and are excluded from version control.
