import argparse
import json
import os
from typing import Any, Dict, List
from openai import OpenAI
from .prompts import build_risk_summary_prompt
from .retrieve import retrieve_chunks


ANSWER_MODEL = os.getenv("OPENAI_ANSWER_MODEL", "gpt-4.1-mini")
MIN_SIMILARITY = float(os.getenv("RAG_MIN_SIMILARITY", "0"))  # e.g., 0.3 later

def get_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def summarize_ten_k_risks(ticker: str, year: int, question: str, limit: int = 8) -> Dict[str, Any]:
    chunks = retrieve_chunks(
        query_text=question,
        ticker=ticker,
        year=year,
        doc_types=["10-K", "risk_factor"],
        limit=limit,
        min_similarity=MIN_SIMILARITY if MIN_SIMILARITY > 0 else None,
    )

    retrieval_summary = {
        "ticker": ticker, 
        "year": year, 
        "question": question, 
        "requested_limit": limit, 
        "returned_chunks": len(chunks),
        "top_similarity": max((c["similarity"] for c in chunks), default=None),
        "doc_types": sorted(list({c["doc_type"] for c in chunks})) if chunks else [],
    }

    if not chunks:
        return {
            "answer": None,
            "chunks": [],
            "retrieval_summary": retrieval_summary,
        }
    client = get_client()
    prompt = build_risk_summary_prompt(
        ticker=ticker,
        year=year,
        question=question,
        chunks=chunks,
    )

    resp = client.responses.create(
        model=ANSWER_MODEL,
        input=prompt,
    )

    answer = resp.output_text
    return {
        "answer": answer,
        "chunks": chunks,
        "retrieval_summary": retrieval_summary,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker")
    parser.add_argument("year", type=int)
    parser.add_argument("question")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--show-chunks", action="store_true")
    args = parser.parse_args()

    result = summarize_ten_k_risks(
        ticker=args.ticker,
        year=args.year,
        question=args.question,
        limit=args.limit,
    )

    if args.show_chunks: 
        chunks = result["chunks"]
        print(f"Retrieved {len(chunks)} chunks")
        for i, c in enumerate(chunks, start=1):
            preview = (c["chunk_text"] or "")[:160].replace("\n", " ")
            sim = c.get("similarity")
            sim_str = f"{sim:.3f}" if sim is not None else "None"
            print(
                f"[{i}] doc_type={c['doc_type']} "
                f"date={c['filing_date']} "
                f"section={c['section_name']} "
                f"sim={sim_str} "
                f"order={c['chunk_order']} "
                f"text='{preview}...'"
            )
    print(json.dumps(result, default=str, indent=2))


if __name__ == "__main__":
    main()