/* ===== COST TRACKING FEATURE JAVASCRIPT ===== */

// Cost-specific utility functions
const CostUtils = {
    
    // Format currency with proper decimal places
    formatCurrency: function(amount, decimals = 6) {
        return `$${parseFloat(amount).toFixed(decimals)}`;
    },
    
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
    
    // Download data as file
    downloadFile: function(data, filename, mimeType = 'text/plain') {
        const blob = new Blob([data], { type: mimeType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
};

// Cost-specific API functions
const CostApi = {
    
    // Get cost summary
    async getSummary(days = 30) {
        try {
            const response = await fetch(`/api/v1/costs/summary?days=${days}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch cost summary:', error);
            throw error;
        }
    },
    
    // Get cost breakdown
    async getBreakdown(days = 30) {
        try {
            const response = await fetch(`/api/v1/costs/breakdown?days=${days}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch cost breakdown:', error);
            throw error;
        }
    },
    
    // Get cost efficiency
    async getEfficiency(days = 30) {
        try {
            const response = await fetch(`/api/v1/costs/efficiency?days=${days}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch cost efficiency:', error);
            throw error;
        }
    },
    
    // Get cost alerts
    async getAlerts(threshold = 5.0) {
        try {
            const response = await fetch(`/api/v1/costs/alerts?threshold=${threshold}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch cost alerts:', error);
            throw error;
        }
    },
    
    // Get real-time costs
    async getRealtime() {
        try {
            const response = await fetch('/api/v1/costs/realtime');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch real-time costs:', error);
            throw error;
        }
    },
    
    // Export cost data
    async exportData(format = 'csv', days = 30) {
        try {
            const response = await fetch(`/api/v1/costs/export?format=${format}&days=${days}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.text();
        } catch (error) {
            console.error('Failed to export cost data:', error);
            throw error;
        }
    }
};

// Cost dashboard functionality
const CostDashboard = {
    
    // Initialize dashboard
    init: function() {
        this.loadSummary();
        this.loadBreakdown();
        this.loadEfficiency();
        this.loadAlerts();
        this.setupEventListeners();
        this.startRealtimeUpdates();
    },
    
    // Setup event listeners
    setupEventListeners: function() {
        // Refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshAll());
        }
        
        // Export button
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportData());
        }
        
        // Time period selector
        const timeSelector = document.getElementById('timeSelector');
        if (timeSelector) {
            timeSelector.addEventListener('change', (e) => this.onTimePeriodChange(e.target.value));
        }
    },
    
    // Load cost summary
    async loadSummary() {
        try {
            CostUtils.showLoading('summaryLoading', true);
            const data = await CostApi.getSummary();
            this.updateSummaryUI(data);
        } catch (error) {
            CostUtils.showAlert('Failed to load cost summary', 'danger');
        } finally {
            CostUtils.showLoading('summaryLoading', false);
        }
    },
    
    // Load cost breakdown
    async loadBreakdown() {
        try {
            CostUtils.showLoading('breakdownLoading', true);
            const data = await CostApi.getBreakdown();
            this.updateBreakdownUI(data);
        } catch (error) {
            CostUtils.showAlert('Failed to load cost breakdown', 'danger');
        } finally {
            CostUtils.showLoading('breakdownLoading', false);
        }
    },
    
    // Load cost efficiency
    async loadEfficiency() {
        try {
            CostUtils.showLoading('efficiencyLoading', true);
            const data = await CostApi.getEfficiency();
            this.updateEfficiencyUI(data);
        } catch (error) {
            CostUtils.showAlert('Failed to load cost efficiency', 'danger');
        } finally {
            CostUtils.showLoading('efficiencyLoading', false);
        }
    },
    
    // Load cost alerts
    async loadAlerts() {
        try {
            CostUtils.showLoading('alertsLoading', true);
            const data = await CostApi.getAlerts();
            this.updateAlertsUI(data);
        } catch (error) {
            CostUtils.showAlert('Failed to load cost alerts', 'danger');
        } finally {
            CostUtils.showLoading('alertsLoading', false);
        }
    },
    
    // Update summary UI
    updateSummaryUI: function(data) {
        // Update total cost
        const totalCostElement = document.getElementById('totalCost');
        if (totalCostElement) {
            totalCostElement.textContent = CostUtils.formatCurrency(data.total_cost);
        }
        
        // Update total requests
        const totalRequestsElement = document.getElementById('totalRequests');
        if (totalRequestsElement) {
            totalRequestsElement.textContent = CostUtils.formatNumber(data.total_requests);
        }
        
        // Update total tokens
        const totalTokensElement = document.getElementById('totalTokens');
        if (totalTokensElement) {
            totalTokensElement.textContent = CostUtils.formatNumber(data.total_tokens);
        }
        
        // Update average cost per request
        const avgCostElement = document.getElementById('avgCostPerRequest');
        if (avgCostElement) {
            avgCostElement.textContent = CostUtils.formatCurrency(data.avg_cost_per_request);
        }
    },
    
    // Update breakdown UI
    updateBreakdownUI: function(data) {
        const breakdownContainer = document.getElementById('costBreakdown');
        if (!breakdownContainer) return;
        
        let html = '';
        data.forEach(item => {
            html += `
                <div class="cost-card">
                    <div class="metric-value">${CostUtils.formatCurrency(item.total_cost)}</div>
                    <div class="metric-label">${item.provider} - ${item.model}</div>
                    <small>${CostUtils.formatNumber(item.request_count)} requests</small>
                </div>
            `;
        });
        
        breakdownContainer.innerHTML = html;
    },
    
    // Update efficiency UI
    updateEfficiencyUI: function(data) {
        const efficiencyContainer = document.getElementById('costEfficiency');
        if (!efficiencyContainer) return;
        
        efficiencyContainer.innerHTML = `
            <div class="efficiency-card">
                <div class="metric-value">${CostUtils.formatPercentage(data.cost_efficiency, 100)}</div>
                <div class="metric-label">Cost Efficiency</div>
                <small>${CostUtils.formatNumber(data.efficient_requests)} efficient requests</small>
            </div>
        `;
    },
    
    // Update alerts UI
    updateAlertsUI: function(data) {
        const alertsContainer = document.getElementById('costAlerts');
        if (!alertsContainer) return;
        
        if (data.alerts && data.alerts.length > 0) {
            let html = '';
            data.alerts.forEach(alert => {
                html += `
                    <div class="alert-card">
                        <div class="metric-value">${CostUtils.formatCurrency(alert.cost)}</div>
                        <div class="metric-label">${alert.type} Alert</div>
                        <small>${alert.message}</small>
                    </div>
                `;
            });
            alertsContainer.innerHTML = html;
        } else {
            alertsContainer.innerHTML = '<p class="text-muted">No cost alerts at this time.</p>';
        }
    },
    
    // Refresh all data
    refreshAll: function() {
        this.loadSummary();
        this.loadBreakdown();
        this.loadEfficiency();
        this.loadAlerts();
        CostUtils.showAlert('Cost data refreshed', 'success');
    },
    
    // Export data
    async exportData() {
        try {
            const data = await CostApi.exportData('csv');
            const filename = `cost_analytics_${new Date().toISOString().split('T')[0]}`;
            CostUtils.downloadFile(data, filename, 'text/csv');
            CostUtils.showAlert('Cost data exported successfully', 'success');
        } catch (error) {
            CostUtils.showAlert('Failed to export cost data', 'danger');
        }
    },
    
    // Handle time period change
    onTimePeriodChange: function(days) {
        // Reload data with new time period
        this.loadSummary();
        this.loadBreakdown();
        this.loadEfficiency();
        this.loadAlerts();
    },
    
    // Start real-time updates
    startRealtimeUpdates: function() {
        // Update real-time data every 30 seconds
        setInterval(async () => {
            try {
                const data = await CostApi.getRealtime();
                this.updateRealtimeUI(data);
            } catch (error) {
                console.error('Failed to update real-time data:', error);
            }
        }, 30000);
    },
    
    // Update real-time UI
    updateRealtimeUI: function(data) {
        const realtimeContainer = document.getElementById('realtimeCosts');
        if (!realtimeContainer) return;
        
        realtimeContainer.innerHTML = `
            <div class="cost-card">
                <div class="metric-value">${CostUtils.formatCurrency(data.current_hour_cost)}</div>
                <div class="metric-label">This Hour</div>
                <small>${CostUtils.formatNumber(data.current_hour_requests)} requests</small>
            </div>
        `;
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    CostDashboard.init();
});
