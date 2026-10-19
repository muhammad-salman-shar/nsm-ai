import re

def split_sentences(text):
    """
    Splits a large block of text into individual sentences.
    Handles periods, question marks, exclamation marks, and newlines.
    """
    # Split by newline, or punctuation followed by space/end
    sentences = re.split(r'(?<=[.!?])\s+|\n+', text.strip())
    # Remove empty strings and extra spaces
    return [s.strip() for s in sentences if s.strip()]
