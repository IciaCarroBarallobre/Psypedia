"""Format retrieved cards as context, independently of storage and model providers."""

def build_context(topics: list[dict]) -> str:
    """Render only the cards selected by the application service."""
    cards = []
    for topic in topics:
        spanish_name = next((alias for alias in topic.get("aliases", [])
                             if alias.startswith(("terapia ", "psicología "))), None)
        label = topic["name"]
        if spanish_name:
            label += f"\nSpanish name from metadata: {spanish_name}"
        cards.append(f"{label}\n{topic['summary']}")
    return "<knowledge_cards>\n" + "\n\n".join(cards) + "\n</knowledge_cards>"
