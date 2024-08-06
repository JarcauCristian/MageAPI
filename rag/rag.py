from ollama import Client
from rag.embed import Embed
from typing import Dict, Any
from rag.memory import Memory
from chromadb import PersistentClient
from langchain_community.llms.ollama import Ollama
from langchain_community.vectorstores import Chroma
from langchain.chains.retrieval_qa.base import RetrievalQA


class RAGPipeline:
    def __init__(
        self,
        ollama_url: str, 
        ollama_model: str,
        ollama_client: Client,
        ollama_embed_model: str,
        chroma_client: PersistentClient,
        chroma_collection_name: str,
    ) -> None:
        self.ollama_llm = Ollama(base_url=ollama_url, model=ollama_model, temperature=0.1)
        self.embeddings = Embed(ollama_client, ollama_embed_model)
        self.db_retriever = Chroma(
            client=chroma_client,
            collection_name=chroma_collection_name,
            embedding_function=self.embeddings,
        )
        self.rag = RetrievalQA.from_chain_type(
            self.ollama_llm,
            retriever=self.db_retriever.as_retriever(search_type="mmr", search_kwargs={"k": 4, "fetch_k": 10}),
            return_source_documents=True,
        )

        self.memory = Memory()

    @staticmethod
    def build_prompt(data: str) -> str:
        return '''
            You are an expert in creating MageAI blocks based on the description received by the user.
            You must return the the Python code for the block as an YAML object, exactly in the format provided inside **Example output** section, without any other information beside it.
            All the python code should strictly adhere to the Mage AI block templates based on block type which is inferred from the description, and inside the decorated function add all the necessary addition to the code, including imports.
            **Example Output**
            ```
            python_code: |
                <Python Code>
            ```
            
            Here is the description of the block
            {}  
        '''.format(
            data
        )

    def invoke(self, session_id: str, description: str) -> Dict[str, Any]:
        query = self.build_prompt(description)

        # Check session memory first
        memory_response = self.memory.retrieve_interaction(session_id, query)
        if memory_response:
            return {"result": memory_response["answer"], "source_documents": []}

        session_context = self.memory.get_session_context(session_id)
        full_query = f"{session_context}\n{query}"

        response = self.rag.invoke({"query": full_query})
        answer = response['result']

        self.memory.store_interaction(session_id, query, answer)

        return response

    def clear_session(self, session_id: str):
        self.memory.clear_session(session_id)
