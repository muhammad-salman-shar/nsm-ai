class Affect:
    DRIVES = ("curiosity", "attention", "social_reward",
              "confusion", "satisfaction", "bonding")
    HORMONES = ("dopamine", "oxytocin", "cortisol")

    DECAY = {"curiosity": 1.0, "attention": 2.0, "social_reward": 1.5,
             "confusion": 2.0, "satisfaction": 1.5, "bonding": 0.5}

    def __init__(self):
        self.drives = {k: 50.0 for k in self.DRIVES}
        self.hormones = {"dopamine": 40.0, "oxytocin": 40.0, "cortisol": 20.0}
        self.drives["curiosity"] = 70.0
        self.turn = 0

    def _clip(self, v):
        return max(0.0, min(100.0, v))

    def tick(self):
        self.turn += 1
        for k, d in self.DECAY.items():
            self.drives[k] = self._clip(self.drives[k] - d)
        for k in self.hormones:
            target = 40.0
            self.hormones[k] = self._clip(self.hormones[k] + (target - self.hormones[k]) * 0.1)

    def event(self, kind, intensity=1.0):
        d, h = self.drives, self.hormones
        if kind == "new_input":
            d["curiosity"] += 10 * intensity
            d["attention"] += 15 * intensity
            h["dopamine"] += 5 * intensity
        elif kind == "familiar_input":
            d["satisfaction"] += 10 * intensity
            d["attention"] += 5 * intensity
            h["oxytocin"] += 8 * intensity
        elif kind == "confused":
            d["confusion"] += 20 * intensity
            h["cortisol"] += 15 * intensity
            h["dopamine"] -= 5 * intensity
        elif kind == "rewarded":
            d["social_reward"] += 15 * intensity
            d["satisfaction"] += 10 * intensity
            d["bonding"] += 8 * intensity
            h["dopamine"] += 12 * intensity
            h["oxytocin"] += 10 * intensity
        elif kind == "punished":
            d["satisfaction"] -= 15 * intensity
            d["bonding"] -= 5 * intensity
            h["cortisol"] += 20 * intensity
            h["dopamine"] -= 10 * intensity
        elif kind == "repeated":
            d["confusion"] -= 10 * intensity
            d["satisfaction"] += 5 * intensity
        elif kind == "bonding_moment":
            d["bonding"] += 20 * intensity
            h["oxytocin"] += 15 * intensity
            d["satisfaction"] += 10 * intensity
        for k in self.drives:
            self.drives[k] = self._clip(self.drives[k])
        for k in self.hormones:
            self.hormones[k] = self._clip(self.hormones[k])

    def mood(self):
        d = self.drives
        if d["confusion"] > 60 and self.hormones["cortisol"] > 50:
            return "confused"
        if d["satisfaction"] > 60 and d["social_reward"] > 50:
            return "happy"
        if d["bonding"] > 65:
            return "affectionate"
        if d["curiosity"] > 65:
            return "curious"
        if d["attention"] < 30 or d["satisfaction"] < 30:
            return "bored"
        return "neutral"

    def binding_strength(self):
        return 0.5 + (self.hormones["dopamine"] / 200.0)

    def social_weight(self):
        return 0.5 + (self.hormones["oxytocin"] / 200.0)

    def exploration(self):
        return max(0.0, 1.0 - self.hormones["cortisol"] / 100.0)

    def __repr__(self):
        d = " ".join(f"{k[:4]}={v:.0f}" for k, v in self.drives.items())
        h = " ".join(f"{k[:4]}={v:.0f}" for k, v in self.hormones.items())
        return f"<Affect mood={self.mood()} | {d} | {h}>"
