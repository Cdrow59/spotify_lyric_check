import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import lyricsgenius
from fuzzywuzzy import fuzz  # Import fuzz function from fuzzywuzzy
import re
import logging
from collections import defaultdict
from rich.console import Console
from rich.logging import RichHandler
from rich import print
from fuzzywuzzy import process

#Get and define script path and and functions
script_path = os.path.realpath(__file__)

base_name = os.path.basename(script_path)
script_name = os.path.splitext(base_name)[0]

#define path
current_dir = os.getcwd()
cache_folder = "\\_spotifycache_\\"
log_folder = "\\logs\\"
#Define cache path vars
log_path = current_dir+log_folder
path = current_dir+cache_folder

file_ext = ".spotify_cache"
log_ext = ".log"


#Create and Clear Logging Path
log_file = (log_path+script_name+log_ext)
print(current_dir)
#check if path exists if not create it
if not os.path.exists(log_path):
    os.makedirs(log_path)

if os.path.exists(log_file):
    os.remove(log_file)
    
# Set up logging
    #Create Logging Handler
    #Levels are:
    #CRITICAL
    #ERROR
    #WARNING
    #INFO
    #DEBUG
    #NOTSET
logging.basicConfig(
    level=logging.DEBUG,  # Set the root logger level (the lowest level that will be processed)
    format="%(message)s",  # Customize the logging format for console output if needed
    datefmt="[%Y-%m-%d %H:%M:%S]",  # Customize the date format if needed
    handlers=[
        RichHandler(level=logging.INFO),  # Use RichHandler for colorful console output with INFO level
    ]
)

# Create a FileHandler with custom message format
file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(levelname)s %(asctime)s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s"))
logging.getLogger().addHandler(file_handler)  # Add the FileHandler to the root logger


log = logging.getLogger("rich")


# Set the cache file
cache_file = (path+script_name+file_ext)  # Specify your desired cache path here

#check if path exists if not create it
if not os.path.exists(path):
    os.makedirs(path)
    

#Create console
console = Console()

# Define your Spotify client credentials
client_id = "18bb257c4ecd411c86431e9b1aa9948d"
client_secret = "03490478cede495d95e275b341cdc5d7"
redirect_uri = 'http://localhost:8000/callback'

# Authenticate with Spotify and Genius
scope = 'playlist-read-private'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope, cache_path=cache_file))
genius = lyricsgenius.Genius('EJvKf6eHsTGVeD47wgOaZigvf3dQS7uJUXpeXaJLYu8VLavUPBNluo_Zd0sW-07e')

#Set Genius Settings
    #Remove genius log messages as we us our own custom messages
genius.verbose = False
    # Remove section headers (e.g. [Chorus]) from lyrics when searching
genius.remove_section_headers = True


    #Set Timeout and Retry Settings
genius.timeout = 60
genius.retries = 2


# File containing words to check
WORD_FILE = "c:/Users/Clayton/OneDrive/Documents/Coding/Spotify Tools/new_bad_dict.txt"

# Load words to check from file
with open(WORD_FILE, 'r') as file:
    WORD_LIST = [word.strip() for word in file.readlines()]
    
# Get playlist ID from user
playlist_id = input('Enter the playlist ID:\n')

# Get tracks from the playlist
playlist = sp.playlist_tracks(playlist_id)
tracks = playlist['items']

#Tracks to remove
item_removal = []

def is_reasonable_match(track_name, song_title):
    # Function to check if a song is a reasonable match for the track name
    return fuzz.token_sort_ratio(track_name.lower(), song_title.lower()) > 65

def clean_lyrics(lyrics, artist_name):
    # Remove patterns like 'Contributors...', 'Translations...' from the beginning
    cleaned_lyrics = re.sub(r'^\d+ (Contributors|Translations).*\n', '', lyrics, flags=re.MULTILINE | re.IGNORECASE)

    # Remove patterns like 'Embed, xEmbed...' from the end
    cleaned_lyrics = re.sub(r'Embed.*$', '', cleaned_lyrics, flags=re.MULTILINE)

    # Remove patterns like 'See {artist_name} LiveGet tickets as low as $xYou might also like'
    pattern = fr"See {re.escape(artist_name)} LiveGet tickets as low as \$\d+You might also like"
    cleaned_lyrics = re.sub(pattern, '', cleaned_lyrics, flags=re.IGNORECASE)

    # Remove patterns like 'Contributor...', 'Translations...' from the beginning
    cleaned_lyrics = re.sub(r'\d+ Contributor', '', cleaned_lyrics)

    # Remove specific patterns "You might also like\d+" and "You might also like"
    cleaned_lyrics = re.sub(r'You might also like\d+', '', cleaned_lyrics)
    
    cleaned_lyrics = re.sub(r'You might also like', '', cleaned_lyrics)
    #Remove pattern "Lyrics"
    cleaned_lyrics = re.sub(r'.*Lyrics', '', cleaned_lyrics)
    #Rremove trailing digits
    cleaned_lyrics = re.sub(r'\d+$', '', cleaned_lyrics)
    # Remove any remaining extra leading and trailing spaces and newlines
    cleaned_lyrics = cleaned_lyrics.strip()

    return cleaned_lyrics

def fetch_lyrics_from_genius(genius_id):
    try:
        song = genius.lyrics(song_id=genius_id)
        return song if song else None
    except Exception as e:
        log.error(f"Failed to fetch lyrics from Genius: {e}")
        return None

def contains_phrase(lyrics):
    for phrase in WORD_LIST:
        if re.search(r'\b' + re.escape(phrase) + r'\b', lyrics, re.IGNORECASE):
            return True
    return False

