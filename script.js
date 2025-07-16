// Modern Chinese Tech Weekly Navigator
class TechWeeklyNavigator {
    constructor() {
        this.data = [];
        this.filteredData = [];
        this.currentCategory = 'all';
        this.searchTerm = '';
        
        this.init();
    }

    async init() {
        await this.loadData();
        this.setupEventListeners();
        this.render();
    }

    async loadData() {
        try {
            const response = await fetch('README.json');
            this.data = await response.json();
            this.filteredData = [...this.data];
        } catch (error) {
            console.error('Failed to load data:', error);
            this.showError('加载数据失败，请刷新页面重试。');
        }
    }

    setupEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('search');
        searchInput.addEventListener('input', this.debounce(this.handleSearch.bind(this), 300));
        
        // Keyboard shortcut for search
        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey) {
                e.preventDefault();
                searchInput.focus();
            }
        });

        // Category filtering
        document.getElementById('category-filter').addEventListener('click', (e) => {
            if (e.target.classList.contains('tag')) {
                this.handleCategoryFilter(e.target);
            }
        });
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    handleSearch(e) {
        this.searchTerm = e.target.value.toLowerCase().trim();
        this.filterData();
    }

    handleCategoryFilter(button) {
        // Update active state
        document.querySelectorAll('.tag').forEach(tag => tag.classList.remove('active'));
        button.classList.add('active');
        
        this.currentCategory = button.dataset.category;
        this.filterData();
    }

    filterData() {
        let filtered = [...this.data];

        // Filter by category
        if (this.currentCategory !== 'all') {
            filtered = filtered.filter(category => category.category === this.currentCategory);
        }

        // Filter by search term
        if (this.searchTerm) {
            filtered = filtered.map(category => ({
                ...category,
                feeds: category.feeds.filter(feed => 
                    feed.name.toLowerCase().includes(this.searchTerm) ||
                    feed.desc.toLowerCase().includes(this.searchTerm) ||
                    this.extractText(feed.latest_post).toLowerCase().includes(this.searchTerm) ||
                    category.category.toLowerCase().includes(this.searchTerm)
                )
            })).filter(category => category.feeds.length > 0);
        }

        this.filteredData = filtered;
        this.renderGrid();
    }

    extractText(markdown) {
        if (!markdown) return '';
        const match = markdown.match(/\[([^\]]+)\]\([^)]+\)/);
        return match ? match[1] : markdown;
    }

    extractUrl(markdown) {
        if (!markdown) return '';
        const match = markdown.match(/\[([^\]]+)\]\(([^)]+)\)/);
        return match ? match[2] : markdown;
    }

    isRecentlyPublished(dateString, days = 7) {
        if (!dateString) return false;
        
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        return diffDays <= days;
    }

    formatDate(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays <= 1) return '今天';
        if (diffDays <= 2) return '昨天';
        if (diffDays <= 7) return `${diffDays}天前`;
        
        return date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    render() {
        this.renderStats();
        this.renderCategories();
        this.renderGrid();
    }

    renderStats() {
        const totalCount = this.data.reduce((sum, category) => sum + category.feeds.length, 0);
        const categoryCount = this.data.length;
        const updatedCount = this.data.reduce((sum, category) => 
            sum + category.feeds.filter(feed => this.isRecentlyPublished(feed.published_date)).length, 0
        );

        document.getElementById('total-count').textContent = totalCount;
        document.getElementById('category-count').textContent = categoryCount;
        document.getElementById('updated-count').textContent = updatedCount;
    }

    renderCategories() {
        const categories = this.data.map(item => item.category);
        const filterContainer = document.getElementById('category-filter');
        
        categories.forEach(category => {
            const button = document.createElement('button');
            button.className = 'tag';
            button.dataset.category = category;
            button.textContent = category;
            filterContainer.appendChild(button);
        });
    }

    renderGrid() {
        const grid = document.getElementById('weekly-grid');
        const noResults = document.getElementById('no-results');
        
        // Clear previous content
        grid.innerHTML = '';
        
        const totalFeeds = this.filteredData.reduce((sum, category) => sum + category.feeds.length, 0);
        
        if (totalFeeds === 0) {
            noResults.classList.remove('hidden');
            return;
        }
        
        noResults.classList.add('hidden');

        // Render feeds with staggered animation
        let delay = 0;
        this.filteredData.forEach(category => {
            category.feeds.forEach(feed => {
                const card = this.createCard(feed, category.category);
                card.style.animationDelay = `${delay}ms`;
                grid.appendChild(card);
                delay += 50;
            });
        });
    }

    createCard(feed, category) {
        const card = document.createElement('article');
        card.className = 'card';
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.animation = 'fadeInUp 0.5s ease forwards';

        const isNew = this.isRecentlyPublished(feed.published_date);
        const latestPostText = this.extractText(feed.latest_post);
        const latestPostUrl = this.extractUrl(feed.latest_post);
        const linkUrl = this.extractUrl(feed.link);

        card.innerHTML = `
            <div class="card-header">
                ${isNew ? '<span class="new-badge">本周更新</span>' : ''}
                <span class="card-category">${category}</span>
                <h3 class="card-title">${feed.name}</h3>
                <p class="card-description">${feed.desc || '暂无描述'}</p>
            </div>
            
            <div class="card-meta">
                ${feed.published_date ? `<p class="publish-date">最近更新: ${this.formatDate(feed.published_date)}</p>` : ''}
                
                ${latestPostText && latestPostText !== feed.name ? `
                    <div class="latest-post">
                        <div class="latest-post-title">最新文章</div>
                        <a href="${latestPostUrl}" target="_blank" rel="noopener noreferrer" class="latest-post-link">
                            ${latestPostText}
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M7 17L17 7"></path>
                                <path d="M7 7h10v10"></path>
                            </svg>
                        </a>
                    </div>
                ` : ''}
            </div>
            
            <div class="card-footer">
                <a href="${linkUrl}" target="_blank" rel="noopener noreferrer" class="visit-link">
                    访问周刊
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M7 17L17 7"></path>
                        <path d="M7 7h10v10"></path>
                    </svg>
                </a>
            </div>
        `;

        return card;
    }

    showError(message) {
        const grid = document.getElementById('weekly-grid');
        grid.innerHTML = `
            <div class="error" style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--error-500);">
                <h3>加载失败</h3>
                <p>${message}</p>
            </div>
        `;
    }
}

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new TechWeeklyNavigator();
});

// Service Worker registration for PWA (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => console.log('SW registered'))
            .catch(registrationError => console.log('SW registration failed'));
    });
}