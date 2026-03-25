import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
import os

class CollaborativeFilter:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.X = None
        self.user_mapper = {}
        self.movie_mapper = {}
        self.movie_inv_mapper = {}
        self.df1 = None # Movies
        self.df2 = None # Ratings
        
    def load_and_prepare(self):
        """Loads data and creates utility matrix."""
        movies_path = os.path.join(self.data_dir, 'ml-32m', 'movies.csv')
        ratings_path = os.path.join(self.data_dir, 'ml-32m', 'ratings.csv')
        
        self.df1 = pd.read_csv(movies_path)
        self.df1.rename(columns={'movieId': 'MovieID', 'title': 'Title', 'genres': 'Genres'}, inplace=True)
        # 32M ratings might be large, but Pandas handles 32M rows natively on most hardware 
        self.df2 = pd.read_csv(ratings_path)
        self.df2.rename(columns={'userId': 'UserID', 'movieId': 'MovieID', 'rating': 'Rating', 'timestamp': 'Timestamp'}, inplace=True)
        
        M = self.df2['UserID'].nunique()
        N = self.df2['MovieID'].nunique()

        self.user_mapper = dict(zip(np.unique(self.df2["UserID"]), list(range(M))))
        self.movie_mapper = dict(zip(np.unique(self.df2["MovieID"]), list(range(N))))
        self.movie_inv_mapper = dict(zip(list(range(N)), np.unique(self.df2["MovieID"])))

        # Vectorized mapping for 32M rows - extremely fast compared to list comprehensions
        user_index = self.df2['UserID'].map(self.user_mapper).values
        item_index = self.df2['MovieID'].map(self.movie_mapper).values

        self.X = csr_matrix((self.df2["Rating"], (user_index, item_index)), shape=(M, N))
        print("Collaborative Data Prepared.")

    def find_similar_movies(self, movie_id, k=10, metric='cosine'):
        """Finds k-nearest neighbours for a given movie id."""
        if self.X is None:
            self.load_and_prepare()
            
        X_T = self.X.T
        neighbour_ids = []

        try:
            movie_ind = self.movie_mapper[movie_id]
        except KeyError:
            return [] # Movie not found in ratings
            
        movie_vec = X_T[movie_ind]
        if isinstance(movie_vec, (np.ndarray)):
            movie_vec = movie_vec.reshape(1,-1)
            
        kNN = NearestNeighbors(n_neighbors=k+1, algorithm="brute", metric=metric)
        kNN.fit(X_T)
        neighbour = kNN.kneighbors(movie_vec, return_distance=False)
        
        for i in range(0, k):
            n = neighbour.item(i)
            neighbour_ids.append(self.movie_inv_mapper[n])
            
        neighbour_ids.pop(0) # Remove self
        return neighbour_ids

    def get_movie_title(self, movie_id):
        titles = self.df1[self.df1['MovieID'] == movie_id]['Title'].values
        return titles[0] if len(titles) > 0 else "Unknown Movie"

if __name__ == "__main__":
    cf = CollaborativeFilter()
    cf.load_and_prepare()
    sim = cf.find_similar_movies(1, k=5)
    title = cf.get_movie_title(1)
    print(f"Because you watched {title}:")
    for sim_id in sim:
        print(cf.get_movie_title(sim_id))
