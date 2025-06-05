// Main application controller
class MonteCarloApp {
    constructor() {
        this.api = new SimulationAPI();
        this.charts = new ChartManager();
        this.simulations = new SimulationController(this.api, this.charts);
        this.currentSimulation = null;
        this.isRunning = false;
        
        this.init();
    }

    async init() {
        try {
            // Connect to WebSocket
            await this.api.connect();
            this.api.showSuccess('Connected to server');
            
            // Set up event handlers
            this.setupEventHandlers();
            
            // Set up WebSocket message handlers
            this.setupMessageHandlers();
            
            // Initialize UI
            this.simulations.updateControls('pi');
            
        } catch (error) {
            console.error('Failed to initialize app:', error);
            this.api.showError('Failed to connect to server. Please refresh the page.');
        }
    }

    setupEventHandlers() {
        // Simulation type change
        document.getElementById('simulationType').addEventListener('change', (e) => {
            this.simulations.updateControls(e.target.value);
        });
        
        // Run simulation button
        document.getElementById('runSimulation').addEventListener('click', () => {
            this.startSimulation();
        });
        
        // Stop simulation button
        document.getElementById('stopSimulation').addEventListener('click', () => {
            this.stopSimulation();
        });
        
        // Export results button
        document.getElementById('exportResults').addEventListener('click', () => {
            this.exportResults();
        });
        
        // Chart zoom reset buttons
        document.getElementById('resetZoomPrimary').addEventListener('click', () => {
            this.charts.resetZoom('primary');
        });
        
        document.getElementById('resetZoomConvergence').addEventListener('click', () => {
            this.charts.resetZoom('convergence');
        });
    }

    setupMessageHandlers() {
        // Connection status
        this.api.on('connection', (message) => {
            console.log('Connection status:', message);
        });
        
        // Simulation started
        this.api.on('simulation_started', (message) => {
            this.isRunning = true;
            this.currentSimulation = message;
            this.updateUIState(true);
            this.charts.clear();
            this.api.showSuccess('Simulation started');
        });
        
        // Simulation update
        this.api.on('simulation_update', (message) => {
            this.handleSimulationUpdate(message.data);
        });
        
        // Simulation complete
        this.api.on('simulation_complete', (message) => {
            this.isRunning = false;
            this.updateUIState(false);
            this.handleFinalResults(message.final_results);
            this.api.showSuccess('Simulation completed');
        });
        
        // Simulation stopped
        this.api.on('simulation_stopped', (message) => {
            this.isRunning = false;
            this.updateUIState(false);
            this.api.showWarning('Simulation stopped');
        });
        
        // Error messages
        this.api.on('error', (message) => {
            this.api.showError(message.error);
            this.isRunning = false;
            this.updateUIState(false);
        });
    }

    startSimulation() {
        if (this.isRunning) return;
        
        const simulationType = document.getElementById('simulationType').value;
        const params = this.simulations.getParameters(simulationType);
        
        // Validate parameters
        if (!this.validateParameters(params)) {
            return;
        }
        
        // Start simulation
        try {
            this.api.startSimulation(simulationType, params);
        } catch (error) {
            this.api.showError('Failed to start simulation: ' + error.message);
        }
    }

    stopSimulation() {
        if (!this.isRunning) return;
        
        try {
            this.api.stopSimulation();
        } catch (error) {
            this.api.showError('Failed to stop simulation: ' + error.message);
        }
    }

    handleSimulationUpdate(data) {
        const { iteration, progress, statistics, visualization, convergence_history } = data;
        
        // Update progress
        this.updateProgress(progress);
        
        // Update statistics
        this.updateStatistics(statistics);
        
        // Update charts
        this.charts.updateVisualization(
            document.getElementById('simulationType').value,
            visualization
        );
        
        if (convergence_history && convergence_history.length > 0) {
            this.charts.updateConvergence(convergence_history);
        }
        
        // Update simulation count
        document.getElementById('simulationsRun').textContent = iteration.toLocaleString();
    }

    handleFinalResults(results) {
        // Show results section
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.style.display = 'block';
        
        // Format and display results
        const resultsHTML = this.formatResults(results);
        document.getElementById('detailedResults').innerHTML = resultsHTML;
        
        // Enable export button
        document.getElementById('exportResults').disabled = false;
        
        // Store results for export
        this.currentResults = results;
    }

