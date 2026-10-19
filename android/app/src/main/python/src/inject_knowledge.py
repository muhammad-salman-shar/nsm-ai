import json
import os
from src.brain import Brain
from src import database, persistence

def inject_definitions():
    filepath = "data/dictionary.json"
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return

    print(f"1. Reading {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to read JSON: {e}")
        return

    print(f"File loaded. Total words: {len(data)}")
    
    # Load Global Brain
    b = Brain(auto_save_path=None)
    state = database.load_brain("public")
    if state:
        persistence.from_dict(b, state)

    # Injecting 5000 common words to keep it fast but smart
    count = 0
    print("2. Injecting definitions into NSM...")
    for word, info in data.items():
        if count >= 5000:
            break
            
        w = word.lower().strip()
        
        # The dictionary json usually has a string definition or a dict
        if isinstance(info, str):
            definition = info
        elif isinstance(info, dict) and "meanings" in info:
            definition = info["meanings"][0].get("def", "")
        else:
            continue
            
        if w and definition:
            # Save to definitions
            b.definitions[w] = definition[:150] + ("..." if len(definition) > 150 else "")
            # Add to lexicon so it's recognized
            b.lexicon.see(w, definition.split()[:3])
            count += 1

    # Save back to DB
    print("3. Saving to database...")
    database.save_brain("public", persistence.to_dict(b))
    print(f"✅ Successfully injected {count} definitions into Global Brain!")

if __name__ == "__main__":
    inject_definitions()
