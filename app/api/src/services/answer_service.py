def build_grounded_answer(question: str, chunks: list[dict]) -> str:
    if not chunks:
        return (
            "I could not find enough grounded source material for that ticker yet. "
            "Try another ticker or refresh the corpus."
        )

    excerpt_lines = []
    for chunk in chunks[:3]:
        text = chunk["chunk_text"].strip().replace("\n", " ")
        excerpt_lines.append(f"- {text[:220]}")

    joined = "\n".join(excerpt_lines)
    return (
        f"Question: {question}\n\n"
        f"Grounded take based on the latest retrieved source chunks:\n"
        f"{joined}\n\n"
        f"This is a placeholder synthesis. Next, replace this function with your LLM-based answer "
        f"generation layer while preserving citations and grounding rules."
    )