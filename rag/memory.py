from typing import Dict, Any
from collections import defaultdict


class Memory:
    def __init__(self):
        self.memory = defaultdict(list)

    def store_interaction(self, session_id: str, query: str, answer: str):
        self.memory[session_id].append({"question": query, "answer": answer})

    def retrieve_interaction(self, session_id: str, query: str) -> Dict[str, Any] | None:
        for interaction in self.memory[session_id]:
            if interaction["question"] == query:
                return interaction
        return None

    def get_session_context(self, session_id: str) -> str:
        context = ""
        for interaction in self.memory[session_id]:
            context += f"Question: {interaction['question']}\nAnswer: {interaction['answer']}\n"
        return context

    def clear_session(self, session_id: str):
        self.memory[session_id] = []