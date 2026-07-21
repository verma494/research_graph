from .state import AgentState
import json

def build_evidence(state: AgentState) -> AgentState:
    package = "## RAW RETRIEVAL EVIDENCE\n\n"
    
    graph_ev = state.get("graph_evidence", [])
    if graph_ev:
        package += "### Graph Evidence\n"
        for item in graph_ev:
            package += f"- {json.dumps(item)}\n"
            
    vector_ev = state.get("vector_evidence", [])
    if vector_ev:
        package += "\n### Vector Evidence\n"
        for item in vector_ev:
            package += f"- {json.dumps(item)}\n"
            
    if not graph_ev and not vector_ev:
        package += "No database evidence found.\n"
        
    return {"evidence_package": package}
