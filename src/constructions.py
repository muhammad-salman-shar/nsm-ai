# L7: Form-Meaning Pairs (Construction Grammar)

CONSTRUCTIONS = [
    {
        "id": "IS_A",
        "form": "[SUBJ] is a/an [OBJ]",
        "meaning": ("IS_A", "{SUBJ}", "{OBJ}"),
        "pos": {"SUBJ": "noun", "OBJ": "noun"}
    },
    {
        "id": "IS_PROP",
        "form": "[SUBJ] is [ADJ]",
        "meaning": ("IS_PROP", "{SUBJ}", "{ADJ}"),
        "pos": {"SUBJ": "noun", "ADJ": "adj"}
    },
    {
        "id": "SVO",
        "form": "[SUBJ] [VERB] [OBJ]",
        "meaning": ("SVO", "{SUBJ}", "{VERB}", "{OBJ}"),
        "pos": {"SUBJ": "noun", "VERB": "verb", "OBJ": "noun"}
    },
    {
        "id": "NOT_IS_A",
        "form": "[SUBJ] is not a/an [OBJ]",
        "meaning": ("NOT_IS_A", "{SUBJ}", "{OBJ}"),
        "pos": {"SUBJ": "noun", "OBJ": "noun"}
    },
    {
        "id": "Q_IS_A",
        "form": "Is [SUBJ] a/an [OBJ]?",
        "meaning": ("Q_IS_A", "{SUBJ}", "{OBJ}"),
        "pos": {"SUBJ": "noun", "OBJ": "noun"}
    }
]
