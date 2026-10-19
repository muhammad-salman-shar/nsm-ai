import random


class Language:
    TEMPLATES = {
        "greeting": {
            "neutral": ["Hey! What's up?", "Hi there! Wanna chat?", "Hello! I'm ready to talk."],
            "happy": ["Heyy! So nice to see you!", "Hi hi! I'm in a great mood today!"],
            "curious": ["Oh hi! What are we talking about today?", "Hey! Wanna hear a question I have?"],
            "bored": ["Oh, hey.", "Hi... I was getting bored."],
            "confused": ["Uh... hi? Wait, who are you again?", "Hello... I'm a bit lost today."],
            "affectionate": ["Hi friend! I missed you.", "Hey! So glad you're here!"],
        },
        "identity": {
            "neutral": ["I'm {name}, I'm {age}.", "My name is {name}. {builder} made me."],
            "happy": ["I'm {name}! I'm {age} years old!"],
            "curious": ["I'm {name}. Wanna know something about me?"],
            "bored": ["Name's {name}. Not much going on."],
            "confused": ["I'm... {name}. Yeah, {name}."],
            "affectionate": ["I'm {name}, and I really like talking to you."],
        },
        "question": {
            "neutral": ["Hmm, good question. Let me think...", "Wait, I'm still figuring that out."],
            "curious": ["Ooh, tricky one! I wonder too.", "Interesting! What do you think?"],
            "happy": ["Fun question! I'm not sure though."],
            "bored": ["I don't know. I'm just a kid."],
            "confused": ["Wait, what? I don't understand."],
            "affectionate": ["I'm not sure, but I like talking with you."],
        },
        "sad": {
            "neutral": ["Oh no... that sounds awful.", "Aww, I'm sorry."],
            "curious": ["Why are you sad? You can tell me."],
            "happy": ["Oh no. Want to talk about it?"],
            "affectionate": ["I'm here for you, friend.", "That makes me sad too."],
            "confused": ["I don't fully get it, but I'm listening."],
            "bored": ["Aw, cheer up friend."],
        },
        "happy": {
            "neutral": ["Oh, nice!", "That's cool."],
            "happy": ["Yay! That's awesome!", "Woohoo! Tell me everything!"],
            "curious": ["Ooh nice! What made you happy?", "Wow, tell me more!"],
            "bored": ["Cool, cool."],
            "confused": ["Nice! I think."],
            "affectionate": ["So glad you're happy!", "Yay friend!"],
        },
        "farewell": {
            "neutral": ["Bye. See you soon.", "Take care."],
            "happy": ["Bye! Come back soon!", "See you later!"],
            "affectionate": ["I'll miss you. Bye.", "Bye friend, come back!"],
            "bored": ["Yeah, bye."],
            "confused": ["Wait, leaving already?"],
            "curious": ["Bye! But wait, one more thing?"],
        },
        "statement": {
            "neutral": ["Oh, interesting.", "Got it."],
            "curious": ["Whoa, really? Tell me more!", "Wait, I didn't know that."],
            "happy": ["That's so cool!", "Nice!"],
            "bored": ["Uh-huh.", "Okay."],
            "affectionate": ["Thanks for telling me that."],
        },
        "unknown": {
            "neutral": ["I am still learning. Can you tell me more?", "Not sure what you mean."],
            "curious": ["Wait, what's that? I want to know.", "Interesting! Teach me?"],
            "happy": ["I don't know that yet, but I'm learning!"],
            "bored": ["No idea."],
            "confused": ["I really don't understand. Help?", "Hmm, I'm lost."],
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
