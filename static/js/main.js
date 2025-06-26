let currentTopic = 'general';
let currentArticleCount = 6;

// Smooth scrolling for anchor links
function scrollToNews() {
    document.getElementById('latest-news').scrollIntoView({ behavior: 'smooth' });
}

function exploreTopics() {
    document.querySelector('.topics-section').scrollIntoView({ behavior: 'smooth' });
}

// Refresh news for a specific topic
async function refreshNews(topicId) {
    const container = document.getElementById('articles-container');
    currentArticleCount = 6; // reset count

    container.innerHTML = `
        <div class="col-12">
            <div class="loading">
                <div class="spinner"></div>
                <p class="mt-3">Loading fresh news...</p>
            </div>
        </div>
    `;

    try {
        const response = await fetch(`/api/articles/${topicId}?count=${currentArticleCount}`);
        const articles = await response.json();

        setTimeout(() => {
            renderArticles(articles, container, true);
            toggleLoadMore(articles.length);
        }, 1000);
    } catch (error) {
        console.error('Error fetching articles:', error);
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    <h4>Oops! Something went wrong</h4>
                    <p>Unable to load fresh news. Please try again later.</p>
                </div>
            </div>
        `;
    }
}

// Load more articles
async function loadMoreArticles(topicId) {
    currentArticleCount += 6;

    try {
        const response = await fetch(`/api/articles/${topicId}?count=${currentArticleCount}`);
        const articles = await response.json();

        const container = document.getElementById('articles-container');
        renderArticles(articles, container, true);
        toggleLoadMore(articles.length);
    } catch (error) {
        console.error('Error loading more articles:', error);
    }
}

// Show or hide Load More button
function toggleLoadMore(articleCount) {
    const loadMoreBtn = document.getElementById('load-more-container');
    if (articleCount < currentArticleCount) {
        loadMoreBtn.style.display = 'none';
    } else {
        loadMoreBtn.style.display = 'block';
    }
}

// Render or append articles in the container
function renderArticles(articles, container, replace = false) {
    const articlesHtml = articles.map((article, index) => `
        <div class="col-lg-6 col-md-6 mb-4">
            <div class="news-card">
                <div class="news-image">
                    <img src="${article.image}" alt="${article.title}" class="img-fluid" onerror="this.src='https://via.placeholder.com/400x250/2563eb/ffffff?text=News';">
                    <div class="news-overlay">
                        <button class="btn btn-light btn-sm share-btn" onclick="shareArticle('${index + 1}')">
                            <i class="fas fa-share-alt"></i> Share
                        </button>
                    </div>
                </div>
                <div class="news-content">
                    <div class="news-meta">
                        <span class="news-source">${article.source}</span>
                        <span class="news-time">${article.time}</span>
                    </div>
                    <h3 class="news-title">${article.title}</h3>
                    <p class="news-summary">${article.summary}</p>
                    <a href="${article.url}" class="btn btn-primary btn-sm read-more-btn" target="_blank" rel="noopener noreferrer">
                        Read More <i class="fas fa-arrow-right ms-1"></i>
                    </a>
                </div>
            </div>
        </div>
    `).join('');

    if (replace) {
        container.innerHTML = articlesHtml;
    } else {
        container.innerHTML += articlesHtml;
    }
}

// Share modal
function shareArticle(articleId) {
    const shareModal = document.createElement('div');
    shareModal.className = 'share-modal';
    shareModal.innerHTML = `
        <div class="share-content">
            <h3><i class="fas fa-share-alt me-2"></i>Share Article</h3>
            <p>Share this news article with your friends and family</p>
            <div class="share-buttons">
                <button class="share-btn-social btn-facebook" onclick="shareToFacebook()">
                    <i class="fab fa-facebook-f me-1"></i> Facebook
                </button>
                <button class="share-btn-social btn-twitter" onclick="shareToTwitter()">
                    <i class="fab fa-twitter me-1"></i> Twitter
                </button>
                <button class="share-btn-social btn-whatsapp" onclick="shareToWhatsApp()">
                    <i class="fab fa-whatsapp me-1"></i> WhatsApp
                </button>
                <button class="share-btn-social btn-copy" onclick="copyToClipboard()">
                    <i class="fas fa-copy me-1"></i> Copy Link
                </button>
            </div>
            <button class="btn btn-secondary mt-3" onclick="closeShareModal()">Close</button>
        </div>
    `;
    document.body.appendChild(shareModal);
    shareModal.addEventListener('click', (e) => {
        if (e.target === shareModal) closeShareModal();
    });
}

function closeShareModal() {
    const modal = document.querySelector('.share-modal');
    if (modal) modal.remove();
}

function shareToFacebook() {
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(window.location.href)}`, '_blank');
    closeShareModal();
}

function shareToTwitter() {
    window.open(`https://twitter.com/intent/tweet?url=${encodeURIComponent(window.location.href)}&text=Check this out!`, '_blank');
    closeShareModal();
}

function shareToWhatsApp() {
    window.open(`https://wa.me/?text=Check this out! ${encodeURIComponent(window.location.href)}`, '_blank');
    closeShareModal();
}

function copyToClipboard() {
    navigator.clipboard.writeText(window.location.href).then(() => {
        showNotification('Link copied to clipboard!', 'success');
        closeShareModal();
    }).catch(() => {
        showNotification('Failed to copy link', 'error');
    });
}

// Notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} notification`;
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        z-index: 1050;
        max-width: 300px;
        animation: slideIn 0.3s ease-out;
    `;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
        ${message}
    `;
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Read more feedback & navbar highlight
document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('read-more-btn') || e.target.closest('.read-more-btn')) {
            showNotification('article opened...', 'info');
            // Do NOT preventDefault() here
        }
    });

    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});


// Auto refresh for topic pages
let autoRefreshInterval;
if (window.location.pathname.includes('/topic/')) {
    startAutoRefresh(10);
}

function startAutoRefresh(minutes = 5) {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
    autoRefreshInterval = setInterval(() => {
        const topicId = window.currentTopic || window.location.pathname.split('/').pop();
        refreshNews(topicId);
    }, minutes * 60000);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
}

window.addEventListener('beforeunload', () => {
    stopAutoRefresh();
});
