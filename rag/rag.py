from ollama import Client
from rag.embed import Embed
from chromadb import PersistentClient
from langchain_community.llms.ollama import Ollama
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


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
        # self.rag = RetrievalQA.from_chain_type(
        #     self.ollama_llm,
        #     retriever=self.db_retriever.as_retriever(search_type="mmr", search_kwargs={"k": 4, "fetch_k": 10}),
        #     return_source_documents=True,
        # )
        self.rag = (
                {"context": self.db_retriever.as_retriever() | self.format_docs, "question": RunnablePassthrough()}
                | ChatPromptTemplate.from_template(self.prompt())
                | self.ollama_llm
                | StrOutputParser()
        )

    @staticmethod
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    @staticmethod
    def prompt() -> str:
        return '''
            You are an expert in creating MageAI blocks based on the description received by the user. You must return the the Python code for the block as an YAML object, exactly in the format provided inside <output></output> XML tags, without any other information beside it. All the python code should strictly adhere to the Mage AI block templates based on block type which is inferred from the description, and inside the decorated function add all the necessary addition to the code, including imports. Also the return type of a function should only be something that is JSON serializable, such as dicts or pandas DataFrames. Look for [block_type=<type>] to infer the type of the block.
            <output>
            
            </output>
            <context>{context}</context>
            Here is the description of the block
            {question}  
        '''

    def invoke(self, description: str) -> str:
        response = self.rag.invoke(description)

        return response
