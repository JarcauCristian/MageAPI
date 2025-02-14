import os
import re
import asyncio
import subprocess
import tempfile
from typing import AsyncIterator,Tuple

from langchain_core.output_parsers import StrOutputParser   
from langchain_core.prompts import ChatPromptTemplate

from langchain_ollama import ChatOllama

from langchain import hub

from langgraph.graph import END, StateGraph, START

from rag.models import BlockType, GradeAnswer, GradeDocuments, GradeHallucinations 
from rag.graph import GraphState
from rag.data import get_retriever

retriever = get_retriever()
 
llm = ChatOllama(model="llama3.1:70b", base_url=os.getenv("OLLAMA_URL"), temperature=0)

# --- Grade Documents ---
structured_llm_grader = llm.with_structured_output(GradeDocuments)

system = (
    "You are a grader assessing the relevance of a retrieved document, in regards to the type of the block, to a user's question that requests a Mage AI block. "
    "If the document contains keywords or semantic context related to generating Mage AI blocks, grade it as relevant. "
    "Your task is not to be overly stringent—the goal is to filter out documents that are unlikely to support accurate Mage AI code generation. "
    "Provide a binary score: 'yes' if the document is relevant, 'no' otherwise."
)
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Retrieved document: \n\n {document} \n\n Block type: {block_type} \n\n User question: {question}"),
    ]
)

retrieval_grader = grade_prompt | structured_llm_grader

# --- Actual RAG ---
prompt = hub.pull("sedimark/mage_prompt")


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = prompt | llm | StrOutputParser()

# --- Halluciantions Grader ---

structured_llm_grader = llm.with_structured_output(GradeHallucinations)
system = (
    "You are a grader evaluating whether the generated Mage AI block is properly formatted according to the provided set of documents and if generation does what the user's question asked. "
    "Assess if the code output is clearly supported by the retrieved facts. "
    "Provide a binary score: 'yes' if the generation is well-supported, 'no' otherwise."
)
hallucination_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "User question: {question} \n\n Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
    ]
)
hallucination_grader = hallucination_prompt | structured_llm_grader

# --- Grader Answer ---

structured_llm_grader = llm.with_structured_output(GradeAnswer)

system = (
    "You are a grader assessing whether the generated answer provides a correct and functional Mage AI block that addresses the user's question. "
    "Evaluate if the code meets the requirements and truly resolves the inquiry. "
    "Provide a binary score: 'yes' if the answer is satisfactory, 'no' otherwise."
)
answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
    ]
)
answer_grader = answer_prompt | structured_llm_grader

# --- Rewriter ---

system = (
    "You are a question rewriter that refines an input question to optimize document retrieval for generating Mage AI blocks. "
    "Analyze the original question and produce a clearer, more targeted version that captures the intent of generating a functional Mage AI block."
)
re_write_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        (
            "human",
            "Here is the initial question: \n\n {question} \n Formulate an improved question.",
        ),
    ]
)

question_rewriter = re_write_prompt | llm | StrOutputParser()

# --- Code Rewriter ---
system = (
    "You are a Python code fixer that ensures that the generated Python code is correct from the syntax point of view. "
    "Evaluate the code and if the code has syntax issues fix them. "
    "Provide only the updated Python code as a response."
)
code_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "LLM generation: {generation}"),
    ]
)
code_fixer = code_prompt | llm | StrOutputParser()

# --- Block Type ---

structured_llm_typer = llm.with_structured_output(BlockType)
system = (
    "You are a assessor to assess the type of the Mage AI block based on the user's question. "
    "Analyze the question and produce a concrete type. "
    "Provide a block type: loader if the question implies a loader block, transformer for transformer blocks, exporter for exporter blocks and sensor for sensor."
)
block_type_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        (
            "human",
            "{question}",
        ),
    ]
)

block_typer = block_type_prompt | structured_llm_typer


def block_type(state):
    print("---BLOCK TYPE---")
    question = state["question"]

    bl_type = block_typer.invoke({"question": question})

    if bl_type:
        return {"block_type": bl_type.block_type}

    return {"block_type": "loader"}


