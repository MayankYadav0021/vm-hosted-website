def chunk_text(text, source, size=1200, overlap=200):
    text = text.strip()
    if not text:
        return []
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    result = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(len(text), start + size)
        piece = text[start:end].strip()
        if piece:
            result.append({"source": source, "chunk_id": idx, "text": piece})
            idx += 1
        if end == len(text):
            break
        start = end - overlap
    return result
