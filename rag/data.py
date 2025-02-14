from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.schema.vectorstore import VectorStoreRetriever

from langchain_chroma import Chroma

from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders.python import PythonLoader

from langchain_ollama import OllamaEmbeddings

from typing import Any, Literal
from pathlib import Path
import os


def insert_type(documents: list[Any], doc_type: str) -> list[Any]:
    returns = []
    for document in documents:
        document.metadata.update({"block_type": doc_type})
        returns.append(document)

    return returns


def add_document(retriever: VectorStoreRetriever, document: str, doc_type: Literal["loader", "transformer", "exporter"]) -> list[str]:
    document = Document(page_content = document, metadata={"source": "orchestartor", "block_type": doc_type})

    return retriever.add_documents([document])
    

def load_chunk(path: Path, file_type: str, doc_type: str) -> list[Document]:
    if file_type not in ["python", "yaml"]:
        raise ValueError("Valid values for doc_type: python or yaml")

    docs = []
    if file_type == "python":
        docs = [PythonLoader(file).load() for file in path.glob("*.py")]
    else:
        docs = [TextLoader(file).load() for file in path.glob("*.yaml")]

    docs_list = [item for sublist in docs for item in sublist]
    return insert_type(docs_list, doc_type)


def split_chunks(paths: list[dict[str, Any]]) -> Any:
    docs = []
    for path in paths:
        chunk = load_chunk(path["path"], path["file_type"], path["doc_type"])
        docs.extend(chunk)

    text_spliter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=500, chunk_overlap=0)  # noqa: E501
    return text_spliter.split_documents(docs)


def get_retriever():

    embed = OllamaEmbeddings(model="llama3.1:70b", base_url=os.getenv("OLLAMA_URL"))

    if not Path("db").exists():
        doc_paths = [
            {
                "path": Path("rag/blocks/loaders"),
                "file_type": "python",
                "doc_type": "loader",
            },
            {
                "path": Path("rag/blocks/transformers"),
                "file_type": "python",
                "doc_type": "transformer",
            },
            {
                "path": Path("rag/blocks/exporters"),
                "file_type": "python",
                "doc_type": "exporter",
            },
        ]

        doc_splits = split_chunks(doc_paths)

    vectorstore = Chroma(persist_directory="db", collection_name="mage-rag-chroma", embedding_function=embed) if Path("db").exists() else Chroma.from_documents(
        persist_directory="./db",
        documents=doc_splits,
        collection_name="mage-rag-chroma",
        embedding=embed
    )

    retriever = vectorstore.as_retriever()

    return retriever
