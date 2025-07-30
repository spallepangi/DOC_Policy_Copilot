# Technical Documentation: Missouri DOC Policy Copilot

**Version:** 2.0
**Last Updated:** 2025-07-30

## 1. Overview

The Missouri DOC Policy Copilot is an advanced AI-powered assistant designed to provide clear, accurate, and easy-to-understand answers to questions about the Missouri Department of Corrections (DOC) policies and procedures. It leverages a sophisticated Retrieval-Augmented Generation (RAG) pipeline, combining the retrieval power of a FAISS vector store with the generative capabilities of Google's Gemini large language models.

The system is built to be used by a wide audience, including inmates, their families, and the general public, and features a user-friendly interface built with Streamlit.

### Key Features:
- **Advanced RAG Pipeline**: Integrates query rewriting, semantic reranking, and modular prompts for high-quality responses.
- **Gemini 2.0 Flash Integration**: Utilizes the latest Gemini model for fast and accurate response generation.
- **Semantic Chunking**: Employs LangChain’s `RecursiveCharacterTextSplitter` to maintain the semantic integrity of policy documents.
- **Interactive UI**: A simple and intuitive web interface powered by Streamlit.
- **Evaluation and Logging**: A `loguru`-based module for detailed logging of RAG performance to flag hallucinations and analyze results.
- **Configurability**: A central `config.py` file allows for easy tuning of all key parameters.

## 2. System Architecture

The system is composed of a backend RAG pipeline and a frontend Streamlit application. They interact to provide a seamless user experience.

```mermaid
graph TD
    subgraph User Interface (streamlit_app.py)
        A[User Input] --> B{Streamlit App};
        B --> C[Ask a Question];
        C --> D{RAGPipeline.generate_response()};
        D --> E[Display Response & Sources];
    end

    subgraph Backend (main.py, vector_store.py, etc.)
        F[PDF Policy Documents] --> G(Document Loader);
        G --> H(Semantic Chunker);
        H --> I(Embedding Generator);
        I --> J[FAISS Vector Store];
        
        D -- RAG Pipeline --> K{Query Rewriter};
        K --> L{Initial Retrieval};
        L --> M{Semantic Reranker};
        M --> N{Prompt Engine};
        N --> O{Gemini 2.0 Flash};
        O --> D;

        L -- Retrieves from --> J;
    end

    subgraph Logging (evaluation.py)
        D -- Logs data --> P[Evaluation Logger];
        P --> Q[rag_evaluation.log];
    end
```

## 3. In-Depth RAG Pipeline Overview

The RAG pipeline is the core of the system. It transforms user queries into accurate, context-aware answers based on the provided policy documents.

### Step 1: Document Ingestion and Indexing (Offline Process)
This process happens once or whenever new documents are added.

1.  **Load Documents**: PDF files from the `data/policies/` directory are loaded using `PyMuPDF` (`fitz`) in `utils.py`.
2.  **Pre-process Text**: The extracted text is cleaned to remove excessive whitespace and special characters (`clean_text` in `utils.py`).
3.  **Semantic Chunking**: The text is split into smaller, semantically meaningful chunks using LangChain’s `RecursiveCharacterTextSplitter`. This splitter tries to break text on paragraphs, sentences, and other logical boundaries to keep related information together. Chunk size and overlap are configured in `config.py`.
4.  **Generate Embeddings**: Each chunk is converted into a high-dimensional vector (embedding) using Google's `models/embedding-001` model. This is handled by the `generate_embeddings` method in `vector_store.py`.
5.  **Index in FAISS**: The generated embeddings are stored in a FAISS (`IndexFlatIP`) index. FAISS allows for efficient similarity search. The index and its corresponding document metadata are saved to the `index/faiss_index/` directory, allowing the system to load a pre-built index on startup.

### Step 2: Query Processing and Response Generation (Online Process)
This process occurs for every user query.

1.  **Query Rewriting**: When a user submits a query, it first goes through a Gemini-powered rewriting step (`_rewrite_query` in `main.py`). The `QUERY_REWRITE_PROMPT` instructs the model to make the query more specific and clear, adding relevant keywords. This significantly improves retrieval accuracy.
    - *Example*: "what is leave policy?" -> "Missouri Department of Corrections employee leave policy, including annual leave, sick leave, family and medical leave (FMLA)..."

2.  **Initial Retrieval**: The (potentially rewritten) query is embedded, and the FAISS index is searched to retrieve the `TOP_K_RETRIEVAL` most similar document chunks.

