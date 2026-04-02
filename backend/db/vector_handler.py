import os
import hashlib
import re
import shutil
import warnings
import logging

import chromadb
from chromadb.config import Settings
from langchain_core.documents import Document

os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")
logging.getLogger("chromadb").setLevel(logging.ERROR)
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)

try:
    from langchain_chroma import Chroma
except Exception:
    from langchain_community.vectorstores import Chroma

try:
    from langchain_core._api.deprecation import LangChainDeprecationWarning

    warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)
except Exception:
    pass


class HashEmbeddingFunction:
    def __call__(self, input):
        return [self._embed_text(text) for text in input]

    def embed_documents(self, texts):
        return [self._embed_text(text) for text in texts]

    def embed_query(self, text):
        return self._embed_text(text)

    def _embed_text(self, text: str, dimensions: int = 128):
        vector = [0.0] * dimensions
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for index in range(0, len(digest), 2):
                position = digest[index] % dimensions
                vector[position] += 1.0
        norm = sum(value * value for value in vector) ** 0.5
        if norm:
            vector = [value / norm for value in vector]
        return vector

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
LOCAL_CHROMA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")
)

class VectorHandler:
    def __init__(self):
        self._use_local_storage = CHROMA_HOST == "localhost"

        try:
            from langchain_huggingface import HuggingFaceEmbeddings

            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        except Exception:
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings

                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
            except Exception:
                self.embeddings = HashEmbeddingFunction()

        self.vectorstore = self._build_vectorstore()

    def _create_client(self):
        if self._use_local_storage:
            return chromadb.PersistentClient(
                path=LOCAL_CHROMA_PATH,
                settings=Settings(anonymized_telemetry=False),
            )
        return chromadb.HttpClient(
            host=CHROMA_HOST,
            port=8080,
            settings=Settings(anonymized_telemetry=False),
        )

    def _build_vectorstore(self):
        try:
            self.client = self._create_client()
            return Chroma(
                client=self.client,
                collection_name="product_manuals",
                embedding_function=self.embeddings,
            )
        except Exception:
            if self._use_local_storage:
                shutil.rmtree(LOCAL_CHROMA_PATH, ignore_errors=True)
                self.client = chromadb.PersistentClient(
                    path=LOCAL_CHROMA_PATH,
                    settings=Settings(anonymized_telemetry=False),
                )
                try:
                    return Chroma(
                        client=self.client,
                        collection_name="product_manuals",
                        embedding_function=self.embeddings,
                    )
                except Exception:
                    self.client = chromadb.EphemeralClient()
                    return Chroma(
                        client=self.client,
                        collection_name="product_manuals",
                        embedding_function=self.embeddings,
                    )
            self.client = chromadb.EphemeralClient()
            return Chroma(
                client=self.client,
                collection_name="product_manuals",
                embedding_function=self.embeddings,
            )

    def ingest_documents(self, docs: list[Document]):
        self.vectorstore.add_documents(docs)

    def similarity_search(self, query: str, k: int = 3):
        return self.vectorstore.similarity_search(query, k=k)