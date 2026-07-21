from typing import TypedDict, List, Dict, Any
from operator import add
from typing_extensions import Annotated

class AgentState(TypedDict):
    """The State of the LangGraph Hybrid GraphRAG Assistant."""
    
    query: str
    route: str  
    
  
    graph_queries: Annotated[List[str], add] 
    
 
    graph_evidence: Annotated[List[Dict[str, Any]], add]
    vector_evidence: Annotated[List[Dict[str, Any]], add]
    metadata_evidence: Annotated[List[Dict[str, Any]], add]
    tool_calls: Annotated[List[Dict[str, Any]], add]
    

    evidence_package: str
    

    final_answer: str
    confidence: str  
