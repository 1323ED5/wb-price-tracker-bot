

def text_ellipsis(text: str, max_length: int = 40) -> str:
    if len(text) <= max_length:
        return text

    return text[:max_length - 3] + "..."
