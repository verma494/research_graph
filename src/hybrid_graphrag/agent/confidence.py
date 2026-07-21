from .state import AgentState

def evaluate_confidence(state: AgentState) -> AgentState:
    graph_ev = state.get("graph_evidence", [])
    vector_ev = state.get("vector_evidence", [])
    route = state.get("route", "GENERAL")
    
    if route == "GENERAL":
        return {"confidence": "HIGH (General Knowledge)"}
        
    if graph_ev and vector_ev:
        return {"confidence": "HIGH"}
    elif graph_ev or vector_ev:
        return {"confidence": "MEDIUM"}
    else:
        return {"confidence": "LOW"}
