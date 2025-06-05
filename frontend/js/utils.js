// Utility functions for Monte Carlo Dashboard

// Format numbers with appropriate precision
function formatNumber(value, decimals = 2) {
    if (typeof value !== 'number' || isNaN(value)) {
        return '-';
    }
    
    if (Math.abs(value) > 1e6) {
        return value.toExponential(decimals);
    } else if (Math.abs(value) < 0.001 && value !== 0) {
        return value.toExponential(decimals);
    } else {
        return value.toFixed(decimals);
    }
}

// Format large numbers with commas
function formatLargeNumber(value) {
    if (typeof value !== 'number' || isNaN(value)) {
        return '-';
    }
    return value.toLocaleString();
}

// Format percentage
function formatPercentage(value, decimals = 2) {
    if (typeof value !== 'number' || isNaN(value)) {
        return '-';
    }
    return (value * 100).toFixed(decimals) + '%';
}

// Format currency
function formatCurrency(value) {
    if (typeof value !== 'number' || isNaN(value)) {
        return '-';
    }
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

// Debounce function for input events
function debounce(func, wait) {
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

// Throttle function for frequent events
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Download data as file
function downloadData(data, filename, type = 'application/json') {
    const blob = new Blob([data], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Convert JSON to CSV
function jsonToCSV(data) {
    if (!Array.isArray(data) || data.length === 0) {
        return '';
    }
    
    const headers = Object.keys(data[0]);
    const csv = [
        headers.join(','),
        ...data.map(row => 
            headers.map(header => {
                const value = row[header];
                // Escape values containing commas or quotes
                if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                    return `"${value.replace(/"/g, '""')}"`;
                }
                return value;
            }).join(',')
        )
    ].join('\n');
    
    return csv;
}

// Calculate statistics from array
function calculateStats(arr) {
    if (!Array.isArray(arr) || arr.length === 0) {
        return {
            mean: 0,
            std: 0,
            min: 0,
            max: 0,
            median: 0
        };
    }
    
    const sorted = [...arr].sort((a, b) => a - b);
    const n = sorted.length;
    
    const mean = arr.reduce((sum, val) => sum + val, 0) / n;
    const variance = arr.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (n - 1);
    const std = Math.sqrt(variance);
    
    return {
        mean: mean,
        std: std,
        min: sorted[0],
        max: sorted[n - 1],
        median: n % 2 === 0 ? (sorted[n/2 - 1] + sorted[n/2]) / 2 : sorted[Math.floor(n/2)]
    };
}

// Validate numeric input
function validateNumericInput(input, min = null, max = null) {
    const value = parseFloat(input.value);
    
    if (isNaN(value)) {
        input.classList.add('error');
        return false;
    }
    
    if (min !== null && value < min) {
        input.classList.add('error');
        return false;
    }
    
    if (max !== null && value > max) {
        input.classList.add('error');
        return false;
    }
    
    input.classList.remove('error');
    return true;
}

// Add input validation listeners
function addValidationListeners() {
    const numericInputs = document.querySelectorAll('input[type="number"]');
    numericInputs.forEach(input => {
        input.addEventListener('input', () => {
            const min = input.hasAttribute('min') ? parseFloat(input.min) : null;
            const max = input.hasAttribute('max') ? parseFloat(input.max) : null;
            validateNumericInput(input, min, max);
        });
    });
}

// Initialize tooltips or help text
function initializeTooltips() {
    // Add tooltips to parameter labels
    const tooltips = {
        'volatility': 'Annual volatility of the asset (standard deviation of returns)',
        'riskFreeRate': 'Risk-free interest rate (e.g., treasury bond yield)',
        'burnIn': 'Number of initial samples to discard before collecting results',
        'stepSize': 'Controls the proposal distribution width - larger values explore more but may reduce acceptance rate',
        'confidenceLevel': 'Probability level for VaR calculation (e.g., 0.95 means 95% of outcomes are better than VaR)'
    };
    
    Object.entries(tooltips).forEach(([id, text]) => {
        const element = document.querySelector(`label[for="${id}"]`);
        if (element) {
            element.title = text;
            element.style.cursor = 'help';
        }
    });
}

// Export functions as needed
window.utils = {
    formatNumber,
    formatLargeNumber,
    formatPercentage,
    formatCurrency,
    debounce,
    throttle,
    downloadData,
    jsonToCSV,
    calculateStats,
    validateNumericInput,
    addValidationListeners,
    initializeTooltips
};