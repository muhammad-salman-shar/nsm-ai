import re

NAME_PATTERNS = [
    re.compile(r"\bmy name is (\w+)", re.I),
    re.compile(r"\bcall me (\w+)", re.I),
]
AGE_PATTERNS = [
    re.compile(r"\bi am (\d+) years? old", re.I),
    re.compile(r"\bi'm (\d+) years? old", re.I),
    re.compile(r"\bmy age is (\d+)", re.I),
]
LOCATION_PATTERNS = [
    re.compile(r"\bi live in (\w+)", re.I),
    re.compile(r"\bi am from (\w+)", re.I),
]
INTRO_PATTERN = re.compile(r"^i am (\w+)$", re.I)

ADJECTIVES = {
    "happy","sad","angry","tired","hungry","thirsty","beautiful","ugly",
    "big","small","tall","short","good","bad","fine","okay","ok","great",
    "bored","excited","scared","afraid","sleepy","sick","healthy",
    "smart","dumb","kind","rude","funny","serious","young","old",
    "human","male","female","boy","girl","man","woman","child","adult",
    "animal","person","student","teacher","here","there","ready","done",
}

NAME_QUERY = re.compile(r"\bwhat(?:'s| is| was) my name\b", re.I)
AGE_QUERY = re.compile(r"\bhow old am i\b", re.I)
LOCATION_QUERY = re.compile(r"\bwhere (?:do i live|am i from)\b", re.I)


class FactStore:
    def __init__(self):
        self.facts = {}

    def set(self, key, value):
        self.facts[key] = value

    def get(self, key):
        return self.facts.get(key)

    def has(self, key):
        return key in self.facts


def extract(text):
    for pat in NAME_PATTERNS:
        m = pat.search(text)
        if m:
            return ("name", m.group(1).strip().capitalize())

    for pat in AGE_PATTERNS:
        m = pat.search(text)
        if m:
            return ("age", int(m.group(1)))

    for pat in LOCATION_PATTERNS:
        m = pat.search(text)
        if m:
            return ("location", m.group(1).strip().capitalize())

    m = INTRO_PATTERN.search(text.strip())
    if m:
        word = m.group(1).lower()
        if word not in ADJECTIVES:
            return ("name", m.group(1).capitalize())

    return None


def query(text):
    if NAME_QUERY.search(text):
        return "name"
    if AGE_QUERY.search(text):
        return "age"
    if LOCATION_QUERY.search(text):
        return "location"
    return None


def format_answer(key, value):
    if key == "name":
        return f"Your name is {value}."
    if key == "age":
        return f"You are {value} years old."
    if key == "location":
        return f"You live in {value}."
    return f"{key}: {value}"