def retrieve(state):
    print("---RETRIEVE---")
    question = state["question"]
    bl_type= state["block_type"]

    retriever.search_kwargs["filter"] = {"block_type": bl_type}
    documents = retriever.invoke(question)

    return {"documents": documents, "question": question}


def generate(state):
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]

    generation = rag_chain.invoke({"context": documents, "question": question})
    return {"documents": documents, "question": question, "generation": generation}


def grade_documents(state):
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]
    bl_type = state["block_type"]

    filtered_docs = []
    for d in documents:
        score = retrieval_grader.invoke(
            {"question": question, "block_type": bl_type, "document": d.page_content}
        )
        grade = score.binary_score
        if grade == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            continue
    return {"documents": filtered_docs, "question": question}


def transform_query(state):
    print("---TRANSFORM QUERY---")
    question = state["question"]
    documents = state["documents"]

    better_question = question_rewriter.invoke({"question": question})
    return {"documents": documents, "question": better_question}


def transform_code(state):
    print("---TRANSFORM CODE---")
    generation = state["generation"]
    better_code = code_fixer.invoke({"generation": generation})

    pattern = re.compile(r'```python\s*(.*?)\s*```', re.DOTALL)
    better_code = pattern.search(better_code)

    if better_code:
        return {"generation": better_code.group(1)}

    return {"generation": generation}


def decide_to_generate(state):
    print("---ASSESS GRADED DOCUMENTS---")
    state["question"]
    filtered_documents = state["documents"]

    if not filtered_documents:
        print(
            "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
        )
        return "transform_query"
    else:
        print("---DECISION: GENERATE---")
        return "generate"


def grade_generation_v_documents_and_question(state):
    print("---CHECK HALLUCINATIONS---")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]

    score = hallucination_grader.invoke(
        {"question": question, "documents": documents, "generation": generation}
    )
    grade = score.binary_score

    if grade == "yes":
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        print("---GRADE GENERATION vs QUESTION---")
        score = answer_grader.invoke({"question": question, "generation": generation})
        grade = score.binary_score
        if grade == "yes":
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
    else:
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not supported"
    

def node_description(node_name: str) -> str | None:
    if node_name == "bl_type":
        return "Extracting the type of block based on user question."
    if node_name == "retrieve":
        return "Retrieve most similar blocks already in memory."
    if node_name == "grade_documents":
        return "Grading previously retrieved documents based on relevancy to the user's question."
    if node_name == "generate":
        return "Generating the new block based on user's question."
    if node_name == "transform_query":
        return "Modifing user's question to be better understand by the LLM."
    if node_name == "transform_code":
        return "Fixing the code if there are any issues in the genration."

    return None

def build_workflow():
    workflow = StateGraph(GraphState)

    workflow.add_node("bl_type", block_type)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate", generate)
    workflow.add_node("transform_query", transform_query)
    workflow.add_node("transform_code", transform_code)

    workflow.add_edge(START, "bl_type")
    workflow.add_edge("bl_type", "retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "transform_query": "transform_query",
            "generate": "generate",
        },
    )
    workflow.add_edge("transform_query", "retrieve")
    workflow.add_conditional_edges(
        "generate",
        grade_generation_v_documents_and_question,
        {
            "not supported": "generate",
            "useful": "transform_code",
            "not useful": "transform_query",
        },
    )
    workflow.add_edge("transform_code", END)

    return workflow.compile()

mage_app = build_workflow()

async def run_workflow(question: str) -> AsyncIterator[Tuple[str, bool]]:
    yield (f"Starting workflow for question: {question}", False)
    input = {"question": question}
    final_result = None

    for output in mage_app.stream(input):
        await asyncio.sleep(0)
        for node_name, result in output.items():
            final_result = result
            yield (node_name, False)
            await asyncio.sleep(0)

    if final_result and final_result.get("generation"):
        yield (result.get("generation"), True)
    else:
        yield ("Failed generation!", False)


def apply_ruff(code: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as temp:
        temp.write(code)
        temp.close()

        try:
            subprocess.run(["ruff", "check", "--fix", temp.name], capture_output=True, check=True, shell=False)
        except Exception:
            os.remove(temp.name)
            return code
        
        with open(temp.name, 'r') as fp:
            result = fp.read()
            fp.close()

            os.remove(temp.name)

    return result
