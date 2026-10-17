# NSM-AI — Bachcha v0.1

A developmental cognitive system. Not an LLM. No gradients, no parameters, no tokens.

## Core principles
- **Hyperdimensional Computing** (10k-dim binary vectors) for memory
- **Homeostasis** — energy, pain, curiosity, safety drive behavior
- **Virtual death** — energy=0 or pain=100 → restart (memory persists)
- **Contingency detection** — no explicit labels, only co-occurrence
- **Survival policy** — Q-learning without neural nets

## Stage 1 (this repo)
Reflex-level learning:
- Bind stimuli to contexts via XOR
- Detect "X always followed by Y" (contingency)
- Learn actions that maximize life score
- Report: survival time, deaths, associations formed

## Run
python -m src.main

## Honest
"Emotions" are numeric state variables. "Feeling" is functional, not phenomenal.
Stage 1 is reflex-level — no language, no reasoning, just associative life.
