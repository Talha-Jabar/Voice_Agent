def detect_termination_intent(text: str) -> bool:
    termination_keywords = ["goodbye", "bye", "end call", "hang up", "that's all", "no more"]
    return any(keyword in text.lower() for keyword in termination_keywords)


