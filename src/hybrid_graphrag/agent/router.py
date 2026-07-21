from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from .state import AgentState
from ..logging import logger

router_prompt = PromptTemplate.from_template("""
You are the routing brain of a Hybrid GraphRAG Research Assistant.
Given the user query, classify it into exactly one of these 4 categories:

1. GENERAL: The user is saying hello, asking who you are, or asking general knowledge questions (e.g. "What is AI?", "tell me a joke"). No database retrieval is needed.
2. GRAPH: The user is asking about structured relationships, authors, institutions, citation counts, collaborators, or venues. (e.g. "Who wrote paper X?", "Who collaborates with author Y?")
3. VECTOR: The user is asking about the deep text content, methodology, summaries, or results of papers. (e.g. "Explain the methodology of GraphRAG", "Summarize the findings.")
4. HYBRID: The user is asking a complex question requiring BOTH structured graph traversals AND deep text content. (e.g. "What methodology did Stanford researchers use?", "Which papers cite X and what do they conclude?")

User Query: {query}

Reply with exactly one word: GENERAL, GRAPH, VECTOR, or HYBRID.
""")

def route_query(state: AgentState) -> AgentState:
    query = state["query"]
    logger.info(f"Routing query: {query}")
    
    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        chain = router_prompt | llm
        result = chain.invoke({"query": query}).content.strip().upper()
        
        # Clean up any trailing punctuation
        result = "".join(c for c in result if c.isalpha())
        
        if result not in ["GENERAL", "GRAPH", "VECTOR", "HYBRID"]:
            logger.warning(f"Invalid route generated: {result}. Defaulting to GENERAL.")
            result = "GENERAL"
            
    except Exception as e:
        logger.error(f"Error in router: {e}. Defaulting to GENERAL.")
        result = "GENERAL"
        
    logger.info(f"Routed to: {result}")
    return {"route": result}
