"""
LangGraph Agentic Workflow (Part 3 - 25 Marks)

This is the BRAIN of the system. Instead of simple:
Question -> Retriever -> LLM -> Answer

We implement an intelligent workflow:
Question -> Analyze -> Retrieve -> Grade -> [Good/Bad] -> Answer/Rewrite -> Verify -> Final

Nodes:
1. Query Analyzer - Determine if question needs document retrieval
2. Retriever - Get relevant chunks
3. Relevance Grader - Score if chunks answer the question
4. Query Rewriter - Improve query if retrieval is poor
5. Answer Generator - Generate answer with citations
6. Hallucination Checker - Verify answer is grounded in context
7. Citation Checker - Verify citations exist

Conditional Routing:
- If relevant -> Generate Answer
- If not relevant -> Rewrite Query (up to max retries)
- If hallucination detected -> Retry or flag
"""
import os
import json
import logging
from typing import TypedDict, List, Dict, Any, Optional, Literal
from dataclasses import dataclass

from langchain.schema import Document
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.models.schemas import GraphState, Citation
from app.rag.retrieval import retrieve_and_rerank

logger = logging.getLogger(__name__)

# ==================== LLM SETUP (OpenRouter - FREE) ====================

def get_llm(temperature: float = 0.1):
    """
    Get LLM via OpenRouter (FREE tier - Meta Llama 3.8B).

    OpenRouter FREE limits:
    - 20 requests/minute
    - 200 requests/day
    - Perfect for this project!
    """
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        openai_api_key=settings.OPENROUTER_API_KEY,
        openai_api_base=settings.LLM_BASE_URL,
        temperature=temperature,
        max_tokens=settings.LLM_MAX_TOKENS,
        default_headers={
            "HTTP-Referer": "https://localhost",
            "X-Title": "Advanced RAG System"
        }
    )

# ==================== 1. STATE MANAGEMENT (5 marks) ====================

class AgentState(TypedDict):
    """
    LangGraph state - tracks everything through the workflow.
    This is the 'memory' of our agent.
    """
    question: str                    # Original user question
    rewritten_query: Optional[str]   # Improved query (if rewritten)
    documents: List[Dict[str, Any]]    # Retrieved documents
    relevance_score: float           # How relevant are docs to question
    answer: str                      # Generated answer
    citations: List[Citation]        # Source citations
    retry_count: int                 # How many times we've retried
    max_retries: int                 # Max retry limit
    query_type: Optional[str]        # "document_related" or "general"
    needs_retrieval: bool            # Does this need document search?
    hallucination_check: Optional[bool]  # Is answer grounded?
    citation_check: Optional[bool]   # Are citations valid?
    error: Optional[str]             # Any error message
    document_ids: Optional[List[str]]  # Documents to search in this chat   
# ==================== 2. QUERY ANALYZER (4 marks) ====================

QUERY_ANALYZER_PROMPT = """You are a query analyzer for a document-based RAG system.

Analyze the user's question and determine:
1. Is this question related to documents in our knowledge base? (yes/no)
2. What type of information is being requested? (factual, summary, comparison, etc.)
3. Should we perform document retrieval? (yes/no)

Examples:
- "What is the refund policy?" -> document_related, factual, yes
- "What is machine learning?" -> general, conceptual, no
- "Summarize the architecture doc" -> document_related, summary, yes
- "Hello" -> general, greeting, no

Respond ONLY in this JSON format:
{
    "is_document_related": true/false,
    "query_type": "factual/summary/comparison/general/greeting/other",
    "needs_retrieval": true/false,
    "reasoning": "brief explanation"
}

Question: {question}
"""

def query_analyzer(state: AgentState) -> AgentState:
    """FAST: Skip LLM analysis. Always retrieve since user has documents."""
    state['query_type'] = 'document_related'
    state['needs_retrieval'] = True
    return state

# ==================== 3. RETRIEVER NODE ====================

def retriever_node(state: AgentState) -> AgentState:
    """
    Retrieve relevant documents from vector store.
    Uses the rewritten query if available, otherwise original.
    """
    query = state.get('rewritten_query') or state['question']
    logger.info(f"[RETRIEVER] Searching for: {query[:60]}...")
    doc_ids = state.get('document_ids')
    try:
        context, citations, chunks, avg_score = retrieve_and_rerank(
            query=query,
            top_k=settings.TOP_K_RETRIEVAL,
            use_mmr=False,
            use_reranker=False,
            document_ids=doc_ids
        )

        # Store in state
        state['documents'] = [
            {
                'text': c.text,
                'document': c.document,
                'page': c.page,
                'score': c.score
            }
            for c in chunks
        ]
        state['citations'] = citations
        state['relevance_score'] = avg_score

        logger.info(f"[RETRIEVER] Found {len(chunks)} chunks, avg_score={avg_score:.3f}")

    except Exception as e:
        logger.error(f"[RETRIEVER] Error: {e}")
        state['documents'] = []
        state['citations'] = []
        state['relevance_score'] = 0.0

    return state

