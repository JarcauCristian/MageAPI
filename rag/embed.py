from ollama import Client
from typing import Sequence


class Embed:
    def __init__(self, ollama_client: Client, embed_model: str) -> None:
        self.ollama_client = ollama_client
        self.embed_model = embed_model

    def embed_query(self, text: str) -> Sequence[float]:
        return self.ollama_client.embeddings(self.embed_model, text)["embedding"]
