from typing import List, Dict, Any


def _format_chunks(chunks: List[Dict[str, Any]]) -> str:
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        lines.append(
            "\n".join(
                [
                    f"[Chunk {i}]",
                    f"ticker: {chunk.get('ticker')}",
                    f"doc_type: {chunk.get('doc_type')}",
                    f"filing_date: {chunk.get('filing_date')}",
                    f"section_name: {chunk.get('section_name')}",
                    f"chunk_order: {chunk.get('chunk_order')}",
                    f"similarity: {chunk.get('similarity')}",
                    f"text: {chunk.get('chunk_text')}",
                ]
            )
        )
    return "\n\n".join(lines)


def build_risk_summary_prompt(
    ticker: str,
    year: int,
    question: str,
    chunks: List[Dict[str, Any]],
) -> str:
    context_block = _format_chunks(chunks)

    return f"""
You are a financial filings analyst.

Your task is to answer the user's question about {ticker}'s {year} 10-K risk disclosures using ONLY the retrieved context below.

Instructions:
- Use only the supplied context.
- Do not use outside knowledge.
- If the context is insufficient, say so clearly.
- Focus on the most material risks and explain them plainly.
- Prefer evidence from the retrieved text over general interpretation.
- When useful, reference the relevant doc_type or section_name in prose.
- Keep the answer concise but specific.

User question:
{question}

Retrieved context:
{context_block}

Return:
- A short direct answer first.
- Then 3-6 bullet points covering the main risks or takeaways.
""".strip()