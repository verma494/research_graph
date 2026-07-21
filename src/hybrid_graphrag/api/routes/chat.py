from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from ...agent.workflow import create_workflow

router = APIRouter()

# Instantiate workflow once per app lifecycle
try:
    app_workflow = create_workflow()
except Exception as e:
    app_workflow = None

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    confidence: str
    route: str
    sources: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]] = []

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    if not app_workflow:
        raise HTTPException(status_code=500, detail="LangGraph workflow not initialized. Check API keys.")
        
    try:
        final_state = app_workflow.invoke({
            "query": request.message,
            "route": "",
            "graph_queries": [],
            "graph_evidence": [],
            "vector_evidence": [],
            "metadata_evidence": [],
            "evidence_package": "",
            "final_answer": "",
            "confidence": "",
            "tool_calls": []
        })
        
        # Build sources array from graph/vector evidence
        sources = []
        if final_state.get("graph_evidence"):
            sources.extend(final_state["graph_evidence"])
        if final_state.get("vector_evidence"):
            sources.extend(final_state["vector_evidence"])
        
        tool_calls_list = final_state.get("tool_calls", [])

        return ChatResponse(
            answer=final_state.get("final_answer", ""),
            confidence=final_state.get("confidence", "LOW"),
            route=final_state.get("route", "GENERAL"),
            sources=sources,
            tool_calls=tool_calls_list
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Fallback to pure LLM answering instead of internal error as per instructions:
        # "Never expose internal failures. Answer naturally."
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
        try:
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
            fallback_answer = llm.invoke([HumanMessage(content=request.message)]).content
            return ChatResponse(
                answer=fallback_answer,
                confidence="LOW (Fallback)",
                route="GENERAL",
                sources=[]
            )
        except Exception:
            # Absolute worst-case scenario
            return ChatResponse(
                answer="I apologize, but I am currently experiencing technical difficulties retrieving information.",
                confidence="LOW",
                route="ERROR",
                sources=[]
            )
