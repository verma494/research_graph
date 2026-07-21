from langgraph.graph import StateGraph, END
from .state import AgentState
from .router import route_query
from .graph_agent import execute_graph_agent
from .vector_agent import execute_vector_agent
from .hybrid_agent import execute_hybrid_agent
from .evidence_builder import build_evidence
from .answer_generator import generate_answer
from .confidence import evaluate_confidence

def create_workflow():
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("router", route_query)
    workflow.add_node("graph", execute_graph_agent)
    workflow.add_node("vector", execute_vector_agent)
    workflow.add_node("hybrid", execute_hybrid_agent)
    workflow.add_node("evidence", build_evidence)
    workflow.add_node("answer", generate_answer)
    workflow.add_node("confidence", evaluate_confidence)
    
    # Entry Point
    workflow.set_entry_point("router")
    
    # Conditional Edges from Router
    def route_condition(state: AgentState):
        route = state["route"]
        if route == "GRAPH":
            return "graph"
        elif route == "VECTOR":
            return "vector"
        elif route == "HYBRID":
            return "hybrid"
        else: # GENERAL
            return "evidence"
            
    workflow.add_conditional_edges(
        "router",
        route_condition,
        {
            "graph": "graph",
            "vector": "vector",
            "hybrid": "hybrid",
            "evidence": "evidence"
        }
    )
    
    # Converge paths to evidence builder
    workflow.add_edge("graph", "evidence")
    workflow.add_edge("vector", "evidence")
    workflow.add_edge("hybrid", "evidence")
    
    # Final pipeline
    workflow.add_edge("evidence", "answer")
    workflow.add_edge("answer", "confidence")
    workflow.add_edge("confidence", END)
    
    return workflow.compile()
