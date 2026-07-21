from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from .state import AgentState
from .tools.graph_tools import GRAPH_TOOLS
from .tools.vector_tools import VECTOR_TOOLS
from ..logging import logger

def execute_hybrid_agent(state: AgentState) -> AgentState:
    query = state["query"]
    logger.info("Executing Hybrid Agent...")
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    tools = GRAPH_TOOLS + VECTOR_TOOLS
    agent = create_react_agent(llm, tools=tools)
    
    sys_msg = SystemMessage(content="""You are a Hybrid GraphRAG assistant. 
    You have access to BOTH graph structural tools (Neo4j) and vector semantic tools (Qdrant).
    If asked about a specific researcher, paper, or topic, FIRST use graph tools (like paper_neighbors or search_paper) to find the paper_id or context, 
    THEN use the vector tools (like paper_content_lookup or semantic_search) to read the actual PDF text or methodologies.
    If the user asks you to find connections between distant concepts, trace influences, or find what links two distinct entities, YOU MUST use the hippocampal_recall tool.
    You MUST execute both Graph and Vector searches if the user asks for details about a paper's content.
    If your search for ANY entity (Author, Topic, Venue, Institution, Paper, Methodology, Dataset, Metric) returns empty, you MUST assume the user made a typo and use `fuzzy_entity_resolution` to find the correct spelling before trying again.
    If BOTH your graph lookup AND fuzzy spelling check fail, it means it is not in the primary Graph metadata. You MUST gracefully fallback by using `semantic_to_graph_discovery`.
    CRITICAL RULE: DO NOT answer from your own knowledge until you have explicitly executed `semantic_to_graph_discovery`. If fuzzy fails, you MUST run semantic_to_graph_discovery before giving up!
    If the user asks about an algorithm, model, framework, or methodology (e.g. Stochastic Gradient Descent, U-Net, etc), YOU MUST prioritize using `methodology_lookup`. Do NOT jump straight to semantic search.
    If you are asked to extract new knowledge from a paper (like a specific Methodology), you should use `dynamic_graph_enrichment` to permanently add it to the Graph.
    CRITICAL RULE: DO NOT CALL THE SAME TOOL MORE THAN TWICE. Once you gather initial context and chunks, you MUST provide an answer immediately. Do not keep searching for the perfect chunk.
    CRITICAL RULE 2: DO NOT EXECUTE MULTIPLE TOOLS IN PARALLEL. You must execute exactly ONE single tool call at a time.""")
    
    response = agent.invoke({"messages": [sys_msg, HumanMessage(content=query)]}, {"recursion_limit": 40})
    
    graph_ev = []
    vector_ev = []
    queries = []
    
    for msg in response["messages"]:
        if msg.type == "tool":
            if msg.name in [t.name for t in GRAPH_TOOLS]:
                graph_ev.append({msg.name: msg.content})
                queries.append(msg.name)
            else:
                vector_ev.append({msg.name: msg.content})
            
    
    tool_calls = []
    for msg in response["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({"name": tc.get("name", ""), "args": tc.get("args", {})})
                
    return {"graph_evidence": graph_ev, "vector_evidence": vector_ev, "graph_queries": queries, "tool_calls": tool_calls}
