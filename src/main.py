import sys
from src.brain import Brain


BANNER = """
=====================================
  NSM VB — NeuraSaMu Virtual Brain
  A 10-year-old kid. Still learning.
  Type 'quit' to exit, 'state' for info.
=====================================
"""


def main():
    b = Brain()
    print(BANNER)
    while True:
        try:
            user = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            break
        if not user:
            continue
        if user.lower() in ("quit", "exit", "bye"):
            print(f"NSM VB> {b.lang.generate('farewell', b.personality, b.affect)}")
            break
        if user.lower() == "state":
            for k, v in b.state().items():
                print(f"  {k}: {v}")
            continue
        r = b.observe(user)
        print(f"NSM VB> {r['response']}")
        if r["recall"]:
            print(f"        (recall: {r['recall']!r})")


if __name__ == "__main__":
    main()
