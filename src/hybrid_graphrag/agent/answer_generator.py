from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from .state import AgentState

answer_prompt = PromptTemplate.from_template("""
You are a highly intelligent Research Assistant.
You must answer the User Query based primarily on the Evidence Package provided below.

EVIDENCE PACKAGE:
{evidence}

RULES:
1. If the Evidence Package contains relevant information, use it to construct a detailed answer.
2. If the Evidence Package is empty or lacks information, fallback to your own knowledge, but state that you are doing so.
3. NEVER claim "According to the graph" if no graph evidence was provided.
4. NEVER claim "According to the paper" if no vector evidence was provided.

User Query: {query}
Answer:
""")

def generate_answer(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    chain = answer_prompt | llm
    result = chain.invoke({"evidence": state.get("evidence_package", ""), "query": state["query"]})
    return {"final_answer": result.content}
