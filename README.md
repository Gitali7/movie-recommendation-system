# AI Movie Recommendation System 🎬

Welcome to the **Movie Recommendation System**! This project is designed to act just like Netflix or Amazon Prime—it figures out what movies you might like based on data and patterns, and recommends them to you in a beautiful, interactive web app!

Even if you have **zero programming knowledge**, this guide will help you understand **why** we built this, **how** it works, **what** data we use, and exactly **how you can run it yourself**.

---

## 🌟 Why Did We Build This?
The goal of this project is to create a smart engine that helps people discover new movies. With millions of movies out there, it's hard to know what to watch next. 

By analyzing massive amounts of data—such as how other users rated movies, what genres exist, and even what time of day it is—this system provides **highly personalized recommendations** tailored specifically to what you are looking for.

### What Does the App Actually Do?
When you start the application, you'll be presented with a modern, glass-like website where you can:
1. **Search for any movie** (e.g., *Toy Story*).
2. The AI will instantly analyze 32 million data points and show you a list of **similar movies** that people who liked your searched movie also enjoyed.
3. You can click to **Play the Trailer** directly on YouTube!
4. You can also **Explore by Mood and Era** (e.g., "Find me Happy movies from the 80s"). The AI will filter the perfect movies for your vibe.

---

## 🧠 How Does It Work? (The Methodology)

We use powerful Machine Learning (AI) techniques to understand movies. We didn't just hard-code rules; the system *learns* the relationships between movies automatically.

Here are the main **Methods** we use behind the scenes:

1. **Item-Item Collaborative Filtering**: 
   - *How it works:* "If you liked Movie A, and lots of other people who liked Movie A *also* liked Movie B... we will recommend Movie B to you!"
   - *Under the hood:* It calculates mathematical distances (Cosine Similarity) between movies based on thousands of users' ratings to find the "closest" matches.
   
2. **Temporal & Mood Recommendations**:
   - *How it works:* We categorize movies by "Era" (Classic, 80s, Modern) and map human "Moods" (Happy, Spooky, Sad) to specific movie genres (Comedy, Horror, Drama). The system filters the massive database dynamically based on your dropdown selections to give you the perfect movie for your current vibe.

3. **Live Web Scraping (Wikipedia & YouTube)**:
   - *How it works:* We don't store movie posters or synopses locally because it would take up too much space!
   - *Under the hood:* When the app recommends a movie like *The Matrix*, it acts like a rapid web browser—visiting Wikipedia specifically to grab the movie's Synopsis and Poster Image, and then searching YouTube to find the official trailer link, handing them all back to you instantly!

---

## 📊 What Data Do We Use?

To teach our AI, we used one of the most famous datasets in the world:
**The MovieLens 32M Dataset.**

- **Size:** It contains over **32 million ratings** and **2 million tags** applied to **87,000 movies** by **200,000 users**.
- **Source:** Created by the GroupLens Research group at the University of Minnesota.

Our AI reads this massive dataset, finds the hidden patterns in how users vote, and learns which movies share similar audiences. Because the raw dataset is almost 1 Gigabyte large, our system automatically compresses and processes it into a smaller `preprocessed.csv` file to make our web app lightning fast!

---

## 📁 Project Structure & Technical Deep Dive

Here is exactly how the codebase is organized, and the specific functions that drive it:

```text
Movie-Recommendation-System/
│
├── data/                       # 🗄️ Stores the raw MovieLens data and preprocessed vectors.
│
├── src/                        # ⚙️ The core Python Engine.
│   ├── models/
│   │   └── collaborative.py    # Powers the AI recommendation logic.
│   │       - Class: `CollaborativeFilter`
│   │       - Method: `load_and_prepare()` Uses pandas to load 32M ratings, and SciPy's `csr_matrix` to build a sparse utility matrix to save RAM.
│   │       - Method: `find_similar_movies()` Uses scikit-learn's `NearestNeighbors` (kNN) algorithm with 'cosine' distance to find mathematical similarities between user ratings.
│   │
│   └── utils/
│       └── scraper.py          # The live web-scraping utility.
│           - Method: `get_wikipedia_metadata()` Uses `BeautifulSoup` to scrape Wikipedia's DOM for `<p>` text summaries and `<img>` posters. Uses `youtubesearchpython` to find trailers dynamically.
│
├── static/                     # 🎨 UI Logic & Styling
│   ├── style.css               # Defines modern "glassmorphism" variables, CSS Grid layouts, and CSS keyframe animations (like orb floating).
│   └── script.js               # Frontend JavaScript logic.
│       - Function: `getCollaborative()` Fetches recommendations asynchronously from our Flask backend.
│       - Function: `createMovieCard()` Dynamically builds DOM elements and handles tooltip visibility and trailer popup logic.
│
├── templates/                  
│   └── index.html              # 🖼️ Frontend View. Built with HTML5 semantics, providing the Search Box and 'Explore by Mood' dropdowns. 
│
└── app.py                      # 🌐 The Flask Backend Server.
    - Route: `/api/search` uses fuzzy matching (`difflib.get_close_matches`) to autocomplete user searches.
    - Route: `/api/recommend/collaborative` invokes our kNN ML model class.
    - Route: `/api/explore` parses user input locally via Pandas dataframe filtering based on year boundaries and genre substring matches.
```

---

## 🚀 Step-by-Step Guide to Running the App

Running the project is incredibly easy! Just follow these steps on your computer:

### Step 1: Install Python
Ensure you have **Python** installed on your computer. You can download it from [python.org](https://www.python.org/).

### Step 2: Open Your Terminal
Open your computer's `Terminal` (Mac/Linux) or `Command Prompt / PowerShell` (Windows) and open the folder containing this project:
```bash
cd path/to/Movie-Recommendation-System
```

### Step 3: Install the "Grocery List" (Dependencies)
We need to download a few code libraries (like Pandas for data and Flask for the web server). Run this command:
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application!
Now, you just turn on the web server. Run this command:
```bash
python app.py
```
*(Wait a few seconds while the AI loads the millions of data points into its memory)*

### Step 5: Open Your Web Browser
When the terminal says `Running on http://127.0.0.1:5000`, open your web browser (like Chrome, Edge, or Safari) and go to that exact web address: 
👉 **http://127.0.0.1:5000**

**Congratulations! You are now running an AI Movie Recommender! 🎉** 

Search for a classic movie, pick your language, and watch the AI do its magic!
