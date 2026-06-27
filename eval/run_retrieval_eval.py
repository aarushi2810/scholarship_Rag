import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.db.vector_store import hybrid_search

def run_eval(top_k: int = 5):
    dataset_path = ROOT / "eval" / "golden_dataset.json"
    if not dataset_path.exists():
        print(f"Error: Golden dataset not found at {dataset_path}")
        sys.exit(1)
        
    with open(dataset_path) as f:
        cases = json.load(f)
        
    print(f"=== RUNNING RETRIEVAL EVALUATION (Top-{top_k}) ===")
    print(f"Loaded {len(cases)} evaluation test cases from golden_dataset.json\n")
    
    total_mrr = 0.0
    total_hits = 0
    total_precision = 0.0
    total_recall = 0.0
    
    print(f"{'Profile Description':<55} | {'Hit?':<5} | {'MRR':<5} | {'Precision':<10} | {'Recall':<6}")
    print("-" * 92)
    
    for case in cases:
        query = case["query"]
        filters = case.get("filters", {})
        expected = set(case["expected_scheme_ids"])
        desc = case.get("description", "Test case")
        
        # Run hybrid search
        results = hybrid_search(query, filters=filters, top_k=top_k)
        retrieved_ids = [res["scheme_id"] for res in results]
        
        # Compute metrics
        hit = 0
        mrr = 0.0
        relevant_retrieved = 0
        
        for rank, rid in enumerate(retrieved_ids):
            if rid in expected:
                if hit == 0:
                    hit = 1
                    mrr = 1.0 / (rank + 1)
                relevant_retrieved += 1
                
        precision = relevant_retrieved / len(retrieved_ids) if retrieved_ids else 0.0
        recall = relevant_retrieved / len(expected) if expected else 0.0
        
        total_hits += hit
        total_mrr += mrr
        total_precision += precision
        total_recall += recall
        
        # Format description to fit table
        short_desc = desc[:52] + "..." if len(desc) > 55 else desc
        print(f"{short_desc:<55} | {hit:<5} | {mrr:<5.2f} | {precision:<10.2f} | {recall:<6.2f}")
        
    num_cases = len(cases)
    avg_hit_rate = total_hits / num_cases
    avg_mrr = total_mrr / num_cases
    avg_precision = total_precision / num_cases
    avg_recall = total_recall / num_cases
    
    print("-" * 92)
    print(f"{'OVERALL AVERAGE':<55} | {avg_hit_rate:<5.2f} | {avg_mrr:<5.2f} | {avg_precision:<10.2f} | {avg_recall:<6.2f}")
    print("==========================================================")

if __name__ == "__main__":
    run_eval()
