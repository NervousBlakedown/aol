// news.js - Handles dynamic news ticker functionality
console.log('News.js loaded');

async function loadNewsTicker(source = "bbc") {
    try {
        const response = await fetch(`/api/news?source=${source}`);
        const data = await response.json();

        const tickerContent = document.getElementById('news-ticker');

        if (response.ok && data.success) {
            tickerContent.innerHTML = data.headlines.map(article =>
                `<span><a href="${article.url}" target="_blank">${article.title}</a></span>`
            ).join('');
        } else {
            console.error('Failed to load news:', data.message);
            tickerContent.innerHTML = '<span>⚠️ Failed to load news headlines.</span>';
        }
    } catch (error) {
        console.error('Error fetching news:', error);
        document.getElementById('news-ticker').innerHTML = '<span>⚠️ Error fetching news.</span>';
    }
}


// Switch feeds based on user selection
document.querySelectorAll('input[name="rss-feed"]').forEach(feed => {
    feed.addEventListener('change', (event) => {
        const selectedFeed = event.target.id; // Get the selected feed URL
        loadNewsTicker(selectedFeed);
    });
});

// Fetch news on page load
document.addEventListener('DOMContentLoaded', () => loadNewsTicker());
    

// Auto-refresh every 2 minutes
setInterval(() => loadNewsTicker(), 120_000);