from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader

from db.path_utils import find_data_path

try:
    from .vector_handler import VectorHandler
except ImportError:
    try:
        from backend.db.vector_handler import VectorHandler
    except ImportError:
        from db.vector_handler import VectorHandler


def ingest():
    manuals_dir = find_data_path("product_manuals")
    loader = DirectoryLoader(str(manuals_dir), glob="*.txt", loader_cls=TextLoader)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    vh = VectorHandler()
    vh.ingest_documents(chunks)
    print(f"Ingested {len(chunks)} chunks into ChromaDB")


if __name__ == "__main__":
    ingest()
