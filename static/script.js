// Elements
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const searchResults = document.getElementById('searchResults');
const resultsSection = document.getElementById('resultsSection');
const movieGrid = document.getElementById('movieGrid');
const sourceMovieSpan = document.getElementById('sourceMovie');

// Debounce timer
let debounceTimer;

// Handle Search Input (Autocomplete)
searchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    const query = e.target.value.trim();

    if (query.length < 2) {
        searchResults.classList.add('hidden');
        return;
    }

    debounceTimer = setTimeout(() => {
        fetch(`/api/search?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                searchResults.innerHTML = '';
                if (data.length > 0) {
                    data.forEach(movie => {
                        const li = document.createElement('li');
                        li.innerHTML = `
                            <span class="movie-title">${movie.title}</span>
                            <span class="movie-genre">${movie.genres.slice(0, 3).join(' • ')}</span>
                        `;
                        li.addEventListener('click', () => {
                            searchInput.value = movie.title;
                            searchResults.classList.add('hidden');
                            getCollaborative(movie.id);
                        });
                        searchResults.appendChild(li);
                    });
                    searchResults.classList.remove('hidden');
                } else {
                    searchResults.classList.add('hidden');
                }
            });
    }, 300);
});

// Handle Enter Key for immediate search
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        searchResults.classList.add('hidden');
        searchBtn.click();
    }
});

// Close dropdown on outside click
document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
        searchResults.classList.add('hidden');
    }
});

// Build Movie Card DOM
function createMovieCard(movie) {
    const card = document.createElement('div');
    card.className = 'movie-card';

    // Convert genres array and take max 4
    let genresHtml = '';
    const genres = Array.isArray(movie.genres) ? movie.genres : movie.genres.split('|');
    genres.slice(0, 4).forEach(g => {
        genresHtml += `<span class="genre-pill">${g}</span>`;
    });

    // Guarantee unique IDs if same movie renders twice
    const uniqueHash = Math.random().toString(36).substring(2, 9);
    const uId = `${movie.id}-${uniqueHash}`;

    // Dynamic Trailer Link logic (Fallback if iframe fails)
    const langSelect = document.getElementById('langSelect');
    const langCode = langSelect ? langSelect.value : 'en';
    const langText = langSelect && langSelect.selectedIndex >= 0 ? langSelect.options[langSelect.selectedIndex].text : '';
    const trailerQuery = langText && langCode !== 'en' ? `${movie.title} trailer in ${langText}` : `${movie.title} trailer`;
    const searchQuery = encodeURIComponent(trailerQuery);
    const trailerUrl = `https://www.youtube.com/results?search_query=${searchQuery}`;

    card.innerHTML = `
        <div class="card-poster" id="poster-${uId}">
            <div class="poster-placeholder">
                <span class="icon">🎥</span>
                <span>No Poster<br>Available</span>
            </div>
        </div>
        <div class="card-content">
            <h4>${movie.title} <span class="info-icon">📑 Story<div class="tooltip" id="desc-${uId}">Loading synopsis...</div></span></h4>
            <div class="pill-container">
                ${genresHtml}
            </div>
            <button class="trailer-btn" id="trailer-btn-${uId}" style="margin-top:auto;">▶ Play Trailer</button>
        </div>
    `;

    // 1. Setup Embedded Trailer Button
    const btn = card.querySelector(`#trailer-btn-${uId}`);

    btn.addEventListener('click', () => {
        let ytHref = trailerUrl;
        if (btn.dataset.trailerId) {
            ytHref = `https://www.youtube.com/watch?v=${btn.dataset.trailerId}&autoplay=1`;
        }
        window.open(ytHref, '_blank');
    });

    // 2. Fetch Wikipedia Metadata Lazily
    fetch(`/api/metadata?title=${encodeURIComponent(movie.title)}&lang=${langCode}`)
        .then(res => res.json())
        .then(data => {
            const descEl = card.querySelector(`#desc-${uId}`);
            const posterEl = card.querySelector(`#poster-${uId}`);

            if (data.description) {
                // Truncate long descriptions
                descEl.textContent = data.description.length > 300 ? data.description.substring(0, 300) + "..." : data.description;
            } else {
                descEl.textContent = "Synopsis not available.";
            }

            if (data.poster) {
                posterEl.innerHTML = `<img src="${data.poster}" alt="${movie.title} Poster" class="poster-img" />`;
            }

            if (data.trailer_id) {
                btn.dataset.trailerId = data.trailer_id;
            }
        })
        .catch(() => {
            card.querySelector(`#desc-${uId}`).textContent = "Synopsis not available.";
        });

    return card;
}

// Fetch Collaborative Recommendations
function getCollaborative(movieId) {
    if (!movieId) return;

    // Loading State
    resultsSection.classList.remove('hidden');
    // Hide explore grid to prevent UI clutter
    exploreGrid.classList.add('hidden');
    exploreBadge.classList.add('hidden');

    sourceMovieSpan.textContent = "...";
    movieGrid.innerHTML = `
        <div class="loader-container">
            <div class="spinner"></div>
            <p class="loader-text">Analyzing user interactions...</p>
        </div>
    `;

    fetch(`/api/recommend/collaborative?movie_id=${movieId}`)
        .then(res => {
            if (!res.ok) throw new Error("Could not find movie");
            return res.json();
        })
        .then(data => {
            sourceMovieSpan.textContent = data.source_title;
            movieGrid.innerHTML = '';
            data.recommendations.forEach(rec => {
                movieGrid.appendChild(createMovieCard(rec));
            });

            // Scroll to results
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        })
        .catch(err => {
            movieGrid.innerHTML = `<p style="color:#ef4444;text-align:center;grid-column: 1/-1;">Error: ${err.message}</p>`;
        });
}

// Manual Search Button fallback
searchBtn.addEventListener('click', () => {
    const query = searchInput.value.trim();
    if (!query) return;

    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
            if (data.length > 0) {
                getCollaborative(data[0].id);
            } else {
                alert(`We couldn't find "${query}".\n\nNote: The MovieLens 1M dataset only contains classical movies released up to the year 2000!\n\nTry searching for older classics like "Star Wars", "The Matrix", or "Toy Story".`);
            }
        });
});

