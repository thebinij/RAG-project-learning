/* ===== VISUALIZER FEATURE JAVASCRIPT ===== */

// Visualizer-specific utility functions
const VisualizerUtils = {
    
    // Format large numbers with commas
    formatNumber: function(num) {
        return num.toLocaleString();
    },
    
    // Format percentage
    formatPercentage: function(value, total, decimals = 1) {
        if (total === 0) return '0%';
        return `${((value / total) * 100).toFixed(decimals)}%`;
    },
    
    // Show loading spinner
    showLoading: function(elementId, show = true) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = show ? 'block' : 'none';
        }
    },
    
    // Create alert message
    showAlert: function(message, type = 'info', containerId = 'alertContainer') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        container.innerHTML = alertHtml;
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    },
    
    // Debounce function for search inputs
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Format date
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString();
    },
    
    // Format date and time
    formatDateTime: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString();
    },
    
    // Sanitize HTML content
    sanitizeHTML: function(html) {
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    }
};

// Visualizer-specific API functions
const VisualizerApi = {
    
    // Get vector database stats
    async getStats() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch stats:', error);
            throw error;
        }
    },
    
    // Search documents
    async searchDocuments(query, filters = {}) {
        try {
            const response = await fetch('/api/visualizer/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query, filters })
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to search documents:', error);
            throw error;
        }
    },
    
    // Get document metadata
    async getDocumentMetadata() {
        try {
            const response = await fetch('/api/visualizer/metadata');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch document metadata:', error);
            throw error;
        }
    }
};

// Dashboard functionality
const VisualizerDashboard = {
    
    // Initialize dashboard
    init: function() {
        this.loadStats();
        this.setupEventListeners();
        this.startAutoRefresh();
    },
    
    // Setup event listeners
    setupEventListeners: function() {
        // Refresh button
        const refreshBtn = document.getElementById('refreshStatsBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadStats());
        }
    },
    
    // Load statistics
    async loadStats() {
        try {
            VisualizerUtils.showLoading('statsLoading', true);
            const data = await VisualizerApi.getStats();
            this.updateStatsUI(data);
        } catch (error) {
            VisualizerUtils.showAlert('Failed to load statistics', 'danger');
        } finally {
            VisualizerUtils.showLoading('statsLoading', false);
        }
    },
    
    // Update stats UI
    updateStatsUI: function(data) {
        // Update total documents
        const totalDocsElement = document.getElementById('totalDocuments');
        if (totalDocsElement) {
            totalDocsElement.textContent = VisualizerUtils.formatNumber(data.documents || 0);
        }
        
        // Update total chunks
        const totalChunksElement = document.getElementById('totalChunks');
        if (totalChunksElement) {
            totalChunksElement.textContent = VisualizerUtils.formatNumber(data.chunks || 0);
        }
        
        // Update last updated
        const lastUpdatedElement = document.getElementById('lastUpdated');
        if (lastUpdatedElement && data.last_updated) {
            lastUpdatedElement.textContent = VisualizerUtils.formatDateTime(data.last_updated);
        }
        
        // Update status
        const statusElement = document.getElementById('systemStatus');
        if (statusElement) {
            if (data.status === 'operational') {
                statusElement.className = 'badge bg-success';
                statusElement.textContent = 'Operational';
            } else {
                statusElement.className = 'badge bg-warning';
                statusElement.textContent = 'Limited';
            }
        }
    },
    
    // Start auto-refresh
    startAutoRefresh: function() {
        // Refresh stats every 60 seconds
        setInterval(() => {
            this.loadStats();
        }, 60000);
    }
};

