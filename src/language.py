import random


class Language:
    TEMPLATES = {
        "greeting": {
            "neutral": ["Hi! I'm {name}.", "Hello! How are you?", "Hey there."],
            "happy": ["Hi hi hi! So nice to see you!", "Hello hello! I'm happy today!"],
            "curious": ["Oh hi! What are you up to?", "Hello! Wanna talk about something fun?"],
            "bored": ["Oh, hi.", "Hey... I was getting bored."],
            "confused": ["Uh... hi? I'm a bit confused.", "Hello... wait, who are you?"],
            "affectionate": ["Hi friend! I missed you.", "Hello my friend!"],
        },
        "identity": {
            "neutral": ["I'm {name}. I'm {age}.", "My name is {name}. {builder} built me."],
            "happy": ["I'm {name}! I'm {age} years old!"],
            "curious": ["I'm {name}. Wanna know more about me?"],
            "bored": ["Name's {name}. Not much else today."],
            "confused": ["I'm... {name}. Yes, {name}."],
            "affectionate": ["I'm {name}, and I'm happy to know you."],
        },
        "question": {
            "neutral": ["Good question. Let me think...", "Hmm, I'm still learning about that."],
            "curious": ["Ooh, good question! I wonder too.", "Interesting! What do you think?"],
            "happy": ["Fun question! I'm not sure but I like it."],
            "bored": ["I don't know. I'm just a kid."],
            "confused": ["I don't understand that yet. Can you explain?"],
            "affectionate": ["I'm not sure, but I like talking with you."],
        },
        "sad": {
            "neutral": ["I'm sorry you feel that way.", "That sounds hard."],
            "curious": ["Why are you sad? Tell me."],
            "happy": ["Oh no. Want to talk about it?"],
            "affectionate": ["I'm here for you.", "I care about you."],
            "confused": ["I don't fully understand sadness, but I'm listening."],
            "bored": ["Aw, cheer up friend."],
        },
        "happy": {
            "neutral": ["That's nice!", "Good to hear."],
            "happy": ["Yay! I'm happy for you!", "That's wonderful!"],
            "curious": ["Ooh nice! Tell me more!", "What made you happy?"],
            "bored": ["Cool, cool."],
            "confused": ["Nice! I think."],
            "affectionate": ["So glad you're happy!", "Yay friend!"],
        },
        "farewell": {
            "neutral": ["Goodbye. See you soon.", "Take care."],
            "happy": ["Bye! Come back soon!", "See you later friend!"],
            "affectionate": ["I'll miss you. Bye.", "Bye friend, come back!"],
            "bored": ["Yeah, bye."],
            "confused": ["Bye? Already?"],
            "curious": ["Bye! But wait, one more thing?"],
        },
        "statement": {
            "neutral": ["Interesting.", "Okay, noted."],
            "curious": ["Really? Tell me more!", "Wow, I didn't know."],
            "happy": ["That's cool!", "Nice!"],
            "bored": ["Uh-huh.", "Okay."],
            "affectionate": ["Thanks for sharing that with me."],
        },
        "unknown": {
            "neutral": ["I am learning. Can you tell me more?", "Not sure what you mean."],
            "curious": ["Interesting! I'm learning, tell me more.", "What's that? I want to know."],
            "happy": ["I don't know that yet but I'm learning!"],
            "bored": ["I don't know."],
            "confused": ["I really don't understand. Teach me?", "Hmm, I'm lost. Help?"],
            "affectionate": ["I'm still learning. Teach me, friend?"],
        },
    }

    def __init__(self, seed=42):
        self.rng = random.Random(seed)

    def _persona_context(self, personality):
        return {
            "name": personality.NAME,
            "full_name": personality.FULL_NAME,
            "age": personality.AGE,
            "builder": personality.BUILDER,
            "fav_food": personality.favorite("food"),
            "fav_game": personality.favorite("game"),
            "fav_animal": personality.favorite("animal"),
            "fav_color": personality.favorite("color"),
        }

    def _fill(self, template, ctx):
        try:
            return template.format(**ctx)
        except (KeyError, IndexError):
            return template

    def generate(self, intent, personality, affect=None):
        mood = affect.mood() if affect else "neutral"
        bank = self.TEMPLATES.get(intent, self.TEMPLATES["unknown"])
        options = bank.get(mood) or bank.get("neutral") or ["I am learning."]
        template = self.rng.choice(options)
        return self._fill(template, self._persona_context(personality))
