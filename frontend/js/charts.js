// Chart management for Monte Carlo Dashboard
class ChartManager {
    constructor() {
        this.primaryChart = null;
        this.convergenceChart = null;
        this.chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: {
                mode: 'nearest',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#e0e0e0',
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#00f5ff',
                    bodyColor: '#e0e0e0',
                    borderColor: '#00f5ff',
                    borderWidth: 1
                }
            }
        };
        
        this.initCharts();
    }

    initCharts() {
        // Initialize primary visualization chart
        const primaryCtx = document.getElementById('primaryChart').getContext('2d');
        this.primaryChart = new Chart(primaryCtx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Simulation Data',
                    data: [],
                    backgroundColor: 'rgba(0, 245, 255, 0.6)',
                    borderColor: 'rgba(0, 245, 255, 1)',
                    pointRadius: 2,
                    pointHoverRadius: 4
                }]
            },
            options: {
                ...this.chartOptions,
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#e0e0e0'
                        }
                    },
                    y: {
                        type: 'linear',
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#e0e0e0'
                        }
                    }
                }
            }
        });

        // Initialize convergence chart
        const convergenceCtx = document.getElementById('convergenceChart').getContext('2d');
        this.convergenceChart = new Chart(convergenceCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Estimate',
                    data: [],
                    borderColor: 'rgba(255, 0, 255, 1)',
                    backgroundColor: 'rgba(255, 0, 255, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.2
                }, {
                    label: 'Upper CI',
                    data: [],
                    borderColor: 'rgba(0, 245, 255, 0.5)',
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false
                }, {
                    label: 'Lower CI',
                    data: [],
                    borderColor: 'rgba(0, 245, 255, 0.5)',
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false
                }]
            },
            options: {
                ...this.chartOptions,
                scales: {
                    x: {
                        type: 'linear',
                        title: {
                            display: true,
                            text: 'Iterations',
                            color: '#e0e0e0'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#e0e0e0'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Estimate',
                            color: '#e0e0e0'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#e0e0e0'
                        }
                    }
                }
            }
        });
    }

    updateVisualization(simulationType, data) {
        switch (data.type) {
            case 'scatter':
                this.updateScatterPlot(data);
                break;
            case 'function_integration':
                this.updateFunctionPlot(data);
                break;
            case 'paths':
                this.updatePathsPlot(data);
                break;
            case 'hypothesis_test':
                this.updateHypothesisPlot(data);
                break;
            case 'value_at_risk':
                this.updateVaRPlot(data);
                break;
            case 'markov_chain':
                this.updateMarkovPlot(data);
                break;
            default:
                console.warn('Unknown visualization type:', data.type);
        }
    }

    updateScatterPlot(data) {
        // For Pi estimation
        this.primaryChart.data.datasets[0].data = data.points.map(p => ({x: p[0], y: p[1]}));
        
        // Add unit circle
        if (!this.primaryChart.data.datasets[1]) {
            const circlePoints = [];
            for (let i = 0; i <= 100; i++) {
                const angle = (i / 100) * 2 * Math.PI;
                circlePoints.push({
                    x: Math.cos(angle),
                    y: Math.sin(angle)
                });
            }
            
            this.primaryChart.data.datasets.push({
                label: 'Unit Circle',
                data: circlePoints,
                borderColor: 'rgba(255, 255, 255, 0.3)',
                backgroundColor: 'transparent',
                pointRadius: 0,
                borderWidth: 2,
                showLine: true
            });
        }
        
        this.primaryChart.update('none');
    }

    updateFunctionPlot(data) {
        // Clear existing datasets
        this.primaryChart.data.datasets = [];
        
        // Add function curve
        if (data.function_curve) {
            const curveData = data.function_curve.x.map((x, i) => ({
                x: x,
                y: data.function_curve.y[i]
            }));
            
            this.primaryChart.data.datasets.push({
                label: 'Function',
                data: curveData,
                borderColor: 'rgba(255, 0, 255, 1)',
                backgroundColor: 'rgba(255, 0, 255, 0.1)',
                borderWidth: 2,
                pointRadius: 0,
                fill: data.shaded_area,
                showLine: true
            });
        }
        
        // Add sample points
        if (data.sample_points && data.sample_points.length > 0) {
            this.primaryChart.data.datasets.push({
                label: 'Sample Points',
                data: data.sample_points.map(p => ({x: p[0], y: p[1]})),
                backgroundColor: 'rgba(0, 245, 255, 0.4)',
                borderColor: 'rgba(0, 245, 255, 0.8)',
                pointRadius: 3,
                showLine: false
            });
        }
        
        this.primaryChart.update('none');
    }

    updatePathsPlot(data) {
        // For option pricing - show stock price paths
        this.primaryChart.data.datasets = [];
        
        if (data.paths && data.paths.length > 0) {
            // Add sample paths
            data.paths.slice(0, 20).forEach((path, index) => {
                this.primaryChart.data.datasets.push({
                    label: index === 0 ? 'Price Paths' : null,
                    data: path.times.map((t, i) => ({
                        x: t,
                        y: path.prices[i]
                    })),
                    borderColor: `hsla(${180 + index * 10}, 70%, 50%, 0.3)`,
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    pointRadius: 0,
                    showLine: true
                });
            });
            
            // Add strike price line
            const maxTime = data.paths[0].times[data.paths[0].times.length - 1];
            this.primaryChart.data.datasets.push({
                label: 'Strike Price',
                data: [{x: 0, y: data.strike_price}, {x: maxTime, y: data.strike_price}],
                borderColor: 'rgba(255, 100, 100, 0.8)',
                borderDash: [10, 5],
                borderWidth: 2,
                pointRadius: 0,
                showLine: true
            });
        }
        
        this.primaryChart.update('none');
    }

    updateHypothesisPlot(data) {
        // Show sampling distributions
        this.primaryChart.data.datasets = [];
        
        if (data.sampling_distributions) {
            const dist = data.sampling_distributions;
            
            // Null distribution
            this.primaryChart.data.datasets.push({
                label: 'Null Distribution',
                data: dist.x.map((x, i) => ({x: x, y: dist.null[i]})),
                borderColor: 'rgba(100, 100, 255, 0.8)',
                backgroundColor: 'rgba(100, 100, 255, 0.1)',
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                showLine: true
            });
            
            // Alternative distribution
            this.primaryChart.data.datasets.push({
                label: 'Alternative Distribution',
                data: dist.x.map((x, i) => ({x: x, y: dist.alternative[i]})),
                borderColor: 'rgba(255, 100, 100, 0.8)',
                backgroundColor: 'rgba(255, 100, 100, 0.1)',
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                showLine: true
            });
            
            // Add critical value line
            if (data.critical_value) {
                this.primaryChart.data.datasets.push({
                    label: 'Critical Value',
                    data: [{x: data.critical_value, y: 0}, {x: data.critical_value, y: 0.5}],
                    borderColor: 'rgba(255, 255, 0, 0.8)',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    pointRadius: 0,
                    showLine: true
                });
            }
        }
        
        this.primaryChart.update('none');
    }

    updateVaRPlot(data) {
        // Show loss distribution
        this.primaryChart.data.datasets = [];
        
        if (data.losses_histogram && data.losses_histogram.bins.length > 0) {
            // Convert histogram to bar chart data
            this.primaryChart.data.datasets.push({
                label: 'Loss Distribution',
                data: data.losses_histogram.bins.map((bin, i) => ({
                    x: bin,
                    y: data.losses_histogram.counts[i]
                })),
                type: 'bar',
                backgroundColor: 'rgba(255, 100, 100, 0.6)',
                borderColor: 'rgba(255, 100, 100, 1)',
                borderWidth: 1
            });
            
            // Add VaR line
            if (data.var_line) {
                const maxCount = Math.max(...data.losses_histogram.counts);
                this.primaryChart.data.datasets.push({
                    label: `VaR (${(data.confidence_level * 100).toFixed(0)}%)`,
                    data: [{x: data.var_line, y: 0}, {x: data.var_line, y: maxCount}],
                    type: 'line',
                    borderColor: 'rgba(255, 255, 0, 0.8)',
                    borderDash: [10, 5],
                    borderWidth: 2,
                    pointRadius: 0,
                    showLine: true
                });
            }
            
            // Add ES line
            if (data.es_line) {
                const maxCount = Math.max(...data.losses_histogram.counts);
                this.primaryChart.data.datasets.push({
                    label: 'Expected Shortfall',
                    data: [{x: data.es_line, y: 0}, {x: data.es_line, y: maxCount}],
                    type: 'line',
                    borderColor: 'rgba(255, 0, 255, 0.8)',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    pointRadius: 0,
                    showLine: true
                });
            }
        }
        
        this.primaryChart.update('none');
    }

    updateMarkovPlot(data) {
        // Show histogram with target density overlay
        this.primaryChart.data.datasets = [];
        
        if (data.histogram && data.histogram.bins.length > 0) {
            // Histogram of samples
            this.primaryChart.data.datasets.push({
                label: 'MCMC Samples',
                data: data.histogram.bins.map((bin, i) => ({
                    x: bin,
                    y: data.histogram.counts[i]
                })),
                type: 'bar',
                backgroundColor: 'rgba(0, 245, 255, 0.4)',
                borderColor: 'rgba(0, 245, 255, 0.8)',
                borderWidth: 1
            });
            
            // Target density
            if (data.target_density && data.target_density.x.length > 0) {
                this.primaryChart.data.datasets.push({
                    label: 'Target Density',
                    data: data.target_density.x.map((x, i) => ({
                        x: x,
                        y: data.target_density.y[i]
                    })),
                    type: 'line',
                    borderColor: 'rgba(255, 0, 255, 1)',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    pointRadius: 0,
                    showLine: true
                });
            }
        }
        
        this.primaryChart.update('none');
    }

    updateConvergence(convergenceHistory) {
        if (!convergenceHistory || convergenceHistory.length === 0) return;
        
        // Update labels and data
        this.convergenceChart.data.labels = convergenceHistory.map(h => h.iteration);
        
        // Estimate line
        this.convergenceChart.data.datasets[0].data = convergenceHistory.map(h => h.estimate);
        
        // Confidence intervals
        this.convergenceChart.data.datasets[1].data = convergenceHistory.map(h => 
            h.estimate + 1.96 * h.std_error
        );
        this.convergenceChart.data.datasets[2].data = convergenceHistory.map(h => 
            h.estimate - 1.96 * h.std_error
        );
        
        this.convergenceChart.update('none');
    }

    clear() {
        // Clear primary chart
        this.primaryChart.data.datasets.forEach(dataset => {
            dataset.data = [];
        });
        this.primaryChart.update('none');
        
        // Clear convergence chart
        this.convergenceChart.data.labels = [];
        this.convergenceChart.data.datasets.forEach(dataset => {
            dataset.data = [];
        });
        this.convergenceChart.update('none');
    }

    resetZoom(chartType) {
        if (chartType === 'primary') {
            this.primaryChart.resetZoom();
        } else if (chartType === 'convergence') {
            this.convergenceChart.resetZoom();
        }
    }
}

// Export as global
window.ChartManager = ChartManager;