3.  **Fallback for Low Similarity**: If the similarity scores of all retrieved chunks are below the `SIMILARITY_THRESHOLD` in `config.py`, the system assumes no relevant context was found and generates a helpful fallback message using the `LOW_CONFIDENCE_RESPONSE` prompt.

4.  **Semantic Reranking**: The retrieved chunks are then reranked using a Gemini prompt (`_semantic_rerank` in `main.py`). This step re-evaluates the chunks in the context of the specific query, improving the relevance of the final context. The top `TOP_K_RERANKED` chunks are selected.

5.  **Context Compilation**: The text from the top reranked chunks is compiled into a single context string to be passed to the language model.

6.  **Prompt Engineering & Final Response**: The compiled context and the original user query are inserted into the `BASE_PROMPT`. This final prompt instructs the model on tone, style, and rules (e.g., to not use jargon and to cite sources). The prompt is sent to the `gemini-2.0-flash` model, which generates the final, user-facing answer.

7.  **Evaluation Logging**: The entire process—from the original query to the final answer, including all retrieved/reranked chunks and their scores—is logged to `logs/rag_evaluation.log`. This structured log is invaluable for debugging, analysis, and future fine-tuning.

## 4. Core Modules and Components

-   **`main.py`**: Orchestrates the entire RAG pipeline within the `RAGPipeline` class. It handles query rewriting, retrieval, reranking, and response generation.
-   **`streamlit_app.py`**: Provides the user interface. It initializes the `RAGPipeline`, captures user input, displays the response, and manages the chat history.
-   **`utils.py`**: Contains helper functions for loading PDFs, cleaning text, and chunking documents.
-   **`vector_store.py`**: The `VectorStore` class abstracts away the complexities of embedding generation and FAISS indexing.
-   **`evaluation.py`**: Manages the logging of evaluation data and includes a basic hallucination detection function.
-   **`config.py`**: A centralized file for all system parameters, making it easy to tune the pipeline's performance.
-   **`prompts/`**: A directory containing Python files for each of the modular prompts, separating prompt logic from the application code.
-   **`.env`**: Stores the `GEMINI_API_KEY` securely.
-   **`requirements.txt`**: Lists all Python dependencies for the project.

## 5. Setup and Deployment

### Local Setup

1.  **Clone the repository.**
2.  **Install dependencies**: `pip install -r requirements.txt`
3.  **Create `.env` file**: Create a `.env` file in the root directory and add your Gemini API key:
    ```
    GEMINI_API_KEY=YOUR_API_KEY_HERE
    ```
4.  **Add PDF Documents**: Place your policy PDF files in the `data/policies/` directory.
5.  **Run the application**: `streamlit run streamlit_app.py`

### Deployment (Streamlit Cloud)

1.  **Push to GitHub**: Ensure your repository is up-to-date on GitHub.
2.  **Create a Streamlit Cloud App**: Connect your GitHub repository to Streamlit Cloud.
3.  **Set Environment Variables**: In the Streamlit Cloud app settings, add `GEMINI_API_KEY` as a secret.
4.  **Deploy**: The app will automatically build and deploy. The graceful import handling for `config.py` ensures the app will run even though the file is not in the repo.

## 6. Potential Future Upgrades

The current system is powerful and robust, but it can be enhanced further:

1.  **Advanced Reranker**: Replace the current prompt-based reranker with a dedicated, more efficient reranker model like Cohere Rerank or a cross-encoder model for better performance.

2.  **Smarter Hallucination Detection**: Implement a more sophisticated hallucination detection system using Natural Language Inference (NLI) models to verify that every claim in the generated response is directly supported by the source context.

3.  **Conversational Memory**: Add a conversational memory module (e.g., `ConversationBufferMemory` in LangChain) to allow the assistant to remember previous turns in the conversation and answer follow-up questions more effectively.

4.  **User Feedback Mechanism**: Add "thumbs up/down" buttons in the UI to collect user feedback on the quality of responses. This data can be logged and used to fine-tune the system.

5.  **Automated Document Ingestion**: Create a script or a separate UI to automate the process of adding new documents, which would automatically trigger re-indexing.

6.  **Hybrid Search**: Combine the current semantic search with traditional keyword-based search (e.g., BM25) to improve retrieval for queries that rely on specific codes or jargon.

7.  **Analytics Dashboard**: Build a Streamlit or Dash dashboard to visualize the data from the `rag_evaluation.log` file, providing insights into query patterns, response quality, and potential areas for improvement.

8.  **Support for More Document Types**: Extend the document loader to support other formats like `.docx`, `.html`, or even scrape content directly from web pages.

