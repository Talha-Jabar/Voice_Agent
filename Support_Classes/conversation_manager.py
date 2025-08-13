class ConversationManager:
    def __init__(self):
        self.history = []

    def add_message(self, speaker, text):
        self.history.append({"speaker": speaker, "text": text})

    def get_history(self):
        return self.history

    def get_summary(self):
        # This is a placeholder for more sophisticated summarization logic
        # In a real application, this would involve LLM calls to summarize
        # sentiment, extract complaints, etc.
        full_history_text = "\n".join([f"{msg['speaker']}: {msg['text']}" for msg in self.history])

        # Dummy sentiment and complaint detection for demonstration
        sentiment = "neutral"
        if any(word in full_history_text.lower() for word in ["unhappy", "bad", "problem", "issue"]):
            sentiment = "negative"
        elif any(word in full_history_text.lower() for word in ["happy", "good", "satisfied"]):
            sentiment = "positive"

        complaint = ""
        if "complaint" in full_history_text.lower() or "issue" in full_history_text.lower():
            complaint = "Customer expressed an issue/complaint."

        short_summary = full_history_text[-200:] # Last 200 characters as a short summary

        return {
            "history": full_history_text,
            "sentiment": sentiment,
            "complaint": complaint,
            "short_summary": short_summary
        }