def highlight_phrases(lyrics):
    # Create a defaultdict to store the count of occurrences for each phrase
    phrase_count = defaultdict(int)

    # Function to replace words with appropriate colors and count occurrences
    def replace_word(match):
        word = match.group(0)
        word_lower = word.lower()
        for phrase in WORD_LIST:
            if re.search(r'\b' + re.escape(phrase) + r'\b', word_lower, re.IGNORECASE):
                phrase_count[phrase] += 1
                return "[red]" + word + "[/red]"
        
        return "[green]" + word + "[/green]"

    # Create a regex pattern to match all words (including multi-word phrases)
    pattern = re.compile(r'\b(?:' + '|'.join(re.escape(phrase) for phrase in WORD_LIST) + r')\b|\w+')

    # Perform replacement and highlighting while counting occurrences
    highlighted_lyrics = re.sub(pattern, replace_word, lyrics)

    log.info("Lyrics:")
    log.debug(cleaned_lyrics, extra={"markup": True, "highlighter": False})
    log.info(highlighted_lyrics, extra={"markup": True, "highlighter": False})

    # Print the count of occurrences for each phrase
    for phrase, count in phrase_count.items():
        log.info(f"- [red]{phrase}[/red] found [bright_cyan]{count}[/bright_cyan] time(s) in the lyrics", extra={"markup": True, "highlighter": False})
    return highlighted_lyrics

def find_best_match(track_name, artist_name, results, similarity_threshold=30):
    # Function to find the best match for the track name and artist name

    # Create a list of song titles and their corresponding IDs from the results
    song_titles = [track['title'] for track in results]
    song_ids = [track['id'] for track in results]

    # Use fuzzy matching to get a list of matches sorted by similarity score
    matches = process.extract(track_name.lower(), song_titles, scorer=fuzz.token_sort_ratio)

    # Check the top match and see if it meets the similarity threshold
    try:
        best_match, score = matches[0]
        if score >= similarity_threshold:
            best_match_id = song_ids[song_titles.index(best_match)]
        else:
            best_match_id = None

    except IndexError:
        best_match_id = None
    
    return best_match_id

def extract_genius_id(url):
    # Example URL: "https://genius.com/Niviro-demons-lyrics"
    match = re.search(r'https://genius.com/([^/?]+)', url)
    if match:
        return match.group(1)
    else:
        return None

def get_user_input(prompt):
    while True:
        user_input = input(prompt).strip().lower()
        if user_input == "y" or user_input == "n" or user_input =="exit" or user_input == "autoy":
            return user_input
        else:
            print("Invalid input! Please enter 'y' for yes or 'n' for no.")

user_input = None


# Iterate over tracks
for index, track in enumerate(tracks):
    log.info("")
    # Get track details
    track_name = track['track']['name']
    artist_name = track['track']['artists'][0]['name']
    track_id = track['track']['id']
    track_uri = track['track']['uri']
    
    # Search for lyrics using Genius API
    search_query = track_name + ' ' + artist_name

    # Fetch the songs from Genius by search query
    log.info(f"Searching for {search_query}")
    search_results = genius.search(search_query)
    if search_results:
        # Filter the search results to find the matching track with a score >= 65
        matching_tracks = [result['result'] for result in search_results['hits'] if result['type'] == 'song']
        best_match_id = find_best_match(track_name, artist_name, matching_tracks)

        if best_match_id:
            # Fetch the lyrics from Genius using the Genius ID
            lyrics = fetch_lyrics_from_genius(best_match_id)
            if lyrics:
                log.info(f"Lyrics Found For {track_name} by {artist_name}")
                # Clean the lyrics by removing unwanted patterns
                cleaned_lyrics = clean_lyrics(lyrics, artist_name=artist_name)
                # Print the highlighted lyrics with matched phrases in red and others in green


                


                # Check if the cleaned lyrics contain any of the phrases from the word list
                if contains_phrase(cleaned_lyrics):
                    # Process the cleaned lyrics to apply color highlighting
                    highlighted_lyrics = highlight_phrases(cleaned_lyrics)
                    
                    track_info = {"uri": track_id, "positions": [index]}
                    # Check for phrases in the WORD_LIST in the cleaned lyrics
                    if user_input != "autoy":
                        user_input = get_user_input("Enter 'y' to remove the song, 'autoy' to remove automatically, 'n' to keep it, or 'exit' to save and exit the program\n")
                    if user_input == "y":
                        log.info(f"Adding Track with 'Item' value of {track_info} for removal")
                        
                        # Append the track_info dictionary to the item_removal list
                        item_removal.append(track_info)
                    if user_input == "autoy":
                        log.info(f"Adding Track with 'Item' value of {track_info} for removal")
                        
                        # Append the track_info dictionary to the item_removal list
                        item_removal.append(track_info)
                    if user_input == "n":
                        continue
                    if user_input == "exit":
                        break
                    
                else:
                    #No matches for the phrase dict where found
                    log.info(f"No phrases found for {track_name} by {artist_name}")
            else:
                # Lyrics not found or no reasonable matches within similarity_threshold 
                log.warning(f"Failed to fetch lyrics for {track_name} by {artist_name} from Genius ID: {best_match_id} or lyrics do not match track name")
        else:
            # Best match not found in the find_best_match function, log a warning and continue to the next track
            log.warning(f"No reasonable match found for {track_name} by {artist_name}")
    else:
        # No search results found, log a warning and continue to the next track
        log.warning(f"No search results found for {track_name} by {artist_name}")


if item_removal:
    # Remove the selected items from the playlist
    log.info(f"Removing tracks with values of {item_removal}")
    sp.playlist_remove_specific_occurrences_of_items(playlist_id, item_removal)