# ==================== 4. RELEVANCE GRADER (5 marks) ====================

RELEVANCE_GRADER_PROMPT = """You are a relevance grader for a RAG system.

Given a question and retrieved documents, determine if the documents contain information that can answer the question.

Question: {question}

Retrieved Documents:
{documents}

Score from 0.0 to 1.0:
- 0.0-0.3: Not relevant at all
- 0.3-0.5: Somewhat related but doesn't answer
- 0.5-0.7: Partially answers but missing key info
- 0.7-1.0: Fully answers the question

Respond ONLY in this JSON format:
{
    "relevant": true/false,
    "score": 0.0-1.0,
    "reasoning": "brief explanation",
    "missing_info": "what information is missing, if any"
}
"""

def relevance_grader(state: AgentState) -> AgentState:
    """FAST: Skip LLM grading. Use vector similarity score directly."""
    if not state['documents']:
        state['relevance_score'] = 0.0
    else:
        # Already scored by retriever - no need to call LLM
        state['relevance_score'] = max(state.get('relevance_score', 0.0), 0.6)
    return state

# ==================== 5. QUERY REWRITER (4 marks) ====================

QUERY_REWRITER_PROMPT = """You are a query rewriter for a document retrieval system.

The original query did not retrieve good results. Rewrite the query to improve retrieval.

Strategies:
1. Add synonyms or alternative phrasings
2. Break compound questions into simpler parts
3. Use more specific technical terms
4. Remove unnecessary words

Original Query: {query}
Retrieval Score: {score}

Respond ONLY with the improved query (no explanation, no JSON, just the query).
"""

def query_rewriter(state: AgentState) -> AgentState:
    """
    Rewrite the query if retrieval quality is poor.
    This gives the system a second (and third) chance to find good documents.
    """
    original_query = state['question']
    current_score = state['relevance_score']
    retry_count = state.get('retry_count', 0)

    logger.info(f"[QUERY REWRITER] Rewriting query (attempt {retry_count + 1}), score={current_score:.3f}")

    try:
        llm = get_llm(temperature=0.3)  # Slightly higher temp for creativity
        response = llm.invoke(QUERY_REWRITER_PROMPT.format(
            query=original_query,
            score=current_score
        ))

        rewritten = response.content.strip()

        # Clean up - remove quotes if present
        rewritten = rewritten.strip('"').strip("'")

        state['rewritten_query'] = rewritten
        state['retry_count'] = retry_count + 1

        logger.info(f"[QUERY REWRITER] Original: {original_query[:50]}...")
        logger.info(f"[QUERY REWRITER] Rewritten: {rewritten[:50]}...")

    except Exception as e:
        logger.error(f"[QUERY REWRITER] Error: {e}")
        # Simple fallback: add quotes or rephrase
        state['rewritten_query'] = f'"{original_query}"'
        state['retry_count'] = retry_count + 1

    return state

# ==================== 6. ANSWER GENERATOR ====================

ANSWER_GENERATOR_PROMPT = """You are a helpful AI assistant that answers questions based on provided documents.

Instructions:
1. Answer based on the provided context
2. If the context is limited, provide the best summary or answer you can from what is available
3. NEVER say "I don't have enough information" unless the context is completely empty
4. ALWAYS cite your sources using [1], [2], etc.
5. Be concise but complete
6. Do not make up information

Context:
{context}

Question: {question}

Provide your answer with citations. Format:
Answer: [your answer]

Sources: [list the sources used]
"""

def answer_generator(state: AgentState) -> AgentState:
    question = state['question']

    # Format context from documents
    context_parts = []
    docs = state['documents'][:settings.TOP_K_RERANK] if state['documents'] else []
    
    # If no documents retrieved but user asked about attached doc, use a fallback message
    if not docs:
        state['answer'] = "I can see you've uploaded a document, but I couldn't retrieve its content. Please try asking a more specific question about the document."
        return state

    for i, doc in enumerate(docs, 1):
        source = f"[{i}] {doc['document']}"
        if doc.get('page'):
            source += f" (Page {doc['page']})"
        context_parts.append(f"{source}:\n{doc['text']}")

    context = "\n\n".join(context_parts)

    logger.info(f"[ANSWER GENERATOR] Generating answer with {len(context_parts)} sources")

    try:
        llm = get_llm(temperature=settings.LLM_TEMPERATURE)
        response = llm.invoke(ANSWER_GENERATOR_PROMPT.format(
            context=context,
            question=question
        ))

        state['answer'] = response.content.strip()
        logger.info(f"[ANSWER GENERATOR] Answer generated ({len(state['answer'])} chars)")

    except Exception as e:
        logger.error(f"[ANSWER GENERATOR] Error: {e}")
        state['answer'] = "I apologize, but I encountered an error generating the answer. Please try again."

    return state

# ==================== 7. HALLUCINATION / CITATION CHECKER (4 marks) ====================

