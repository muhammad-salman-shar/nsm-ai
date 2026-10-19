import urllib.request
from src.brain import Brain
from src import database, persistence

def import_words(url):
    print(f"1. Downloading word list from:\n   {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            words = response.read().decode('utf-8').splitlines()
    except Exception as e:
        print(f"Download failed: {e}")
        return
        
    print(f"2. Downloaded {len(words)} words. Loading into public brain...")
    
    # Load existing public brain
    b = Brain(auto_save_path=None)
    state = database.load_brain("public")
    if state:
        persistence.from_dict(b, state)
        
    count = 0
    for w in words:
        w = w.strip().lower()
        if len(w) >= 2 and not w.isdigit():
            b.lexicon.see(w)
            count += 1
            
    # Save back to public DB
    database.save_brain("public", persistence.to_dict(b))
    print(f"✅ Successfully imported {count} words into Global Brain!")

if __name__ == "__main__":
    URL = "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-no-swears.txt"
    import_words(URL)
