from src.patterns import conjugate, to_base_verb

def produce_svo(subject, verb, obj):
    """Generates a simple present-tense affirmative sentence from SVO."""
    # Capitalize 'I' and first letter of other subjects
    if subject.lower() == "i":
        subj = "I"
    else:
        subj = subject.capitalize()

    base_v = to_base_verb(verb)
    v = conjugate(base_v, subject)

    # Don't capitalize object unless it's a proper noun (like NeuraSaMu)
    return f"{subj} {v} {obj}."
