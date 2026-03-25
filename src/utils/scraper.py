import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from youtubesearchpython import VideosSearch

def get_wikipedia_metadata(movie_title, lang='en'):
    """
    Scrapes Wikipedia for a movie's main poster image and opening paragraph.
    Handles disambiguation (e.g. "Toy Story" vs "Toy Story (1995 film)").
    """
    # Clean the title (e.g., "Toy Story (1995)" -> "Toy Story")
    base_title = re.sub(r'\s*\(\d{4}\)', '', movie_title).strip()
    
    # Handle MovieLens format: "Avengers, The" -> "The Avengers"
    if base_title.endswith(", The"):
        base_title = "The " + base_title[:-5]
    elif base_title.endswith(", A"):
        base_title = "A " + base_title[:-3]
    elif base_title.endswith(", An"):
        base_title = "An " + base_title[:-4]

    year_match = re.search(r'\((\d{4})\)', movie_title)
    year = year_match.group(1) if year_match else ""

    # Try specific film title first, then generic
    search_titles = [f"{base_title} ({year} film)", f"{base_title} (film)", base_title]
    
    metadata = {
        "poster": None,
        "description": "Synopsis not available.",
        "trailer_id": None
    }

    # Grab YouTube Trailer ID
    try:
        lang_map = {'en': 'English', 'es': 'Spanish', 'fr': 'French', 'hi': 'Hindi'}
        trailer_lang_query = f"in {lang_map.get(lang, '')}" if lang != 'en' else ""
        videosSearch = VideosSearch(f"{base_title} {year} official trailer {trailer_lang_query}".strip(), limit = 1)
        res = videosSearch.result()
        if res and res['result']:
            metadata['trailer_id'] = res['result'][0]['id']
    except Exception as e:
        print(f"YouTube Scraper error: {e}")

    headers = {
        'User-Agent': 'MovieXRecommenderBot/1.0 (Educational Project)'
    }

    for title in search_titles:
        encoded_title = urllib.parse.quote(title.replace(' ', '_'))
        url = f"https://{lang}.wikipedia.org/wiki/{encoded_title}"
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Double check it's actually about a film to avoid generic pages
                page_text_start = soup.text[:1000].lower()
                is_film_page = 'film' in page_text_start or 'película' in page_text_start or 'फ़िल्म' in page_text_start or '(film)' in title.lower()
                if not is_film_page:
                    continue

                # 1. Scrape Poster (from Infobox)
                infobox = soup.find('table', class_='infobox')
                if infobox:
                    img_tag = infobox.find('img')
                    if img_tag and img_tag.get('src'):
                        metadata['poster'] = "https:" + img_tag['src']

                # 2. Scrape Description (first viable paragraph)
                for p in soup.find_all('p'):
                    text = p.get_text().strip()
                    # A valid plot description should be reasonably long
                    if len(text) > 150: 
                        clean_text = re.sub(r'\[\d+\]', '', text)
                        metadata['description'] = clean_text
                        break
                            
                # If we got at least a description, consider it a success and stop trying other title variations
                if metadata['description'] != "Synopsis not available.":
                    return metadata

        except Exception as e:
            print(f"Scraper error for {title}: {e}")
            
    return metadata

if __name__ == "__main__":
    # Test script locally
    print("Testing Iron Man:")
    print(get_wikipedia_metadata("Iron Man (2008)"))
    print("\nTesting Toy Story:")
    print(get_wikipedia_metadata("Toy Story (1995)"))
