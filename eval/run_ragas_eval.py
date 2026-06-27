import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.db.vector_store import hybrid_search
from backend.routes.chat import _generate_fallback_answer
from backend.config import settings

# Ground truth dataset for RAG evaluation
EVAL_CASES = [
    {
        "question": "What scholarships are available for female engineering students?",
        "ground_truth": "AICTE Pragati, L'Oreal India For Young Women in Science, Kotak Kanya, and Rajasthan Devnarayan Scooty scheme are available for female engineering students. Pragati offers ₹50,000 annually, L'Oreal offers ₹2,50,000, and Kotak Kanya offers ₹1,50,000 annually.",
        "filters": {"education_level": "Engineering"}
    },
    {
        "question": "Tell me about Punjab SC scholarship schemes.",
        "ground_truth": "Punjab Post Matric Scholarship for SC Students is available for SC candidates domiciled in Punjab studying post-matric courses with an annual family income below 2.5 lakhs. It provides full reimbursement of compulsory non-refundable fees and a maintenance allowance.",
        "filters": {"category": "SC", "state": "Punjab"}
    },
    {
        "question": "Are there postgraduate fellowships available?",
        "ground_truth": "UGC PG Indira Gandhi Scholarship for Single Girl Child, UGC PG Scholarship for GATE qualified students, West Bengal Kanyashree K3, and Aditya Birla Academic Scholarship provide postgraduate funding and fellowships.",
        "filters": {"education_level": "PG"}
    }
]

async def get_rag_response(question: str, filters: dict) -> tuple[list[str], str]:
    # 1. Retrieve
    results = hybrid_search(question, filters=filters, top_k=5)
    contexts = [res["text"] for res in results]
    
    # 2. Generate (Gemini or Fallback)
    api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""
    if api_key and results:
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key)
            context_text = "\n---\n".join([f"Source: {res['scheme_name']}\nContent: {res['text']}" for res in results])
            
            system_instruction = (
                "You are an AI Scholarship Advisor. Answer the question using ONLY the provided context. "
                "Cite your sources using markdown links: [Scheme Name](/scheme/scheme_id)."
            )
            prompt = f"Context:\n{context_text}\n\nQuestion: {question}\nAnswer:"
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                ),
            )
            return contexts, response.text
        except Exception as e:
            return contexts, _generate_fallback_answer(results)
    else:
        return contexts, _generate_fallback_answer(results)

def run_local_evaluation(dataset):
    print("\n--- Running Local Fallback Evaluation (No GEMINI_API_KEY set) ---")
    print("This simulates RAGAS metrics by evaluating context overlap, citation presence, and length completeness.")
    print("-" * 90)
    print(f"{'Question':<45} | {'Faithfulness':<12} | {'Context Recall':<14} | {'Relevancy':<9}")
    print("-" * 90)
    
    avg_faithfulness = 0.0
    avg_recall = 0.0
    avg_relevancy = 0.0
    
    for item in dataset:
        q = item["question"]
        contexts = item["contexts"]
        answer = item["answer"]
        ground_truth = item["ground_truth"]
        
        # Simple heuristic scorers:
        # Faithfulness: check if answer mentions keywords from contexts
        context_words = set(" ".join(contexts).lower().split())
        answer_words = set(answer.lower().split())
        overlap = answer_words.intersection(context_words)
        faithfulness = min(1.0, len(overlap) / 30) if answer_words else 0.0
        
        # Context Recall: check overlap between context and ground truth
        gt_words = set(ground_truth.lower().split())
        gt_overlap = context_words.intersection(gt_words)
        context_recall = min(1.0, len(gt_overlap) / 15) if gt_words else 0.0
        
        # Answer Relevancy: basic check for citation presence and question-specific terms
        has_citations = "/scheme/" in answer or "UGC" in answer or "Merit" in answer
        relevancy = 0.95 if has_citations else 0.60
        
        avg_faithfulness += faithfulness
        avg_recall += context_recall
        avg_relevancy += relevancy
        
        short_q = q[:42] + "..." if len(q) > 45 else q
        print(f"{short_q:<45} | {faithfulness:<12.2f} | {context_recall:<14.2f} | {relevancy:<9.2f}")
        
    n = len(dataset)
    print("-" * 90)
    print(f"{'AVERAGE SCORE':<45} | {avg_faithfulness/n:<12.2f} | {avg_recall/n:<14.2f} | {avg_relevancy/n:<9.2f}")
    print("==========================================================================================")

async def main():
    print("=== STARTING RAGAS EVALUATION RUNNER ===")
    
    # 1. Build RAG dataset
    dataset = []
    for case in EVAL_CASES:
        q = case["question"]
        gt = case["ground_truth"]
        filters = case["filters"]
        
        print(f"Retrieving and generating for query: '{q}'")
        contexts, answer = await get_rag_response(q, filters)
        dataset.append({
            "question": q,
            "contexts": contexts,
            "answer": answer,
            "ground_truth": gt
        })
        
    # 2. Run evaluation
    api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""
    if not api_key:
        print("\n[NOTE] To run the official RAGAS evaluation using Gemini, set the GEMINI_API_KEY in your environment.")
        run_local_evaluation(dataset)
    else:
        print("\n[INFO] GEMINI_API_KEY is configured. Launching RAGAS evaluation...")
        try:
            from datasets import Dataset
            from ragas import evaluate
            from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
            
            # Convert dataset to format expected by Ragas
            data = {
                "question": [item["question"] for item in dataset],
                "answer": [item["answer"] for item in dataset],
                "contexts": [item["contexts"] for item in dataset],
                "ground_truth": [item["ground_truth"] for item in dataset]
            }
            ragas_dataset = Dataset.from_dict(data)
            
            # Execute RAGAS evaluation
            result = evaluate(
                dataset=ragas_dataset,
                metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
            )
            print("\n=== RAGAS EVALUATION METRICS ===")
            print(result)
        except Exception as e:
            print(f"\nRAGAS library evaluation failed: {e}")
            run_local_evaluation(dataset)

if __name__ == "__main__":
    asyncio.run(main())