    updateProgress(progress) {
        const percentage = Math.round(progress * 100);
        document.getElementById('progressFill').style.width = `${percentage}%`;
        document.getElementById('progressText').textContent = `${percentage}%`;
    }

    updateStatistics(stats) {
        // Update estimate
        const estimate = stats.estimate || 0;
        document.getElementById('currentEstimate').textContent = 
            typeof estimate === 'number' ? estimate.toFixed(6) : '-';
        
        // Update standard error
        const stdError = stats.std_error || 0;
        document.getElementById('standardError').textContent = 
            typeof stdError === 'number' ? stdError.toFixed(8) : '-';
        
        // Update confidence interval
        if (stats.lower_ci !== undefined && stats.upper_ci !== undefined) {
            document.getElementById('confidence95').textContent = 
                `[${stats.lower_ci.toFixed(6)}, ${stats.upper_ci.toFixed(6)}]`;
        } else {
            document.getElementById('confidence95').textContent = '-';
        }
    }

    updateUIState(isRunning) {
        document.getElementById('runSimulation').disabled = isRunning;
        document.getElementById('stopSimulation').disabled = !isRunning;
        document.getElementById('simulationType').disabled = isRunning;
        
        // Disable parameter inputs when running
        const inputs = document.querySelectorAll('#specificControls input, #specificControls select');
        inputs.forEach(input => input.disabled = isRunning);
        
        // Add loading class to buttons
        if (isRunning) {
            document.getElementById('runSimulation').classList.add('loading');
        } else {
            document.getElementById('runSimulation').classList.remove('loading');
        }
    }

    validateParameters(params) {
        // Basic validation
        if (params.n_simulations < 1000) {
            this.api.showError('Number of simulations must be at least 1000');
            return false;
        }
        
        if (params.n_simulations > 10000000) {
            this.api.showError('Number of simulations cannot exceed 10,000,000');
            return false;
        }
        
        // Add more validation as needed
        return true;
    }

    formatResults(results) {
        const stats = results.statistics;
        const simulationType = document.getElementById('simulationType').value;
        
        let html = '<div class="results-grid">';
        
        // General statistics
        html += '<div class="result-item">';
        html += '<h4>General Statistics</h4>';
        html += `<p>Total Iterations: ${results.total_iterations.toLocaleString()}</p>`;
        html += `<p>Final Estimate: ${stats.estimate.toFixed(8)}</p>`;
        html += `<p>Standard Error: ${stats.std_error.toFixed(10)}</p>`;
        html += `<p>95% Confidence Interval: [${stats.lower_ci.toFixed(8)}, ${stats.upper_ci.toFixed(8)}]</p>`;
        html += '</div>';
        
        // Simulation-specific results
        html += '<div class="result-item">';
        html += '<h4>Simulation-Specific Results</h4>';
        
        switch (simulationType) {
            case 'pi':
                if (stats.true_value) {
                    html += `<p>True Value of π: ${stats.true_value.toFixed(10)}</p>`;
                    html += `<p>Absolute Error: ${stats.error.toFixed(10)}</p>`;
                    html += `<p>Relative Error: ${stats.relative_error.toFixed(6)}%</p>`;
                }
                break;
            case 'option-pricing':
                if (stats.analytical_price) {
                    html += `<p>Analytical Price: ${stats.analytical_price.toFixed(4)}</p>`;
                    html += `<p>Price Error: ${stats.error.toFixed(4)}</p>`;
                    html += `<p>Relative Error: ${stats.relative_error.toFixed(4)}%</p>`;
                }
                if (stats.parameters) {
                    html += '<p>Parameters:</p>';
                    html += '<ul>';
                    for (const [key, value] of Object.entries(stats.parameters)) {
                        html += `<li>${key}: ${value}</li>`;
                    }
                    html += '</ul>';
                }
                break;
        }
        
        html += '</div>';
        html += '</div>';
        
        return html;
    }

    async exportResults() {
        if (!this.currentResults) {
            this.api.showError('No results to export');
            return;
        }
        
        try {
            // Create a blob with the results
            const dataStr = JSON.stringify(this.currentResults, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            
            // Create download link
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `monte-carlo-results-${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.api.showSuccess('Results exported successfully');
        } catch (error) {
            this.api.showError('Failed to export results: ' + error.message);
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new MonteCarloApp();
});