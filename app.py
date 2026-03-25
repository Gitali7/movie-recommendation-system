from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import os
import difflib

# Internal Models & Utils
from src.models.collaborative import CollaborativeFilter
from src.utils.scraper import get_wikipedia_metadata

app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# Initialize models at startup
print("Initialize Collaborative Filter...")
cf_model = CollaborativeFilter(data_dir=DATA_DIR)
cf_model.load_and_prepare()


# Load basic movie list for search
movies_path = os.path.join(DATA_DIR, 'ml-32m', 'movies.csv')
movies_df = pd.read_csv(movies_path)
movies_df.rename(columns={'movieId': 'MovieID', 'title': 'Title', 'genres': 'Genres'}, inplace=True)
all_titles = movies_df['Title'].tolist()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/search', methods=['GET'])
def search_movie():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"error": "No query provided"}), 400

    query_lower = query.lower()
    
    # 1. Exact or starts-with matches
    starts_with = [t for t in all_titles if t.lower().startswith(query_lower)]
    
    # 2. General substring matches
    contains_match = [t for t in all_titles if query_lower in t.lower() and t not in starts_with]
    
    # Sort them by length so exact/shortest titles bubble to the top!
    starts_with.sort(key=len)
    contains_match.sort(key=len)
    
    all_matches = starts_with + contains_match
    
    if all_matches:
        closest_matches = all_matches[:5]
    else:
        # Fallback keyword fuzzy search
        closest_matches = difflib.get_close_matches(query, all_titles, n=5, cutoff=0.6)
    
    results = []
    for match in closest_matches:
        movie_row = movies_df[movies_df['Title'] == match].iloc[0]
        results.append({
            "id": int(movie_row['MovieID']),
            "title": movie_row['Title'],
            "genres": movie_row['Genres'].split('|')
        })
        
    return jsonify(results)


@app.route('/api/recommend/collaborative', methods=['GET'])
def recommend_collaborative():
    movie_id = request.args.get('movie_id', type=int)
    if not movie_id:
        return jsonify({"error": "movie_id required"}), 400
        
    title = cf_model.get_movie_title(movie_id)
    if title == "Unknown Movie":
        return jsonify({"error": "Movie not found"}), 404
        
    sim_ids = cf_model.find_similar_movies(movie_id, k=10)
    
    results = []
    for sid in sim_ids:
        movie_row = movies_df[movies_df['MovieID'] == sid].iloc[0]
        results.append({
            "id": int(movie_row['MovieID']),
            "title": movie_row['Title'],
            "genres": movie_row['Genres'].split('|')
        })
        
    return jsonify({
        "source_title": title,
        "recommendations": results
    })

@app.route('/api/explore', methods=['GET'])
def explore_mood():
    mood = request.args.get('mood', 'all').lower()
    era = request.args.get('era', 'all').lower()
    
    # Emotion to Genre Mapping
    mood_map = {
        'happy': ['Comedy', 'Animation', 'Adventure'],
        'sad': ['Drama', 'Romance'],
        'angry': ['Action', 'Thriller', 'Crime'],
        'relaxed': ['Documentary', 'Fantasy'],
        'spooky': ['Horror', 'Mystery']
    }
    
    # 1. Filter by Mood/Genres
    if mood in mood_map:
        target_genres = mood_map[mood]
        genre_pattern = '|'.join(target_genres)
        filtered_df = movies_df[movies_df['Genres'].str.contains(genre_pattern, case=False, na=False)].copy()
    else:
        filtered_df = movies_df.copy()
        
    # 2. Filter by Era
    filtered_df['Year'] = filtered_df['Title'].str.extract(r'\((\d{4})\)').astype(float)
    
    if era == 'classics':
        filtered_df = filtered_df[filtered_df['Year'] < 1980]
    elif era == '80s90s':
        filtered_df = filtered_df[(filtered_df['Year'] >= 1980) & (filtered_df['Year'] < 2000)]
    elif era == 'modern':
        filtered_df = filtered_df[(filtered_df['Year'] >= 2000) & (filtered_df['Year'] < 2010)]
    elif era == 'recent':
        filtered_df = filtered_df[filtered_df['Year'] >= 2010]
        
    if filtered_df.empty:
        return jsonify([])
        
    # 3. Sample 10 random movies
    sample_size = min(10, len(filtered_df))
    final_sample = filtered_df.sample(n=sample_size)
    
    results = []
    for _, row in final_sample.iterrows():
        results.append({
            "id": int(row['MovieID']),
            "title": row['Title'],
            "genres": row['Genres'].split('|')
        })
        
    return jsonify({
        "time_of_day": f"{mood.capitalize()} {era.capitalize()}",
        "recommendations": results
    })
@app.route('/api/metadata', methods=['GET'])
def get_metadata():
    title = request.args.get('title', '')
    lang = request.args.get('lang', 'en')
    if not title:
        return jsonify({"error": "No title provided"}), 400
        
    metadata = get_wikipedia_metadata(title, lang)
    return jsonify(metadata)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
