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
    
    // State variables
    currentPage: 1,
    currentLimit: 10,
    currentCategory: '',
    currentFile: '',
    allDocuments: [],
    filteredDocuments: [],
    
    // Initialize document browser
    init: function() {
        this.loadFilters();
        this.loadDocuments();
        this.setupEventListeners();
    },
    
    // Setup event listeners
    setupEventListeners: function() {
        // Filter controls
        const categoryFilter = document.getElementById('categoryFilter');
        const fileFilter = document.getElementById('fileFilter');
        const limitSelect = document.getElementById('limitSelect');
        
        if (categoryFilter) {
            categoryFilter.addEventListener('change', () => {
                this.currentPage = 1;
                this.applyFilters();
            });
        }
        
        if (fileFilter) {
            fileFilter.addEventListener('change', () => {
                this.currentPage = 1;
                this.applyFilters();
            });
        }
        
        if (limitSelect) {
            limitSelect.addEventListener('change', () => {
                this.currentPage = 1;
                this.applyFilters();
            });
        }
    },
    
    // Load filter options
    async loadFilters() {
        try {
            const response = await fetch('/api/visualizer/stats');
            const stats = await response.json();
            
            if (stats.error) return;
            
            // Populate category filter
            const categoryFilter = document.getElementById('categoryFilter');
            if (categoryFilter) {
                categoryFilter.innerHTML = '<option value="">All Categories</option>';
                Object.keys(stats.categories).forEach(category => {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category;
                    categoryFilter.appendChild(option);
                });
            }
            
            // Populate file filter
            const fileFilter = document.getElementById('fileFilter');
            if (fileFilter) {
                fileFilter.innerHTML = '<option value="">All Files</option>';
                Object.keys(stats.files).forEach(file => {
                    const option = document.createElement('option');
                    option.value = file;
                    option.textContent = file;
                    fileFilter.appendChild(option);
                });
            }
            
        } catch (error) {
            console.error('Error loading filters:', error);
        }
    },
    
    // Load documents
    async loadDocuments() {
        try {
            const response = await fetch('/api/visualizer/metadata');
            const data = await response.json();
            
            if (data.error) {
                console.error('Error loading documents:', data.error);
                return;
            }
            
            // Check if data has content (either direct array or wrapped in metadata object)
            const metadataArray = data.metadata || data;
            if (!Array.isArray(metadataArray) || metadataArray.length === 0) {
                this.allDocuments = [];
                this.applyFilters();
                return;
            }
            
            // Transform metadata to document format
            this.allDocuments = metadataArray.map((item, index) => ({
                id: item.id !== undefined ? item.id : index,
                metadata: {
                    title: item.title,
                    category: item.category,
                    file: item.filename,
                    chunk_index: item.chunk_index,
                    total_chunks: item.total_chunks,
                    file_type: item.file_type,
                    conversion_quality: item.conversion_quality,
                    chunk_size: item.chunk_size,
                    content: item.content || ""
                },
                // Use actual content from the API
                text: item.content_preview || item.content || `Chunk ${item.chunk_index + 1} of ${item.total_chunks} from ${item.filename} (${item.chunk_size} characters)`
            }));
            
            this.applyFilters();
            
        } catch (error) {
            console.error('Error loading documents:', error);
        }
    },
    
    // Apply filters
    applyFilters() {
        this.currentCategory = document.getElementById('categoryFilter')?.value || '';
        this.currentFile = document.getElementById('fileFilter')?.value || '';
        this.currentLimit = parseInt(document.getElementById('limitSelect')?.value || '10');
        
        this.filteredDocuments = this.allDocuments.filter(doc => {
            if (this.currentCategory && doc.metadata.category !== this.currentCategory) return false;
            if (this.currentFile && doc.metadata.file !== this.currentFile) return false;
            return true;
        });
        
        this.updateDisplay();
    },
    
    // Update display
    updateDisplay() {
        
        const startIndex = (this.currentPage - 1) * this.currentLimit;
        const endIndex = startIndex + this.currentLimit;
        const pageDocuments = this.filteredDocuments.slice(startIndex, endIndex);
        
        // Update statistics
        const showingCount = document.getElementById('showingCount');
        const totalCount = document.getElementById('totalCount');
        if (showingCount) showingCount.textContent = pageDocuments.length;
        if (totalCount) totalCount.textContent = this.filteredDocuments.length;
        
        // Update filter info
        const filterInfo = document.getElementById('filterInfo');
        if (filterInfo) {
            let filterText = '';
            if (this.currentCategory) filterText += `Category: ${this.currentCategory} `;
            if (this.currentFile) filterText += `File: ${this.currentFile}`;
            filterInfo.textContent = filterText;
        }
        
        // Display documents
        this.displayDocuments(pageDocuments);
        
        // Update pagination
        this.updatePagination();
    },
    
    // Display documents
    displayDocuments(documents) {
        const grid = document.getElementById('documentsGrid');
        if (!grid) return;
        
        grid.innerHTML = '';
        
        if (documents.length === 0) {
            grid.innerHTML = `
                <div class="col-12 text-center">
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        No documents found matching your filters.
                    </div>
                </div>
            `;
            return;
        }
        
        documents.forEach(doc => {
            const card = document.createElement('div');
            card.className = 'col-md-6 col-lg-4 mb-3';
            card.innerHTML = `
                <div class="card document-card h-100" onclick="VisualizerDocuments.showDocumentDetail(${doc.id})">
                    <div class="card-body">
                        <h6 class="card-title text-primary mb-2">
                            ${doc.metadata.title || 'No Title'}
                        </h6>
                        <div class="badge-container">
                            <span class="badge bg-secondary metadata-badge">
                                <i class="fas fa-folder me-1"></i>${doc.metadata.category}
                            </span>
                            <span class="badge bg-info metadata-badge file-badge" title="${doc.metadata.file}">
                                <i class="fas fa-file me-1"></i>
                                <span class="filename-text">${doc.metadata.file}</span>
                            </span>
                            ${doc.metadata.chunk_index !== undefined ? 
                                `<span class="badge bg-warning metadata-badge">
                                    <i class="fas fa-layer-group me-1"></i>${doc.metadata.chunk_index + 1}/${doc.metadata.total_chunks}
                                </span>` : ''
                            }
                        </div>
                        <div class="content-preview">
                            <p class="card-text small">${doc.text}</p>
                        </div>
                    </div>
                    <div class="card-footer text-muted small">
                        <i class="fas fa-eye me-1"></i>Click to view details
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });
    },
    
            // Update pagination
        updatePagination() {
            const totalPages = Math.ceil(this.filteredDocuments.length / this.currentLimit);
            const pagination = document.getElementById('pagination');
            if (!pagination) return;
            
            pagination.innerHTML = '';
            
            if (totalPages <= 1) {
                return;
            }
            
            // Previous button
            const prevLi = document.createElement('li');
            prevLi.className = `page-item ${this.currentPage === 1 ? 'disabled' : ''}`;
            prevLi.innerHTML = `
                <a class="page-link" href="#" onclick="VisualizerDocuments.changePage(${this.currentPage - 1}); return false;">
                    <i class="fas fa-chevron-left"></i>
                </a>
            `;
            pagination.appendChild(prevLi);
            
            // Page numbers
            for (let i = 1; i <= totalPages; i++) {
                if (i === 1 || i === totalPages || (i >= this.currentPage - 2 && i <= this.currentPage + 2)) {
                    const li = document.createElement('li');
                    li.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
                    li.innerHTML = `<a class="page-link" href="#" onclick="VisualizerDocuments.changePage(${i}); return false;">${i}</a>`;
                    pagination.appendChild(li);
                } else if (i === this.currentPage - 3 || i === this.currentPage + 3) {
                    const li = document.createElement('li');
                    li.className = 'page-item disabled';
                    li.innerHTML = '<span class="page-link">...</span>';
                    pagination.appendChild(li);
                }
            }
            
            // Next button
            const nextLi = document.createElement('li');
            nextLi.className = `page-item ${this.currentPage === totalPages ? 'disabled' : ''}`;
            nextLi.innerHTML = `
                <a class="page-link" href="#" onclick="VisualizerDocuments.changePage(${this.currentPage + 1}); return false;">
                    <i class="fas fa-chevron-right"></i>
                </a>
            `;
            pagination.appendChild(nextLi);
        },
    
            // Change page
        changePage(page) {
            if (page < 1) {
                return;
            }
            this.currentPage = page;
            this.updateDisplay();
        },
    
    // Show document detail
    showDocumentDetail(docId) {
        const doc = this.allDocuments.find(d => d.id === docId);
        if (!doc) {
            console.error('Document not found for ID:', docId);
            return;
        }
        
        const container = document.getElementById('documentDetail');
        if (!container) return;
        
        container.innerHTML = `
            <div class="row">
                <div class="col-md-7">
                    <h5 class="text-primary mb-3">${doc.metadata.title || 'No Title'}</h5>
                    <div class="badge-container">
                        <span class="badge bg-secondary metadata-badge me-2">
                            <i class="fas fa-folder me-1"></i>${doc.metadata.category}
                        </span>
                        <span class="badge bg-info metadata-badge file-badge me-2" title="${doc.metadata.file}">
                            <i class="fas fa-file me-1"></i>
                            <span class="filename-text">${doc.metadata.file}</span>
                        </span>
                        ${doc.metadata.chunk_index !== undefined ? 
                            `<span class="badge bg-warning metadata-badge me-2">
                                <i class="fas fa-layer-group me-1"></i>Chunk ${doc.metadata.chunk_index + 1} of ${doc.metadata.total_chunks}
                            </span>` : ''
                        }
                    </div>
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">Content</h6>
                        </div>
                        <div class="card-body">
                            <pre class="mb-0" style="white-space: pre-wrap; font-family: inherit; max-height: 400px; overflow-y: auto;">${doc.metadata.content || doc.text}</pre>
                        </div>
                    </div>
                </div>
                <div class="col-md-5">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">Metadata</h6>
                        </div>
                        <div class="card-body">
                            <dl class="row mb-0">
                                ${Object.entries(doc.metadata).filter(([key, _]) => key !== 'content').map(([key, value]) => `
                                    <dt class="col-sm-5 text-break">${key}:</dt>
                                    <dd class="col-sm-7 text-break">${value}</dd>
                                `).join('')}
                            </dl>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Try to show the modal
        try {
            const modalElement = document.getElementById('documentModal');
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            } else {
                console.error('Modal element not found');
            }
        } catch (error) {
            console.error('Error showing modal:', error);
            // Fallback: try to show modal manually
            const modalElement = document.getElementById('documentModal');
            if (modalElement) {
                modalElement.classList.add('show');
                modalElement.style.display = 'block';
                modalElement.setAttribute('aria-hidden', 'false');
                document.body.classList.add('modal-open');
                
                // Add backdrop
                const backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                document.body.appendChild(backdrop);
            }
        }
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
