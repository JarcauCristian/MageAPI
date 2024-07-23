import uuid
import logging
import chromadb
import numpy as np
from ollama import Client
from tokenizers import Tokenizer
from semantic_text_splitter import TextSplitter
from sentence_transformers import SentenceTransformer, util


class Ingester:
    def __init__(self, ollama_client: Client, chroma_client: chromadb.PersistentClient, ollama_embed_model: str, tokenizer: str, max_tokens: int, threshold: float = 0.5) -> None:
        self.client = ollama_client
        self.chroma_client = chroma_client
        self.embed_model = ollama_embed_model
        self.model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
        self.threshold = threshold
        self.tokenizer = Tokenizer.from_pretrained(tokenizer)
        self.splitter: TextSplitter = TextSplitter.from_huggingface_tokenizer(self.tokenizer, capacity=max_tokens, overlap=50, trim=True)
    
    def chunk_it(self, text: str) -> list[str]:
        chunks = self.splitter.chunks(text)
        return chunks
    
    def embed_and_store(self, collection: chromadb.Collection, text: str, filename: str, block_type: str, description: str) -> None:
        chunks = self.chunk_it(text)
        for chunk in chunks:
            uid = uuid.uuid4().hex
            logging.info(id)
            embed = self.client.embeddings(self.embed_model, chunk)["embedding"]
            collection.add([uid], [embed], documents=[chunk], metadatas=[{"source": filename, "block_type": block_type, "description": description}])

    def ingest(
        self,
        text: str,
        filename: str,
        block_type: str,
        description: str,
        chroma_collection_name: str,
    ) -> None:
        collection = self.chroma_client.get_or_create_collection(chroma_collection_name)
        self.embed_and_store(collection, text, filename, block_type, description)

    def encode_input(self, string_input: str) -> np.ndarray:
        return self.model.encode(string_input, convert_to_tensor=True)

    @staticmethod
    def calculate_similarity(embedding1, embedding2) -> float:
        return util.pytorch_cos_sim(embedding1, embedding2).item()

    def retrieve_specific(self, collection: str, query: str, block_type: str) -> dict:
        collection = self.chroma_client.get_or_create_collection(collection)
        documents = collection.get(include=["documents", "metadatas"], where={"block_type": {"$eq": block_type}})
        query_embedding = self.encode_input(query.lower())
        filtered_docs = []

        for doc in documents["metadatas"]:
            doc_embedding = self.encode_input(doc["description"].lower())
            similarity = self.calculate_similarity(query_embedding, doc_embedding)
            print(f"Similarity with doc '{doc['description']}': {similarity}")
            filtered_docs.append({"similarity": similarity, "doc": doc})

        filtered_docs.sort(key=lambda x: x["similarity"], reverse=True)

        if len(filtered_docs) == 0 or filtered_docs[0]["similarity"] < self.threshold:
            returns = collection.get(include=["documents", "metadatas"], where={
                "$and": [{"block_type": {"$eq": block_type}}, {"source": {"$eq": "default.py"}}]})
            return dict(returns["metadatas"][0])

        return filtered_docs[0]["doc"]