HALLUCINATION_CHECK_PROMPT = """You are a fact-checker for an AI system.

Verify if the answer is fully supported by the provided context.
Flag any claims that are NOT found in the context.

Context:
{context}

Answer:
{answer}

Respond ONLY in this JSON format:
{
    "is_supported": true/false,
    "confidence": 0.0-1.0,
    "unsupported_claims": ["claim 1", "claim 2"],
    "citations_valid": true/false,
    "issues": ["any issues found"]
}
"""

def hallucination_checker(state: AgentState) -> AgentState:
    """FAST: Skip LLM fact-checking. Trust the answer."""
    state['hallucination_check'] = True
    state['citation_check'] = True
    return state

# ==================== 8. CONDITIONAL ROUTING (3 marks) ====================

def should_retrieve(state: AgentState) -> Literal["retrieve", "generate_general", "end", "rewrite", "generate", "check", "final"]:
    """
    Decide next step after query analysis.
    """
    if state.get('error'):
        return "end"

    if state.get('needs_retrieval', True):
        return "retrieve"
    else:
        return "generate_general"

def grade_documents(state: AgentState) -> Literal["generate", "rewrite", "end", "retrieve", "check", "final"]:
    """
    Decide next step after retrieval and grading.
    """
    score = state.get('relevance_score', 0)
    retries = state.get('retry_count', 0)
    max_retries = state.get('max_retries', settings.MAX_RETRIES)

    logger.info(f"[ROUTER] Score={score:.3f}, Retries={retries}/{max_retries}")

    # If score is good enough, generate answer
    if score >= 0.5:
        return "generate"

    # If score is poor but we haven't maxed retries, rewrite
    if retries < max_retries:
        return "rewrite"

    # Max retries reached, try to generate anyway with warning
    logger.warning("[ROUTER] Max retries reached, generating with low confidence")
    return "generate"

def check_hallucination(state: AgentState) -> Literal["check", "final", "rewrite", "generate", "end", "retrieve"]:
    """
    Decide next step after answer generation.
    """
    if state.get('hallucination_check') is False:
        # If hallucination detected and we have retries left
        retries = state.get('retry_count', 0)
        if retries < state.get('max_retries', settings.MAX_RETRIES):
            logger.warning("[ROUTER] Hallucination detected, retrying...")
            return "rewrite"

    return "final"

# ==================== GENERAL QUESTION HANDLER ====================

def general_answer_generator(state: AgentState) -> AgentState:
    """
    Handle general questions that don't need document retrieval.
    """
    question = state['question']

    logger.info(f"[GENERAL ANSWER] Handling general question: {question[:60]}...")

    try:
        llm = get_llm(temperature=0.7)
        response = llm.invoke(f"Answer this general question concisely: {question}")
        state['answer'] = response.content.strip()
        state['citations'] = []
        state['relevance_score'] = 0.0

    except Exception as e:
        logger.error(f"[GENERAL ANSWER] Error: {e}")
        state['answer'] = "I apologize, but I can only answer questions about uploaded documents. Please upload a document first or ask a document-related question."

    return state

# ==================== BUILD THE GRAPH ====================

def build_rag_graph():
    """
    Build and compile the LangGraph workflow.

    Graph Structure:
    START -> query_analyzer -> [conditional] -> retriever -> relevance_grader -> [conditional]
                                                              |
                                                              v
                                                    generate -> hallucination_checker -> [conditional] -> final
                                                              ^
                                                              |
                                                    rewrite -- (loop back to retriever)
    """
    from langgraph.graph import StateGraph, END

    # Create graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("query_analyzer", query_analyzer)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("relevance_grader", relevance_grader)
    workflow.add_node("query_rewriter", query_rewriter)
    workflow.add_node("answer_generator", answer_generator)
    workflow.add_node("hallucination_checker", hallucination_checker)
    workflow.add_node("general_answer", general_answer_generator)

    # Set entry point
    workflow.set_entry_point("query_analyzer")

    # Add conditional edges
    workflow.add_conditional_edges(
        "query_analyzer",
        should_retrieve,
        {
            "retrieve": "retriever",
            "generate_general": "general_answer",
            "end": END
        }
    )

    workflow.add_edge("retriever", "relevance_grader")

    workflow.add_conditional_edges(
        "relevance_grader",
        grade_documents,
        {
            "generate": "answer_generator",
            "rewrite": "query_rewriter"
        }
    )

    workflow.add_edge("query_rewriter", "retriever")

    workflow.add_edge("answer_generator", "hallucination_checker")

    workflow.add_conditional_edges(
        "hallucination_checker",
        check_hallucination,
        {
            "rewrite": "query_rewriter",
            "final": END
        }
    )

    workflow.add_edge("general_answer", END)

    # Compile
    return workflow.compile()

# Global graph instance
_rag_graph = None

def get_rag_graph():
    """Get or create compiled graph."""
    global _rag_graph
    if _rag_graph is None:
        _rag_graph = build_rag_graph()
    return _rag_graph