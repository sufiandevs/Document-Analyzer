"""
Evaluation Script for RAG System

Run: python evaluation/evaluate.py
"""
import json
import requests
import time
from typing import List, Dict

API_URL = "http://localhost:8000"

def load_dataset(path: str = "evaluation/evaluation_dataset.json") -> List[Dict]:
    with open(path, "r") as f:
        data = json.load(f)
    return data["questions"]

def evaluate_retrieval(question: str, expected_source: str) -> Dict:
    """Evaluate retrieval quality."""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"question": question},
            timeout=30
        )
        result = response.json()
        
        citations = result.get("citations", [])
        retrieval_score = result.get("retrieval_score", 0)
        
        # Check if expected source is in citations
        source_found = any(
            cite.get("document") == expected_source 
            for cite in citations
        ) if expected_source else False
        
        return {
            "retrieval_score": retrieval_score,
            "source_found": source_found,
            "citation_count": len(citations),
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

def evaluate_generation(question: str, expected_answer: str, actual_answer: str) -> Dict:
    """Evaluate answer quality using simple string matching."""
    expected_lower = expected_answer.lower()
    actual_lower = actual_answer.lower()
    
    # Check for key terms
    key_terms = expected_lower.split()
    matches = sum(1 for term in key_terms if term in actual_lower)
    term_coverage = matches / len(key_terms) if key_terms else 0
    
    # Check if answer contains expected content
    contains_answer = any(
        phrase in actual_lower 
        for phrase in [expected_lower, expected_lower[:20]]
    )
    
    return {
        "term_coverage": term_coverage,
        "contains_expected": contains_answer,
        "faithfulness": term_coverage > 0.5
    }

def run_evaluation():
    questions = load_dataset()
    results = []
    
    print("=" * 60)
    print("RAG SYSTEM EVALUATION")
    print("=" * 60)
    
    for q in questions:
        print(f"\n[{q['id']}] {q['category'].upper()}: {q['question'][:60]}...")
        
        try:
            response = requests.post(
                f"{API_URL}/chat",
                json={"question": q["question"]},
                timeout=60
            )
            result = response.json()
            
            # Evaluate
            retrieval = evaluate_retrieval(q["question"], q.get("expected_source"))
            generation = evaluate_generation(
                q["question"], 
                q["expected_answer"], 
                result.get("answer", "")
            )
            
            eval_result = {
                "id": q["id"],
                "category": q["category"],
                "question": q["question"],
                "expected": q["expected_answer"],
                "actual": result.get("answer", ""),
                "retrieval_score": retrieval.get("retrieval_score", 0),
                "source_found": retrieval.get("source_found", False),
                "faithfulness": generation["faithfulness"],
                "term_coverage": generation["term_coverage"],
                "success": True
            }
            
            print(f"  Score: {eval_result['retrieval_score']:.2f} | "
                  f"Source: {'✓' if eval_result['source_found'] else '✗'} | "
                  f"Faithful: {'✓' if eval_result['faithfulness'] else '✗'}")
            
        except Exception as e:
            eval_result = {
                "id": q["id"],
                "error": str(e),
                "success": False
            }
            print(f"  ERROR: {e}")
        
        results.append(eval_result)
        time.sleep(1)  # Rate limiting
    
    # Summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    
    total = len(results)
    successful = sum(1 for r in results if r.get("success"))
    avg_score = sum(r.get("retrieval_score", 0) for r in results if r.get("success")) / successful if successful else 0
    sources_found = sum(1 for r in results if r.get("source_found"))
    faithful = sum(1 for r in results if r.get("faithfulness"))
    
    print(f"Total Questions: {total}")
    print(f"Successful: {successful}/{total}")
    print(f"Avg Retrieval Score: {avg_score:.3f}")
    print(f"Sources Found: {sources_found}/{total}")
    print(f"Faithful Answers: {faithful}/{total}")
    
    # Save results
    with open("evaluation/results.json", "w") as f:
        json.dump({
            "summary": {
                "total": total,
                "successful": successful,
                "avg_score": avg_score,
                "sources_found": sources_found,
                "faithful": faithful
            },
            "results": results
        }, f, indent=2)
    
    print("\nResults saved to evaluation/results.json")

if __name__ == "__main__":
    run_evaluation()