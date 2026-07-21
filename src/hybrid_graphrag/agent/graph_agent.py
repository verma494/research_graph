from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from .state import AgentState
from .tools.graph_tools import GRAPH_TOOLS
from ..logging import logger

def execute_graph_agent(state: AgentState) -> AgentState:
    query = state["query"]
    logger.info("Executing Graph Agent...")
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    agent = create_react_agent(llm, tools=GRAPH_TOOLS)
    
    sys_msg = SystemMessage(content="""You are a graph database assistant. Use the provided tools to fetch relationships from Neo4j to answer the user query. Gather all the evidence needed.
    CRITICAL RULE: DO NOT CALL THE SAME TOOL MORE THAN TWICE. Once you gather initial context, you MUST provide an answer immediately. Do not loop endlessly.
    CRITICAL RULE 2: DO NOT EXECUTE MULTIPLE TOOLS IN PARALLEL. You must execute exactly ONE single tool call at a time.""")
    
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
                
    return {"graph_evidence": evidence, "tool_calls": tool_calls}
