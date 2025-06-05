// API Client for Monte Carlo Dashboard
class SimulationAPI {
    constructor() {
        this.baseURL = window.location.origin;
        this.ws = null;
        this.isConnected = false;
        this.messageHandlers = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    // WebSocket connection management
    async connect() {
        return new Promise((resolve, reject) => {
            try {
                const wsURL = `${this.baseURL.replace('http', 'ws')}/ws/simulate`;
                this.ws = new WebSocket(wsURL);

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(JSON.parse(event.data));
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    reject(error);
                };

                this.ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    this.isConnected = false;
                    this.attemptReconnect();
                };
            } catch (error) {
                reject(error);
            }
        });
    }

    handleMessage(message) {
        const { type, data } = message;
        
        // Call registered handlers
        if (this.messageHandlers.has(type)) {
            this.messageHandlers.get(type).forEach(handler => handler(message));
        }
        
        // Call global handler if exists
        if (this.messageHandlers.has('*')) {
            this.messageHandlers.get('*').forEach(handler => handler(message));
        }
    }

    on(messageType, handler) {
        if (!this.messageHandlers.has(messageType)) {
            this.messageHandlers.set(messageType, []);
        }
        this.messageHandlers.get(messageType).push(handler);
    }

    off(messageType, handler) {
        if (this.messageHandlers.has(messageType)) {
            const handlers = this.messageHandlers.get(messageType);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    async attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.showError('Connection lost. Please refresh the page.');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
        
        console.log(`Attempting to reconnect in ${delay}ms...`);
        setTimeout(async () => {
            try {
                await this.connect();
                this.showSuccess('Reconnected successfully');
            } catch (error) {
                console.error('Reconnection failed:', error);
            }
        }, delay);
    }

    // Send message to server
    send(message) {
        if (!this.isConnected || !this.ws) {
            throw new Error('WebSocket is not connected');
        }
        this.ws.send(JSON.stringify(message));
    }

    // Start simulation
    startSimulation(simulationType, params) {
        this.send({
            type: 'start_simulation',
            simulation_type: simulationType,
            params: params
        });
    }

    // Stop current simulation
    stopSimulation() {
        this.send({
            type: 'stop_simulation'
        });
    }

    // Get current status
    getStatus() {
        this.send({
            type: 'get_status'
        });
    }

    // REST API methods
    async getSimulationHistory() {
        const response = await fetch(`${this.baseURL}/api/v1/simulations/history`);
        if (!response.ok) {
            throw new Error('Failed to fetch simulation history');
        }
        return response.json();
    }

    async exportResults(simulationId, format = 'json') {
        const response = await fetch(`${this.baseURL}/api/v1/simulations/${simulationId}/export?format=${format}`);
        if (!response.ok) {
            throw new Error('Failed to export results');
        }
        
        if (format === 'json') {
            return response.json();
        } else {
            // For CSV or other formats, return blob
            return response.blob();
        }
    }

    // Utility methods
    showSuccess(message) {
        this.showStatus(message, 'success');
    }

    showError(message) {
        this.showStatus(message, 'error');
    }

    showWarning(message) {
        this.showStatus(message, 'warning');
    }

    showStatus(message, type = 'info') {
        const statusEl = document.getElementById('statusMessage');
        if (statusEl) {
            statusEl.textContent = message;
            statusEl.className = `status-message ${type} show`;
            
            setTimeout(() => {
                statusEl.classList.remove('show');
            }, 3000);
        }
    }

    // Disconnect
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
            this.isConnected = false;
        }
    }
}

// Export as global
window.SimulationAPI = SimulationAPI;