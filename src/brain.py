import re
from src.affect import Affect
from src.personality import Personality
from src.memory import Lexicon, EpisodicMemory
from src.perceptron import Perceptron, TRAINING_DATA
from src.language import Language
from src.relations import (extract, parse_query, RelationStore,
                           CORRECTION_MARKERS, NOUN_DETERMINERS, STOP_TAIL, AUX_VERBS)
from src import persistence
from src.facts import extract as extract_fact, query as fact_query, format_answer, FactStore
from src.producer import produce_svo
from src.composer import compose_object
from src.reasoner import infer_relation
from src.parser_v2 import parse_to_meaning
from src.realizer import realize, get_article
from src.llm_teacher import improve_language
from src.patterns import is_svo_verb
from src.morphology import conjugate_verb

MATH_WORDS = {"zero":0,"one":1,"two":2,"three":3,"four":4,
              "five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}

DEFAULT_MAX_DEPTH = 5
HARD_MAX_DEPTH = 8

_GRAMMAR = {
    "a","an","the","is","are","am","was","were","be","been","being",
    "i","you","we","they","he","she","it","me","my","your","our","their","its",
    "to","of","in","on","at","for","with","by","from","about","into",
    "and","or","but","if","then","so","because","as","than","also","too",
    "do","does","did","done","have","has","had",
    "will","would","can","could","should","may","might","must","shall",
    "what","who","why","how","when","where","which","whose",
    "this","that","these","those","there","here",
    "not","no","yes","ok","okay","sure","please",
    "hi","hello","hey","bye","goodbye","greetings",
    "thanks","thank","nevermind","never","skip","cancel",
    "forget","stop","quit","whatever","nothing","later","fine",
    "one","two","three","four","five","six","seven","eight","nine","ten","zero",
    "plus","minus","times","multiplied","divided",
}

_COMMON_VERBS = {
    "saw","see","seen","look","looked","looks",
    "go","went","gone","goes","come","came","comes",
    "say","said","says","tell","told","tells",
    "make","made","makes","get","got","gets",
    "take","took","takes","give","gave","gives",
    "know","knew","knows","think","thought","thinks",
    "feel","felt","feels","find","found","finds",
    "ask","asked","asks","work","worked","works",
    "play","played","plays","want","wanted","wants",
    "need","needed","needs","help","helped","helps",
    "put","use","used","try","tried","call","called",
    "eat","ate","drink","drank","sleep","slept",
    "live","lived","learn","learned","understand","understood",
    "remember","remembered","forget","forgot","show","showed",
    "bring","brought","buy","bought","sell","sold",
    "build","built","break","broke","start","started",
    "stop","stopped","open","opened","close","closed",
    "sit","sat","stand","stood","wait","waited",
    "meet","met","carry","carried","hold","held",
    "hit","cut","kill","killed","die","died",
    "win","won","lose","lost","write","wrote",
    "read","sing","sang","dance","danced","jump","jumped",
    "fly","flew","swim","swam","drive","drove","ride","rode",
    "climb","climbed","fall","fell","laugh","laughed",
    "cry","cried","smile","smiled","hope","hoped",
    "wish","wished","decide","decided","explain","explained",
    "means","mean","meaning","meant","known",
    "actually","wrong","correction","instead","alright",
}

_QUESTION_STARTERS = {
    "what","who","where","when","why","how","which","whose",
    "tell","explain","define",
    "do","does","did","can","could","will","would","should",
    "is","are","was","were","have","has","had","may","might","must",
}

def _build_stopwords():
    words = set(_GRAMMAR) | set(_COMMON_VERBS)
    words.update(["alive", "dead", "awake", "asleep"])
    for text, _ in TRAINING_DATA:
        for w in re.findall(r"[a-z]+", text.lower()):
            words.add(w)
    return words

STOPWORDS = _build_stopwords()

FUNCTION_WORDS = {
    "i","you","we","they","he","she","it","me","us","them",
    "my","your","our","their","his","her","its",
    "am","is","are","was","were","be","been","being",
    "a","an","the","and","or","but",
    "do","does","did","have","has","had",
    "to","of","in","on","at","for","with","by","from",
    "this","that","these","those",
    "not","no","yes","ok","okay",
    "what","who","when","where","why","how","which",
    "like","love","want","need","know","think","feel","said",
}

def _content_words(text):
    return {w for w in _words(text) if w not in FUNCTION_WORDS and len(w) >= 3}

_CANCEL_WORDS = {
    "hi","hello","hey","greetings","yo","sup","bye","goodbye",
    "thanks","thank","ok","okay","yes","no","nevermind","never",
    "skip","cancel","forget","stop","quit","whatever","nothing",
    "later","fine",
}

def _is_cancel_or_greeting(text):
    words = _words(text)
    if not words:
        return False
    if len(words) == 1 and words[0] in _CANCEL_WORDS:
        return True
    if len(words) <= 2 and all(w in _CANCEL_WORDS for w in words):
        return True
    return False

_CANCEL_WORDS = {
    "hi","hello","hey","greetings","yo","sup","bye","goodbye",
    "thanks","thank","ok","okay","yes","no","nevermind","never",
    "skip","cancel","forget","stop","quit","whatever","nothing",
    "later","fine",
}

def _is_cancel_or_greeting(text):
    words = _words(text)
    if not words:
        return False
    if len(words) == 1 and words[0] in _CANCEL_WORDS:
        return True
    if len(words) <= 2 and all(w in _CANCEL_WORDS for w in words):
        return True
    return False


def _words(text):
    return re.findall(r"[a-z]+", text.lower())


def _to_int(tok):
    return int(tok) if tok.isdigit() else MATH_WORDS.get(tok)


def _is_question_text(text):
    words = _words(text)
    return bool(words) and words[0] in _QUESTION_STARTERS


class Brain:
    def __init__(self, perceptron_path="src/perceptron.npz",
                 max_depth=DEFAULT_MAX_DEPTH,
                 auto_save_path=None):
        self.affect = Affect()
        self.personality = Personality
        self.lexicon = Lexicon()
        self.episodic = EpisodicMemory()
        self.perceptron = Perceptron()
        self.lang = Language(seed=7)
        self.relations = RelationStore()
        self.fact_store = FactStore()
        self.meanings = {}
        self.max_depth = min(int(max_depth), HARD_MAX_DEPTH)
        self._boot_perceptron(perceptron_path)
        self._seed_lexicon("data/stimuli.txt")
        self.turn = 0
        self.pending = None
        self.definitions = {}
        self.ask_depth = 0
        self.asked_words = set()
        self.auto_save_path = auto_save_path
        if auto_save_path:
            persistence.load(self, auto_save_path)

    def _boot_perceptron(self, path):
        try:
            self.perceptron.load(path)
        except (FileNotFoundError, OSError):
            self.perceptron.train(TRAINING_DATA, epochs=300)
            try:
                self.perceptron.save(path)
            except OSError:
                pass

    def _seed_lexicon(self, path):
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        self.lexicon.see(parts[0], parts[1:])
        except FileNotFoundError:
            pass

    def _try_math(self, text):
        t = text.lower()
        t = t.replace("plus", "+").replace("minus", "-")
        t = t.replace("times", "*").replace("multiplied by", "*")
        toks = t.split()
        for i, op in enumerate(toks):
            if op in ("+", "-", "*") and 0 < i < len(toks) - 1:
                a, b = _to_int(toks[i - 1]), _to_int(toks[i + 1])
                if a is not None and b is not None:
                    return {"+": a + b, "-": a - b, "*": a * b}[op]
        m = re.search(r"(\d+)\s*([+\-*])\s*(\d+)", t)
        if m:
            a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
            return {"+": a + b, "-": a - b, "*": a * b}[op]
        return None

    def _perceive(self, text):
        words = _words(text)
        intent, conf = self.perceptron.predict(text)
        if conf < 0.40:
            intent = "unknown"
        return words, intent, conf

    def _is_unknown(self, w):
        if w in STOPWORDS:
            return False
        if len(w) < 3:
            return False
        if self.lexicon.has(w) or self.lexicon.has(w + "s") or self.lexicon.has(w + "es"):
            return False
        if w.endswith("s") and (self.lexicon.has(w[:-1]) or self.lexicon.has(w[:-2])):
            return False
        if w in self.definitions:
            return False
        if hasattr(self, "meanings") and w in self.meanings:
            return False
        return True

    def _find_unknown(self, words):
        seen, unknown = set(), []
        for w in words:
            if w in seen:
                continue
            seen.add(w)
            if self._is_unknown(w):
                unknown.append(w)
        unknown.sort(key=lambda w: -len(w))
        return unknown

    def _attend(self, words):
        known = sum(1 for w in words if self.lexicon.has(w))
        ratio = known / max(len(words), 1)
        if ratio < 0.3:
            self.affect.event("new_input", intensity=0.25)
        else:
            self.affect.event("familiar_input", intensity=ratio)
        return ratio

    def _bind_words(self, words):
        if not words:
            return
        for i, w in enumerate(words):
            ctx = [words[j] for j in range(len(words)) if j != i][:2]
            self.lexicon.see(w, ctx)

    def _lookup_definition(self, text):
        q = _words(text)
        if not any(w in ("what","who","tell","explain","define") for w in q):
            return None
        
        # Don't hijack SVO queries like "what does salman eat"
        if parse_query(text) is not None:
            return None
            
        target = q[-1]
        if target in self.definitions:
            return f"{target} means: {self.definitions[target]}"
        if self.relations.get("IS", target):
            return f"I know {target} is related to {', '.join(self.relations.get('IS', target))}."
        return None

    def _generate(self, intent, conf, text, recall):
        t_low = text.lower()
        if "your name" in t_low or "who are you" in t_low or "what are you" in t_low:
            return f"I am {self.personality.NAME}, built by {self.personality.BUILDER}."
        if "your age" in t_low or "how old are you" in t_low:
            return f"I am {self.personality.AGE} years old."
            
        math = self._try_math(text)
        if math is not None:
            self.affect.event("rewarded", intensity=0.5)
            return f"The answer is {math}."
        # L2.5: what is X where X is known-but-undefined -> ask user
        if _is_question_text(text) and parse_query(text) is None:
            qw = _words(text)
            if qw and qw[0] == "what" and len(qw) >= 3:
                target = qw[-1]
                known_meaning = (
                    target in self.definitions
                    or bool(self.relations.get("IS", target))
                    or (hasattr(self, "meanings") and target in self.meanings)
                )
                if (len(target) >= 3
                        and target not in FUNCTION_WORDS
                        and self.lexicon.has(target)
                        and not known_meaning):
                    self.pending = (target, text)
                    self.ask_depth += 1
                    self.asked_words.add(target)
                    self.affect.event("new_input", intensity=0.6)
                    return f"I know the word '{target}' but I don't know its meaning. Can you tell me?"

        rel_query = parse_query(text)
        if rel_query:
            rel_type, subj, obj = rel_query
            
            if rel_type == "SVO":
                composed_obj = compose_object(subj, obj, self.relations)
                if composed_obj:
                    return produce_svo(subj, obj, composed_obj)
                return f"I don't know what {subj} {obj}s."

            verb_map = {"IS": "is", "HAS": "has", "CAN": "can"}
            verb = verb_map.get(rel_type, "is")
            status, detail = self.relations.query(rel_type, subj, obj)
            if status == "yes":
                if rel_type == "IS":
                    return f"Yes, {subj} is {get_article(obj)} {obj}."
                return f"Yes, {subj} {verb} {obj}."
            if status == "superseded":
                active = self.relations.get(rel_type, subj)
                if active:
                    return f"No, {subj} {verb} {', '.join(active)}, not {obj}."
                return f"No, {subj} {verb} {obj} is outdated."
            if status == "no":
                inferred, reason_msg = infer_relation(self.relations, subj, rel_type, obj)
                if inferred:
                    return reason_msg
                if detail:
                    # If it's CAN, we say "I know dog can bark" not "dog is bark"
                    known_str = f"{subj} {verb} {detail[0]}" if len(detail) == 1 else f"{subj} {verb} {', '.join(detail[:-1])} or {detail[-1]}"
                    return f"I know {known_str}, but I don't know if {subj} {verb} {obj}."
                return f"I don't have enough information about {subj} yet."
            return f"I don't know {subj} yet. Teach me?"
        # L7: Use realizer if meaning was stored via construction
        if _is_question_text(text) and parse_query(text) is None:
            qw = _words(text)
            if len(qw) >= 3 and qw[0] == "what" and qw[1] == "is":
                target = qw[-1]
                if target in self.meanings:
                    return realize(self.meanings[target])

        lookup = self._lookup_definition(text)
        if lookup:
            return lookup
        if recall and intent != "identity":
            past_ep, past_score = recall[0]
            past_text = past_ep["text"]
            cur_content = _content_words(text)
            past_content = _content_words(past_text)
            overlap = cur_content & past_content

            past_is_question = _is_question_text(past_text)
            cur_is_question = _is_question_text(text)

            use_recall = (
                past_score > 0.55
                and len(overlap) >= 1
                and not (past_is_question and cur_is_question)
            )
            if use_recall:
                past_clean = past_text.strip()
                if past_clean:
                    past_clean = past_clean[0].upper() + past_clean[1:]
                
                # If user is asking a question, confirm it. If statement, just recall.
                if _is_question_text(text):
                    return f"Yes, you told me earlier: \"{past_clean}\""
                return f"I remember you said: \"{past_clean}\"."
        return self.lang.generate(intent, self.personality, self.affect)

    def _reset_chain(self):
        self.ask_depth = 0
        self.asked_words.clear()

    def _try_learn_relation(self, text):
        # Do not learn from questions! Only statements.
        if _is_question_text(text) or text.strip().endswith("?"):
            return None
            
        words = _words(text)
        if len(words) < 3:
            return None
        
        # 1. Check for SVO verbs (likes, wants, eats, etc.)
        svo_verb = None
        for w in words:
            if is_svo_verb(w):
                svo_verb = w
                break
                
        if svo_verb:
            idx = words.index(svo_verb)
            pre = [w for w in words[:idx] if w not in NOUN_DETERMINERS and w not in AUX_VERBS]
            post = [w for w in words[idx+1:] if w not in NOUN_DETERMINERS and w not in STOP_TAIL]
            if pre and post:
                subject = pre[-1]
                if len(subject) >= 3:
                    self.definitions[subject] = text.strip()
                    self.lexicon.see(subject, post[:3])
                    rels = extract(subject, text)
                    if rels:
                        for rel in rels:
                            self.relations.add(rel["type"], rel["subject"], rel["object"], rel["correct"])
                            if rel["object"] and not self.lexicon.has(rel["object"]):
                                self.lexicon.see(rel["object"])
                        subj_cap = subject.capitalize() if subject.lower() != "i" else "I"
                        return f"Got it! I learned that {subj_cap} {svo_verb} {' '.join(post[:3])}."
            return None

        # 2. Fallback to standard relations (means, is, are, has)
        m = None
        for word in ("means", "is", "are", "has", "can"):
            if word in words:
                m = word
                break
        
        if not m:
            return None

        idx = words.index(m)
        pre = [w for w in words[:idx] if w not in NOUN_DETERMINERS]
        post = [w for w in words[idx+1:] if w not in NOUN_DETERMINERS and w not in STOP_TAIL]
        
        if not pre or not post:
            return None
            
        subject = pre[-1]
        if len(subject) < 3:
            return None

        self.definitions[subject] = text.strip()
        self.lexicon.see(subject, post[:3])
            
        rels = extract(subject, text)
        if not rels:
            return None
            
        for rel in rels:
            self.relations.add(rel["type"], rel["subject"], rel["object"], rel["correct"])
            if rel["object"] and not self.lexicon.has(rel["object"]):
                self.lexicon.see(rel["object"])
                
        return f"Got it! I learned that {subject} {m} {' '.join(post[:3])}."

    def _try_construction(self, text):
        meaning = parse_to_meaning(text)
        # Only store statements, not questions
        if meaning and meaning[0] in ("IS_A", "IS_PROP", "SVO"):
            subj = meaning[1].lower()
            self.meanings[subj] = meaning
        return meaning

    def _answer_question(self, text):
        fkey = fact_query(text)
        if fkey:
            val = self.fact_store.get(fkey)
            response = (format_answer(fkey, val) if val is not None
                        else f"I don't know your {fkey} yet. Tell me?")
            wq = _words(text)
            self._attend(wq)
            self._bind_words(wq)
            self.episodic.store(text, self.affect.mood(), response, self.affect.binding_strength())
            self.affect.tick()
            return {
                "turn": self.turn, "text": text, "intent": "question",
                "confidence": 1.0, "mood": self.affect.mood(), "recall": None,
                "response": response,
            }
        words, intent, conf = self._perceive(text)
        self._attend(words)
        lookup = self._lookup_definition(text)
        if lookup:
            response = lookup
        else:
            recall = self.episodic.recall(text, top_k=1)
            response = self._generate(intent, conf, text, recall)
        self._bind_words(words)
        self.episodic.store(text, self.affect.mood(), response, self.affect.binding_strength())
        self.affect.tick()
        return {
            "turn": self.turn, "text": text, "intent": intent,
            "confidence": round(conf, 3), "mood": self.affect.mood(),
            "recall": None, "response": response,
        }

    def _resolve_pending(self, text):
        word, original = self.pending
        self.pending = None
        definition = text.strip()
        # Strip prefixes like "remember this" and trailing quotes
        definition = re.sub(r'^(remember this|remember|learn this|learn|note this)[\s:]+', '', definition, flags=re.I)
        definition = definition.strip('"\' ')
        
        # Pivot logic: If user gave a definition for a different word
        def_words = _words(definition)
        if def_words:
            first_word = def_words[0]
            if (word and first_word != word.lower() and len(first_word) >= 3 
                and first_word not in FUNCTION_WORDS 
                and any(w in def_words[1:4] for w in ("is", "are", "means", "has"))):
                # User pivoted to a new subject, process this new sentence independently
                self.pending = None
                self._reset_chain()
                return self._observe_inner(definition)
                
        w_lower = (word or "").lower()

        def_unknown = [w for w in _words(definition)
                       if w != w_lower and self._is_unknown(w)]
        orig_unknown = [w for w in _words(original)
                        if w != w_lower and self._is_unknown(w)]

        if word is None:
            # If it's a phrase, try to extract the core subject from the original text
            # e.g., "human is specie" -> subject is "human"
            original_words = _words(original)
            subject = original_words[0] if original_words else "phrase"
            self.definitions[subject] = definition
            label = subject
            self.lexicon.see(subject, _words(definition)[:3])
            for rel in extract(subject, definition):
                self.relations.add(rel["type"], rel["subject"], rel["object"], rel["correct"])
        else:
            self.definitions[word] = definition
            label = word
            self.lexicon.see(word, _words(definition)[:3])
            for rel in extract(word, definition):
                self.relations.add(rel["type"], rel["subject"], rel["object"], rel["correct"])
                if rel["object"] and not self.lexicon.has(rel["object"]):
                    self.lexicon.see(rel["object"])

        self.episodic.store(f"learned {label}: {definition}", "curious", "[learned]", 1.0)
        self.affect.event("rewarded", intensity=0.8)

        seen = set()
        candidates = []
        for w in def_unknown + orig_unknown:
            if w not in seen and w not in self.asked_words:
                seen.add(w)
                candidates.append(w)
        candidates.sort(key=lambda w: -len(w))

        if candidates and self.ask_depth < self.max_depth:
            nw = candidates[0]
            self.pending = (nw, original)
            self.ask_depth += 1
            self.asked_words.add(nw)
            self.affect.tick()
            return {
                "turn": self.turn, "text": text, "intent": "question",
                "confidence": 0, "mood": self.affect.mood(), "recall": None,
                "response": f"Got it! But what is '{nw}'?",
                "defined": label,
            }

        self._reset_chain()
        words, intent, conf = self._perceive(original)
        self._attend(words)
        self._bind_words(words)
        recall = self.episodic.recall(original, top_k=1)
        if intent == "unknown" or conf < 0.40:
            response = f"Got it! Now I know about '{label}'. Thanks for teaching me!"
        else:
            response = "Got it! " + self._generate(intent, conf, original, recall)
        self.episodic.store(original, self.affect.mood(), response, self.affect.binding_strength())
        self.affect.tick()
        return {
            "turn": self.turn, "text": text, "intent": intent,
            "confidence": round(conf, 3), "mood": self.affect.mood(),
            "recall": recall[0][0]["text"] if recall else None,
            "response": response, "defined": label,
        }

    def observe(self, text, llm_url=None, llm_model=None):
        self.turn += 1
        result = self._observe_inner(text)
        
        # LLM Teacher Integration (if API key exists, otherwise returns raw)
        if result and result.get("response"):
            raw_thought = result["response"]
            result["raw_thought"] = raw_thought
            result["response"] = improve_language(raw_thought, text, llm_url, llm_model)
            
        self._maybe_save()
        return result

    ASK_BANK = [
        "What is your favourite food?",
        "Do you like mangoes?",
        "What did you do today?",
        "Are you happy?",
        "What is your favourite game?",
        "Do you have a pet?",
        "How are you feeling?",
        "What is something interesting about you?",
        "What do you like?",
        "What is your favourite colour?",
    ]

    ASK_TRIGGERS = {
        "ask me something", "ask me anything", "ask me a question",
        "ask question", "ask me", "your question",
    }

    def _try_ask(self, text):
        if text.lower().strip() not in self.ASK_TRIGGERS:
            return None
        # Priority 1: pending curiosity from past
        if self.asked_words:
            target = next(iter(self.asked_words))
            return f"I'm curious — what is '{target}'? Can you teach me?"
        # Priority 2: user facts to ask about
        if not self.fact_store.has("name"):
            return "What is your name? I want to remember you."
        if not self.fact_store.has("age"):
            return "How old are you?"
        if not self.fact_store.has("location"):
            return "Where do you live?"
        # Priority 3: random from bank
        import random
        return random.choice(self.ASK_BANK)

    def _try_remember(self, text):
        m = re.match(r"^remember(?:\s+this|\s+that)?[:,]?\s+(.*)", text, re.IGNORECASE)
        if not m:
            return None
            
        payload = m.group(1).strip()
        if not payload:
            return "Remember what? Please tell me."
            
        # Replace "you" with "NSM" so it learns correctly about itself
        import re as _re
        payload_clean = _re.sub(r'\byou are\b', 'NSM is', payload, flags=_re.IGNORECASE)
        payload_clean = _re.sub(r'\byour\b', "NSM's", payload_clean, flags=_re.IGNORECASE)
        payload_clean = _re.sub(r'\byou\b', 'NSM', payload_clean, flags=_re.IGNORECASE)
        
        # Pass it to the normal brain pipeline to learn it
        self._observe_inner(payload_clean)
        
        return f"Got it! I will remember: '{payload}'."

    def _try_forget(self, text):
        t_low = text.lower().strip()
        m = re.match(r"^(forget|delete|remove)\s+(?:my\s+|about\s+)?([a-zA-Z]+)", t_low)
        if not m:
            return None
            
        target = m.group(2)
        
        # 1. Forget Name/Facts
        if target == "name":
            self.fact_store.facts.pop("name", None)
            return "Got it. I forgot your name."
        elif target in self.fact_store.facts:
            del self.fact_store.facts[target]
            return f"Got it. I forgot your {target}."
            
        # 2. Forget general words/definitions/meanings
        if target in self.definitions:
            del self.definitions[target]
        if target in self.meanings:
            del self.meanings[target]
        if target in self.lexicon.words:
            del self.lexicon.words[target]
            
        # 3. Forget relations
        keys_to_del = []
        for (rel_type, subj), bucket in self.relations.relations.items():
            if subj == target:
                keys_to_del.append((rel_type, subj))
            else:
                if target in bucket:
                    del bucket[target]
        for k in keys_to_del:
            del self.relations.relations[k]
            
        return f"Got it. I forgot everything about '{target}'."

    def _observe_inner(self, text):
        # L9: Remember System (Highest Priority)
        remember_resp = self._try_remember(text)
        if remember_resp:
            self.affect.event("rewarded", intensity=0.8)
            self.affect.tick()
            self.episodic.store(text, self.affect.mood(), remember_resp, 1.0)
            return {
                "turn": self.turn, "text": text, "intent": "statement",
                "confidence": 1.0, "mood": self.affect.mood(), "recall": None,
                "response": remember_resp,
            }

        # L9: Forget System (Highest Priority)
        forget_resp = self._try_forget(text)
        if forget_resp:
            self.affect.event("punished", intensity=0.5)
            self.affect.tick()
            self.episodic.store(text, self.affect.mood(), forget_resp, 1.0)
            return {
                "turn": self.turn, "text": text, "intent": "statement",
                "confidence": 1.0, "mood": self.affect.mood(), "recall": None,
                "response": forget_resp,
            }

        # L2.5-B: Ask me something (highest priority, overrides pending)
        ask_resp = self._try_ask(text)
        if ask_resp:
            self.affect.event("bonding_moment", intensity=0.5)
            self.affect.tick()
            self.episodic.store(text, self.affect.mood(), ask_resp, 0.7)
            return {
                "turn": self.turn, "text": text, "intent": "question",
                "confidence": 1.0, "mood": self.affect.mood(), "recall": None,
                "response": ask_resp,
            }

        # L4 Grammar Monster Queries (WH, Yes/No, Negation)
        meaning = parse_to_meaning(text)
        if meaning:
            if meaning[0] == "SVO_QUERY":
                subj, verb = meaning[1], meaning[2]
                objs = self.relations.get(verb.upper(), subj)
                if objs:
                    v = conjugate_verb(verb, "present", subj)
                    return {"turn": self.turn, "text": text, "intent": "question", "confidence": 1.0, "mood": self.affect.mood(), "recall": None, "response": f"{subj.capitalize()} {v} {objs[0]}."}
                return {"turn": self.turn, "text": text, "intent": "question", "confidence": 1.0, "mood": self.affect.mood(), "recall": None, "response": f"I don't know what {subj} {conjugate_verb(verb, 'present', subj)}."}

            elif meaning[0] == "SVO_YESNO":
                subj, verb = meaning[1], meaning[2]
                obj = meaning[3] if len(meaning) > 3 else None
                objs = self.relations.get(verb.upper(), subj)
                if obj and obj in objs:
                    return {"turn": self.turn, "text": text, "intent": "question", "confidence": 1.0, "mood": self.affect.mood(), "recall": None, "response": f"Yes, {subj} {conjugate_verb(verb, 'present', subj)} {obj}."}
                elif obj:
                    return {"turn": self.turn, "text": text, "intent": "question", "confidence": 1.0, "mood": self.affect.mood(), "recall": None, "response": f"No, {subj} does not {verb} {obj}."}
                else:
                    return {"turn": self.turn, "text": text, "intent": "question", "confidence": 1.0, "mood": self.affect.mood(), "recall": None, "response": f"I'm not sure."}

            elif meaning[0] == "NOT_SVO":
                subj, verb, obj = meaning[1], meaning[2], meaning[3]
                return {"turn": self.turn, "text": text, "intent": "statement", "confidence": 1.0, "mood": self.affect.mood(), "recall": None, "response": f"Got it. I will remember that {subj} does not {verb} {obj}."}

        if self.pending and _is_question_text(text):
            self.pending = None
            self._reset_chain()
            return self._answer_question(text)

        if self.pending and _is_cancel_or_greeting(text):
            self.pending = None
            self._reset_chain()
            # fall through to normal processing

        if self.pending:
            return self._resolve_pending(text)

        # L2: Fact queries (what is my name?)
        fkey = fact_query(text)
        if fkey:
            val = self.fact_store.get(fkey)
            response = (format_answer(fkey, val) if val is not None
                        else f"I don't know your {fkey} yet. Tell me?")
            wq = _words(text)
            self._attend(wq)
            self._bind_words(wq)
            self.episodic.store(text, self.affect.mood(), response, self.affect.binding_strength())
            self.affect.tick()
            return {
                "turn": self.turn, "text": text, "intent": "question",
                "confidence": 1.0, "mood": self.affect.mood(), "recall": None,
                "response": response,
            }

        # L7: Construction parse (store meaning)
        self._try_construction(text)

        # L2: Fact statements (my name is salman)
        fact = extract_fact(text)
        if fact:
            key, val = fact
            self.fact_store.set(key, val)
            response = f"Got it! I'll remember your {key} is {val}."
            ws = _words(text)
            self._attend(ws)
            self._bind_words(ws)
            self.episodic.store(text, self.affect.mood(), response, self.affect.binding_strength())
            self.affect.event("rewarded", intensity=0.6)
            self.affect.tick()
            return {
                "turn": self.turn, "text": text, "intent": "statement",
                "confidence": 1.0, "mood": self.affect.mood(), "recall": None,
                "response": response,
            }

        learned_resp = self._try_learn_relation(text)
        if learned_resp:
            words_lr = _words(text)
            self._attend(words_lr)
            self._bind_words(words_lr)
            self.episodic.store(text, self.affect.mood(), learned_resp, self.affect.binding_strength())
            self.affect.event("rewarded", intensity=0.5)
            self.affect.tick()
            return {
                "turn": self.turn, "text": text, "intent": "statement",
                "confidence": 0, "mood": self.affect.mood(), "recall": None,
                "response": learned_resp,
            }

        words, intent, conf = self._perceive(text)
        self._attend(words)
        recall = self.episodic.recall(text, top_k=1)

        if parse_query(text) is None:
            unknown = self._find_unknown(words)
        else:
            unknown = []
        if unknown and self.ask_depth < self.max_depth:
            word = unknown[0]
            self.pending = (word, text)
            self.ask_depth += 1
            self.asked_words.add(word)
            self.affect.event("new_input", intensity=0.8)
            known_words = [w for w in words if self.lexicon.has(w)]
            self._bind_words(known_words)
            self.episodic.store(text, self.affect.mood(), f"[asked about '{word}']", 0.5)
            self.affect.tick()
            return {
                "turn": self.turn, "text": text, "intent": "question",
                "confidence": 0, "mood": self.affect.mood(), "recall": None,
                "response": f"I don't know the word '{word}'. What does it mean?",
            }

        self._bind_words(words)
        known_ratio = sum(1 for w in words if self.lexicon.has(w)) / max(len(words), 1)
        if known_ratio > 0.5 and intent != "unknown":
            self.affect.event("repeated", intensity=0.6)

        response = self._generate(intent, conf, text, recall)
        self.episodic.store(text, self.affect.mood(), response, self.affect.binding_strength())
        self.affect.tick()

        for k in ("curiosity", "attention"):
            if self.affect.drives[k] > 85:
                self.affect.drives[k] = 78
        if self.affect.drives["curiosity"] > 65 and self.turn > 3:
            self.affect.drives["curiosity"] -= 8

        return {
            "turn": self.turn, "text": text, "intent": intent,
            "confidence": round(conf, 3), "mood": self.affect.mood(),
            "recall": recall[0][0]["text"] if recall else None,
            "response": response,
        }

    def _maybe_save(self):
        if self.auto_save_path:
            try:
                persistence.save(self, self.auto_save_path)
            except OSError:
                pass

    def observe_bulk(self, text, llm_url=None, llm_model=None):
        from src.text_utils import split_sentences
        sentences = split_sentences(text)
        
        if len(sentences) <= 1:
            return self.observe(text, llm_url=llm_url, llm_model=llm_model)
            
        last_result = None
        for s in sentences:
            last_result = self.observe(s, llm_url=llm_url, llm_model=llm_model)
            
        return {
            "turn": self.turn,
            "text": text,
            "intent": "bulk_learning",
            "confidence": 1.0,
            "mood": self.affect.mood(),
            "recall": None,
            "response": f"I read all {len(sentences)} sentences and learned from them! (Last update: {last_result['response']})"
        }

    def state(self):
        return {
            "turn": self.turn,
            "mood": self.affect.mood(),
            "episodes": self.episodic.size(),
            "vocab": len(self.lexicon.words),
            "definitions": len(self.definitions),
            "relations": self.relations.count(),
            "facts": len(self.fact_store.facts),
            "pending": self.pending,
            "max_depth": self.max_depth,
            "ask_depth": self.ask_depth,
            "affect": dict(self.affect.drives),
            "hormones": dict(self.affect.hormones),
        }
