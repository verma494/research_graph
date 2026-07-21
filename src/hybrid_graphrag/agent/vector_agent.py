from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from .state import AgentState
from .tools.vector_tools import VECTOR_TOOLS
from ..logging import logger

def execute_vector_agent(state: AgentState) -> AgentState:
    query = state["query"]
    logger.info("Executing Vector Agent...")
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    agent = create_react_agent(llm, tools=VECTOR_TOOLS)
    
    sys_msg = SystemMessage(content="""You are a vector database assistant. Use the vector tools to fetch PDF text chunks to answer the user query.
    CRITICAL RULE: DO NOT CALL THE SAME TOOL MORE THAN TWICE. If a tool returns an error or empty array, DO NOT keep retrying it. You MUST provide an answer immediately based on the context you have.
    CRITICAL RULE 2: DO NOT EXECUTE MULTIPLE TOOLS IN PARALLEL. You must execute exactly ONE single tool call at a time to test if the data exists.""")
    
    response = agent.invoke({"messages": [sys_msg, HumanMessage(content=query)]}, {"recursion_limit": 15})
    
    evidence = []
    tool_calls = []
    
    for msg in response["messages"]:
        if msg.type == "tool":
            evidence.append({msg.name: msg.content})
            
    for msg in response["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({"name": tc.get("name", ""), "args": tc.get("args", {})})
                
    return {"vector_evidence": evidence, "tool_calls": tool_calls}
