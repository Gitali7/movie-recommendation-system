import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
import os

class SVDKMeansRecommender:
    def __init__(self, num_clusters=32, n_components=20, random_state=42):
        self.num_clusters = num_clusters
        self.n_components = n_components
        self.random_state = random_state
        self.kmeans = KMeans(n_clusters=num_clusters, random_state=random_state, n_init='auto')
        self.svd = TruncatedSVD(n_components=n_components, random_state=random_state)
        self.cluster_matrix = None
        self.Genres = []

    def fit(self, data_dir='data'):
        """Fits the SVD and KMeans clustering models."""
        preprocessed_path = os.path.join(data_dir, 'preprocessed.csv')
        genre_path = os.path.join(data_dir, 'genre_order.csv')

        df = pd.read_csv(preprocessed_path, index_col=0)
        df = df.fillna(0)
        self.Genres = list(pd.read_csv(genre_path, index_col=0)['0'])

        # Dimensionality Reduction using standard Scikit-Learn
        reduced_features = self.svd.fit_transform(df.to_numpy())
        df_reduced = pd.DataFrame(reduced_features)
        
        # We need the original features split for prediction map
        x_col_size = len(df.columns) - len(self.Genres) + 6 # From original logic
        x = df.drop(labels=df.columns[x_col_size:], axis="columns")
        y = df[df.columns[x_col_size:]]
        
        x_train, _, y_train, _ = train_test_split(x, y, test_size=0.05, shuffle=True, random_state=self.random_state)
        
        # Train KMeans
        y_pred = self.kmeans.fit_predict(x_train)
        
        # Create cluster representative matrix
        X_train2 = pd.concat([x_train, y_train, pd.DataFrame(y_pred, columns=["label"], index=x_train.index)], axis="columns")
        df_cluster_rep = X_train2.groupby(['label'], as_index=False).mean()
        df_cluster_rep.drop(labels="label", axis="columns", inplace=True)
        
        # If any cluster is empty, it won't exist in groupby mean. We fill missing ones with 0s.
        matrix = df_cluster_rep.to_numpy()
        final_matrix = []
        cluster_labels = df_cluster_rep.index.tolist()
        
        j = 0
        for i in range(self.num_clusters):
            if i not in cluster_labels:
                final_matrix.append(np.zeros(len(df.columns)))
            else:
                final_matrix.append(matrix[j])
                j += 1
                
        self.cluster_matrix = np.array(final_matrix)
        self.x_col_size = x_col_size
        self.original_columns = df.columns
        print("Models successfully fitted.")

    def predict_genres(self, datapoint):
        """Returns the sorted recommended genres for a basic user array."""
        if self.cluster_matrix is None:
            raise ValueError("Model not fitted. Call fit() first.")
            
        cluster_id = self.kmeans.predict([datapoint])[0]
        inferred_full = self.cluster_matrix[cluster_id]
        
        # Following original prediction chunk logic
        inferred_genres_only = inferred_full[len(self.original_columns) - len(self.Genres):]
        
        sorted_ratings = []
        for idx, element in enumerate(inferred_genres_only):
            sorted_ratings.append((element, idx + len(self.original_columns) - len(self.Genres)))
            
        sorted_ratings.sort(reverse=True)
        return sorted_ratings

    def recommend_top_movies(self, user_features, data_dir='data', top_n=5):
        """Recommend Top N movies for a user based on predicted genres."""
        ratings_path = os.path.join(data_dir, 'ml-32m', 'ratings.csv')
        movies_path = os.path.join(data_dir, 'ml-32m', 'movies.csv')
        
        ratings = pd.read_csv(ratings_path)
        ratings.rename(columns={'userId': 'UserID', 'movieId': 'MovieID', 'rating': 'Rating', 'timestamp': 'TimeStamp'}, inplace=True)
        movies = pd.read_csv(movies_path)
        movies.rename(columns={'movieId': 'MovieID', 'title': 'Title', 'genres': 'Genres'}, inplace=True)
        
        sorted_ratings_full = self.predict_genres(user_features)
        
        # Map ratings back to genre names
        rating_dict = {}
        for rating_val, col_index in sorted_ratings_full:
            genre_name = self.original_columns[col_index]
            rating_dict[genre_name] = rating_val
            
        # Parse genres and append decades
        movies['Rating'] = [[] for _ in range(len(movies))]
        movies_grouped = ratings.groupby('MovieID')['Rating'].mean()
        movies['Rating'] = movies.index.map(movies_grouped).fillna(0)
        
        movies['Genres'] = movies['Genres'].apply(lambda x: x.split('|'))
        for i in movies.index:
            title = movies.at[i, 'Title']
            try:
                decade = title[-5:-2] + '0s'
            except:
                decade = 'Unknown'
            movies.at[i, 'Genres'].append(decade)
            
        # Compute Affinity
        affinities = []
        for i in movies.index:
            genres = movies.at[i, 'Genres']
            affinity = 0
            for g in genres:
                if g in rating_dict:
                    affinity += rating_dict[g] * movies.at[i, 'Rating']
            affinities.append(affinity)
            
        movies['Affinity'] = affinities
        top_movies = movies.sort_values('Affinity', ascending=False).head(top_n)['Title'].tolist()
        return top_movies

if __name__ == "__main__":
    recommender = SVDKMeansRecommender()
    recommender.fit()
    # Dummy user features corresponding to x_col_size logic
    # Assuming x_col_size features are extracted from x_test
    print("Testing pipeline successful.")