// Handle Explore by Mood & Era
const exploreBtn = document.getElementById('exploreBtn');
const moodSelect = document.getElementById('moodSelect');
const eraSelect = document.getElementById('eraSelect');
const exploreGrid = document.getElementById('exploreGrid');
const exploreBadge = document.getElementById('exploreBadge');

exploreBtn.addEventListener('click', () => {
    const mood = moodSelect.value;
    const era = eraSelect.value;

    exploreBadge.classList.remove('hidden');
    exploreBadge.textContent = "Analyzing...";
    exploreGrid.classList.remove('hidden');
    exploreGrid.innerHTML = `
        <div class="loader-container">
            <div class="spinner" style="border-top-color: var(--accent-glow-2);"></div>
            <p class="loader-text">Finding the perfect mood...</p>
        </div>
    `;

    // Hide search results to prevent UI clutter
    resultsSection.classList.add('hidden');

    fetch(`/api/explore?mood=${mood}&era=${era}`)
        .then(res => res.json())
        .then(data => {
            exploreGrid.innerHTML = '';
            if (data.recommendations && data.recommendations.length > 0) {
                exploreBadge.textContent = data.time_of_day;
                data.recommendations.forEach(rec => {
                    exploreGrid.appendChild(createMovieCard(rec));
                });
            } else {
                exploreBadge.textContent = "No Matches";
                exploreGrid.innerHTML = '<p style="color:var(--text-secondary); grid-column:1/-1;">No movies found for this exact mood and era combination.</p>';
            }
        });
});

// Initial Load
window.addEventListener('DOMContentLoaded', () => {
    // Intentionally left blank
});
