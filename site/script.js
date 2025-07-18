class TechWeeklyApp {
    constructor() {
        this.data = [];
        this.filteredData = [];
        this.currentFilter = 'all';
        this.searchQuery = '';
        
        this.init();
    }

    async init() {
        try {
            await this.loadData();
            this.setupEventListeners();
            this.renderUI();
        } catch (error) {
            console.error('Failed to initialize app:', error);
            this.showError('加载数据失败，请稍后重试');
        }
    }

    async loadData() {
        try {
            const response = await fetch('../README.json');
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            this.data = await response.json();
            this.filteredData = this.getAllFeeds();
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('无法加载周刊数据');
        }
    }

    getAllFeeds() {
        const feeds = [];
        this.data.forEach(category => {
            category.feeds.forEach(feed => {
                feeds.push({
                    ...feed,
                    category: category.category
                });
            });
        });
        return feeds;
    }

    setupEventListeners() {
        const searchInput = document.getElementById('searchInput');
        const filterButtons = document.querySelectorAll('.filter-btn');

        searchInput.addEventListener('input', this.debounce(this.handleSearch.bind(this), 300));
        
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                searchInput.value = ''
                this.handleSearch({ target: searchInput });
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && !e.target.matches('input, textarea')) {
                e.preventDefault();
                searchInput.focus();
            }
        });

        filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleFilter(e.target.dataset.category);
                
                filterButtons.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
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

    handleSearch(event) {
        this.searchQuery = event.target.value.toLowerCase().trim();
        this.applyFilters();
    }

    handleFilter(category) {
        this.currentFilter = category;
        this.applyFilters();
    }

    applyFilters() {
        let filtered = this.getAllFeeds();

        if (this.currentFilter !== 'all') {
            filtered = filtered.filter(feed => feed.category === this.currentFilter);
        }

        if (this.searchQuery) {
            filtered = filtered.filter(feed => {
                const searchText = [
                    feed.name,
                    feed.desc,
                    this.parseMarkdownText(feed.latest_post),
                    this.parseMarkdownText(feed.link)
                ].join(' ').toLowerCase();
                
                return searchText.includes(this.searchQuery);
            });
        }

        this.filteredData = filtered;
        this.renderWeeklyGrid();
        this.updateStats();
    }

    parseMarkdownText(markdown) {
        if (!markdown) return '';
        
        const linkRegex = /\[([^\]]+)\]\([^)]+\)/g;
        const imageRegex = /!\[[^\]]*\]\([^)]*\)/g;
        
        return markdown
            .replace(linkRegex, '$1')
            .replace(imageRegex, '')
            .trim();
    }

    parseMarkdownLink(markdown) {
        if (!markdown) return { text: '', url: '' };
        
        const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/;
        const match = markdown.match(linkRegex);
        
        if (match) {
            return {
                text: match[1],
                url: match[2]
            };
        }
        
        const urlRegex = /(https?:\/\/[^\s]+)/;
        const urlMatch = markdown.match(urlRegex);
        
        if (urlMatch) {
            return {
                text: markdown.replace(urlMatch[0], '').trim() || urlMatch[0],
                url: urlMatch[0]
            };
        }
        
        return { text: markdown, url: '' };
    }

    renderUI() {
        this.renderCategories();
        this.renderWeeklyGrid();
        this.updateStats();
    }

    renderCategories() {
        const categories = [...new Set(this.data.map(cat => cat.category))];
        const filterButtons = document.getElementById('filterButtons');
        
        categories.forEach(category => {
            const button = document.createElement('button');
            button.className = 'filter-btn';
            button.dataset.category = category;
            button.textContent = category;
            filterButtons.appendChild(button);
        });
    }

    renderWeeklyGrid() {
        const grid = document.getElementById('weeklyGrid');
        
        if (this.filteredData.length === 0) {
            grid.innerHTML = `
                <div class="loading">
                    <p>未找到匹配的周刊</p>
                    <p style="font-size: 0.875rem; color: var(--text-muted); margin-top: 0.5rem;">
                        尝试调整搜索关键词或筛选条件
                    </p>
                </div>
            `;
            return;
        }

        grid.innerHTML = this.filteredData.map(feed => {
            const isNew = this.isRecentUpdate(feed.published_date);
            const latestPost = this.parseMarkdownLink(feed.latest_post);
            const link = this.parseMarkdownLink(feed.link);
            
            return `
                <div class="weekly-card ${isNew ? 'new' : ''}" data-category="${feed.category}">
                    <div class="weekly-header">
                        <div>
                            <h3 class="weekly-title">${this.escapeHtml(feed.name)}</h3>
                        </div>
                        <span class="weekly-category">${this.escapeHtml(feed.category)}</span>
                    </div>
                    
                    <p class="weekly-description">${this.escapeHtml(feed.desc)}</p>
                    
                    ${latestPost.url ? `
                        <div class="latest-post">
                            <div class="latest-post-title">最新文章</div>
                            <div class="latest-post-content">
                                ${this.renderMarkdownContent(feed.latest_post)}
                            </div>
                        </div>
                    ` : ''}
                    
                    <div class="weekly-links">
                        ${link.url ? `
                            <a href="${this.escapeHtml(link.url)}" 
                               class="weekly-link" 
                               target="_blank" 
                               rel="noopener noreferrer"
                               title="访问 ${this.escapeHtml(feed.name)}">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                                    <polyline points="15 3 21 3 21 9"/>
                                    <line x1="10" y1="14" x2="21" y2="3"/>
                                </svg>
                                访问周刊
                            </a>
                        ` : ''}
                        
                        ${latestPost.url && latestPost.url !== link.url ? `
                            <a href="${this.escapeHtml(latestPost.url)}" 
                               class="weekly-link" 
                               target="_blank" 
                               rel="noopener noreferrer"
                               title="阅读最新文章">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="10"/>
                                    <line x1="12" y1="8" x2="12" y2="16"/>
                                    <line x1="8" y1="12" x2="16" y2="12"/>
                                </svg>
                                最新文章
                            </a>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }

    renderMarkdownContent(markdown) {
        if (!markdown) return '';
        
        let content = markdown;
        
        content = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
        
        content = content.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="height: 1em; vertical-align: middle; margin-left: 0.25rem;">');
        
        return content;
    }

    updateStats() {
        const totalCount = this.filteredData.length;
        const categoryCount = new Set(this.filteredData.map(feed => feed.category)).size;
        const newCount = this.filteredData.filter(feed => this.isRecentUpdate(feed.published_date)).length;

        document.getElementById('totalCount').textContent = totalCount;
        document.getElementById('categoryCount').textContent = categoryCount;
        document.getElementById('newCount').textContent = newCount;
    }

    isRecentUpdate(publishedDate) {
        if (!publishedDate) return false;
        
        try {
            const publishDate = new Date(publishedDate);
            const now = new Date();
            const daysDiff = (now - publishDate) / (1000 * 60 * 60 * 24);
            return daysDiff <= 7;
        } catch {
            return false;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showError(message) {
        const grid = document.getElementById('weeklyGrid');
        grid.innerHTML = `
            <div class="loading">
                <p style="color: #ef4444; margin-bottom: 1rem;">${message}</p>
                <button onclick="location.reload()" style="padding: 0.5rem 1rem; background: var(--primary-color); color: white; border: none; border-radius: var(--radius-md); cursor: pointer;">
                    重新加载
                </button>
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new TechWeeklyApp();
});