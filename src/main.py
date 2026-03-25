import argparse
import sys
import os

from src.data.preprocessing import run_preprocessing
from src.models.svd_kmeans import SVDKMeansRecommender
from src.models.collaborative import CollaborativeFilter
from src.models.temporal_hybrid import TemporalHybridRecommender

def main():
    parser = argparse.ArgumentParser(description="Movie Recommendation System CLI")
    parser.add_argument('--action', type=str, choices=['preprocess', 'recommend_svd', 'recommend_collaborative', 'recommend_temporal'], required=True, help="Action to perform")
    parser.add_argument('--movie_id', type=int, help="MovieID for collaborative filtering (e.g., 1 for Toy Story)")
    
    args = parser.parse_args()
    
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    if args.action == 'preprocess':
        print("Running Preprocessing Pipeline...")
        run_preprocessing(data_dir=data_dir)
        
    elif args.action == 'recommend_svd':
        print("Running SVD + KMeans Recommendation...")
        print("Note: In a full production system, you would pass a specific user feature vector.")
        print("Demonstrating pipeline fit...")
        recommender = SVDKMeansRecommender()
        recommender.fit(data_dir=data_dir)
        print("Pipeline is capable of predicting genres based on user input features.")
        
    elif args.action == 'recommend_collaborative':
        if not args.movie_id:
            print("Error: --movie_id is required for collaborative filtering")
            sys.exit(1)
            
        print(f"Running Collaborative Filtering for Movie ID {args.movie_id}...")
        cf = CollaborativeFilter(data_dir=data_dir)
        cf.load_and_prepare()
        title = cf.get_movie_title(args.movie_id)
        if title == "Unknown Movie":
            print(f"Error: Movie ID {args.movie_id} not found in database.")
            sys.exit(1)
            
        sim = cf.find_similar_movies(args.movie_id, k=10)
        print(f"\nBecause you watched '{title}':")
        for sim_id in sim:
            print(f"- {cf.get_movie_title(sim_id)}")
            
    elif args.action == 'recommend_temporal':
        print("Running Temporal Recommendations (Based on time of day)...")
        tr = TemporalHybridRecommender(data_dir=data_dir)
        print(f"Current Time of Day: {tr.get_time_of_day()}")
        recs = tr.recommend_temporal(10)
        print("\nRecommended Movies:")
        for idx, row in recs.iterrows():
            print(f"- {row['Title']} ({row['Genres']})")

if __name__ == "__main__":
    main()
