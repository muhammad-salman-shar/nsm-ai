import re

# Common words to ignore (Stopwords)
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "they",
    "to", "of", "in", "on", "at", "for", "with", "by", "from", "up", "down",
    "and", "or", "but", "if", "then", "so", "because", "as", "than",
    "this", "that", "these", "those", "there", "here", "what", "who", "where",
    "when", "why", "how", "which", "do", "does", "did", "have", "has", "had",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must",
    "not", "no", "yes", "ok", "okay"
}

class MemoryIndex:
    def __init__(self):
        # Inverted index: {keyword: [memory_id_1, memory_id_2, ...]}
        self.index = {}
        # Storage: {memory_id: original_text}
        self.memories = {}
        self.next_id = 1

    def extract_keywords(self, text):
        """Extracts important words from a sentence, ignoring stopwords."""
        words = re.findall(r"[a-z0-9]+", text.lower())
        keywords = [w for w in words if w not in STOPWORDS and len(w) > 2]
        return list(set(keywords)) # Remove duplicates

    def save_memory(self, text):
        """Saves memory and indexes its keywords."""
        mem_id = self.next_id
        self.memories[mem_id] = text
        self.next_id += 1
        
        keywords = self.extract_keywords(text)
        for kw in keywords:
            if kw not in self.index:
                self.index[kw] = []
            self.index[kw].append(mem_id)
            
        return mem_id, keywords

    def search(self, query):
        """Finds memories matching the query keywords."""
        query_kws = self.extract_keywords(query)
        if not query_kws:
            return []
            
        # Count how many query keywords each memory matches
        match_scores = {}
        for kw in query_kws:
            if kw in self.index:
                for mem_id in self.index[kw]:
                    match_scores[mem_id] = match_scores.get(mem_id, 0) + 1
                    
        # Sort memories by match score (highest first)
        sorted_mems = sorted(match_scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for mem_id, score in sorted_mems:
            results.append({
                "id": mem_id, 
                "text": self.memories[mem_id], 
                "score": score,
                "matched_keywords": len(query_kws)
            })
        return results