// Search functionality
const VisualizerSearch = {
    
    // Initialize search
    init: function() {
        this.setupEventListeners();
        this.loadSearchHistory();
    },
    
    // Setup event listeners
    setupEventListeners: function() {
        const searchForm = document.getElementById('searchForm');
        const searchInput = document.getElementById('searchInput');
        
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.performSearch();
            });
        }
        
        if (searchInput) {
            // Debounced search as user types
            searchInput.addEventListener('input', VisualizerUtils.debounce(() => {
                this.performSearch();
            }, 500));
        }
    },
    
    // Perform search
    async performSearch() {
        const searchInput = document.getElementById('searchInput');
        const query = searchInput ? searchInput.value.trim() : '';
        
        if (!query) {
            this.clearResults();
            return;
        }
        
        try {
            VisualizerUtils.showLoading('searchLoading', true);
            const results = await VisualizerApi.searchDocuments(query);
            this.displaySearchResults(results);
            this.addToSearchHistory(query);
        } catch (error) {
            VisualizerUtils.showAlert('Search failed', 'danger');
        } finally {
            VisualizerUtils.showLoading('searchLoading', false);
        }
    },
    
    // Display search results
    displaySearchResults: function(results) {
        const resultsContainer = document.getElementById('searchResults');
        if (!resultsContainer) return;
        
        if (results && results.length > 0) {
            let html = '';
            results.forEach(result => {
                html += `
                    <div class="result-card">
                        <h5>${VisualizerUtils.sanitizeHTML(result.title || 'Document')}</h5>
                        <p class="content-preview">${VisualizerUtils.sanitizeHTML(result.content.substring(0, 200))}...</p>
                        <div class="metadata-badges">
                            <span class="metadata-badge">Score: ${(result.score * 100).toFixed(1)}%</span>
                            <span class="metadata-badge">${result.metadata?.category || 'Unknown'}</span>
                        </div>
                    </div>
                `;
            });
            resultsContainer.innerHTML = html;
        } else {
            resultsContainer.innerHTML = '<p class="text-muted">No results found.</p>';
        }
    },
    
    // Clear search results
    clearResults: function() {
        const resultsContainer = document.getElementById('searchResults');
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
        }
    },
    
    // Load search history
    loadSearchHistory: function() {
        const history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        this.displaySearchHistory(history);
    },
    
    // Display search history
    displaySearchHistory: function(history) {
        const historyContainer = document.getElementById('searchHistory');
        if (!historyContainer) return;
        
        if (history.length > 0) {
            let html = '<h6>Recent Searches</h6>';
            history.slice(0, 5).forEach(query => {
                html += `<a href="#" class="search-history-item" data-query="${query}">${query}</a>`;
            });
            historyContainer.innerHTML = html;
            
            // Add click handlers
            historyContainer.querySelectorAll('.search-history-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    const query = e.target.dataset.query;
                    const searchInput = document.getElementById('searchInput');
                    if (searchInput) {
                        searchInput.value = query;
                        this.performSearch();
                    }
                });
            });
        } else {
            historyContainer.innerHTML = '<p class="text-muted">No search history</p>';
        }
    },
    
    // Add to search history
    addToSearchHistory: function(query) {
        let history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        history = [query, ...history.filter(q => q !== query)].slice(0, 10);
        localStorage.setItem('searchHistory', JSON.stringify(history));
        this.displaySearchHistory(history);
    }
};

// Document browser functionality
const VisualizerDocuments = {
    
    // Initialize document browser
    init: function() {
        this.loadDocuments();
        this.setupEventListeners();
    },
    
    // Setup event listeners
    setupEventListeners: function() {
        // Filter controls
        const filterInputs = document.querySelectorAll('.document-filter');
        filterInputs.forEach(input => {
            input.addEventListener('change', () => this.applyFilters());
        });
        
        // Sort controls
        const sortSelect = document.getElementById('documentSort');
        if (sortSelect) {
            sortSelect.addEventListener('change', () => this.applySorting());
        }
    },
    
    // Load documents
    async loadDocuments() {
        try {
            VisualizerUtils.showLoading('documentsLoading', true);
            const metadata = await VisualizerApi.getDocumentMetadata();
            this.displayDocuments(metadata);
        } catch (error) {
            VisualizerUtils.showAlert('Failed to load documents', 'danger');
        } finally {
            VisualizerUtils.showLoading('documentsLoading', false);
        }
    },
    
    // Display documents
    displayDocuments: function(documents) {
        const container = document.getElementById('documentsContainer');
        if (!container) return;
        
        if (documents && documents.length > 0) {
            let html = '';
            documents.forEach(doc => {
                html += `
                    <div class="document-card">
                        <h5>${VisualizerUtils.sanitizeHTML(doc.title || 'Untitled')}</h5>
                        <div class="metadata-badges">
                            <span class="metadata-badge">${doc.category || 'Unknown'}</span>
                            <span class="metadata-badge">${doc.chunk_count || 0} chunks</span>
                            <span class="metadata-badge">${VisualizerUtils.formatDate(doc.created_at)}</span>
                        </div>
                        <p class="content-preview">${VisualizerUtils.sanitizeHTML(doc.description || 'No description available')}</p>
                    </div>
                `;
            });
            container.innerHTML = html;
        } else {
            container.innerHTML = '<p class="text-muted">No documents found.</p>';
        }
    },
    
    // Apply filters
    applyFilters: function() {
        // Implementation for filtering documents
        console.log('Applying filters...');
    },
    
    // Apply sorting
    applySorting: function() {
        // Implementation for sorting documents
        console.log('Applying sorting...');
    }
};

// Initialize based on current page
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    
    if (currentPath === '/visualizer') {
        VisualizerDashboard.init();
    } else if (currentPath === '/visualizer/search') {
        VisualizerSearch.init();
    } else if (currentPath === '/visualizer/documents') {
        VisualizerDocuments.init();
    }
});
