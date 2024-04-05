import itertools

# File containing words to check
WORD_FILE = "c:/Users/Clayton/OneDrive/Documents/Coding/Spotify Tools/bad_dict!.txt"

# Define your second dictionary named 'suffixes'
PREFIXES = ["un","re","pre","mis","dis","in","im","en","ex","over","under","out","auto","anti"]
SUFFIXES = ["t","y","ly","able","less","ness","ful","ment","er","est","ed","ing","en","s","es","head","hole"]

# Load words to check from file
with open(WORD_FILE, 'r') as file:
    WORD_LIST = [word.strip() for word in file.readlines()]

# Generate combinations of phrases and suffixes
combined_phrases = set()
for word1 in WORD_LIST:
    for word2 in WORD_LIST:
        for prefix, suffix in itertools.product(PREFIXES, SUFFIXES):
            combined_phrase1 = f"{word1}"
            combined_phrase2 = f"{word1}{suffix}"
            combined_phrase3 = f"{prefix}{word1}"
            combined_phrase4 = f"{prefix}{word1}{suffix}"
            combined_phrases.add(combined_phrase1)
            combined_phrases.add(combined_phrase2)
            combined_phrases.add(combined_phrase3)
            combined_phrases.add(combined_phrase4)

# Save the combined phrases to a file
COMBINED_FILE = "c:/Users/Clayton/OneDrive/Documents/Coding/Spotify Tools/combined_phrases.txt"
with open(COMBINED_FILE, 'w') as file:
    file.write("\n".join(combined_phrases))