// Simulation controller for Monte Carlo Dashboard
class SimulationController {
    constructor(api, charts) {
        this.api = api;
        this.charts = charts;
        this.currentType = 'pi';
    }

    updateControls(simulationType) {
        this.currentType = simulationType;
        const container = document.getElementById('specificControls');
        
        // Clear existing controls
        container.innerHTML = '<h2>Simulation Parameters</h2>';
        
        // Add simulation-specific controls
        const controls = this.getControlsHTML(simulationType);
        container.innerHTML += controls;
        
        // Update formula display
        this.updateFormula(simulationType);
    }

    getControlsHTML(type) {
        const controlsMap = {
            'pi': '',  // No additional controls for Pi estimation
            
            'integration': `
                <div class="control-group">
                    <label for="functionType">Function to Integrate</label>
                    <select id="functionType" class="control-select">
                        <option value="gaussian">Gaussian: e^(-x²)</option>
                        <option value="sine">Sine: sin(x)</option>
                        <option value="polynomial">Polynomial: x³ - 2x² + x</option>
                        <option value="exponential">Exponential: e^(-|x|)</option>
                        <option value="reciprocal">Reciprocal: 1/(1 + x²)</option>
                    </select>
                </div>
                <div class="control-group">
                    <label for="lowerBound">Lower Bound</label>
                    <input type="number" id="lowerBound" value="-2" step="0.1">
                </div>
                <div class="control-group">
                    <label for="upperBound">Upper Bound</label>
                    <input type="number" id="upperBound" value="2" step="0.1">
                </div>
            `,
            
            'option-pricing': `
                <div class="control-group">
                    <label for="stockPrice">Stock Price (S₀)</label>
                    <input type="number" id="stockPrice" value="100" step="1">
                </div>
                <div class="control-group">
                    <label for="strikePrice">Strike Price (K)</label>
                    <input type="number" id="strikePrice" value="110" step="1">
                </div>
                <div class="control-group">
                    <label for="volatility">Volatility (σ)</label>
                    <input type="number" id="volatility" value="0.2" step="0.01" min="0.01" max="1">
                </div>
                <div class="control-group">
                    <label for="riskFreeRate">Risk-Free Rate (r)</label>
                    <input type="number" id="riskFreeRate" value="0.05" step="0.01" min="0" max="0.5">
                </div>
                <div class="control-group">
                    <label for="timeToMaturity">Time to Maturity (T)</label>
                    <input type="number" id="timeToMaturity" value="1" step="0.1" min="0.1" max="5">
                </div>
                <div class="control-group">
                    <label for="optionType">Option Type</label>
                    <select id="optionType" class="control-select">
                        <option value="call">Call Option</option>
                        <option value="put">Put Option</option>
                    </select>
                </div>
            `,
            
            'hypothesis': `
                <div class="control-group">
                    <label for="nullMean">Null Hypothesis Mean (μ₀)</label>
                    <input type="number" id="nullMean" value="0" step="0.1">
                </div>
                <div class="control-group">
                    <label for="altMean">Alternative Mean (μ₁)</label>
                    <input type="number" id="altMean" value="0.5" step="0.1">
                </div>
                <div class="control-group">
                    <label for="stdDev">Standard Deviation (σ)</label>
                    <input type="number" id="stdDev" value="1" step="0.1" min="0.1">
                </div>
                <div class="control-group">
                    <label for="sampleSize">Sample Size (n)</label>
                    <input type="number" id="sampleSize" value="30" step="1" min="2" max="1000">
                </div>
                <div class="control-group">
                    <label for="alpha">Significance Level (α)</label>
                    <input type="number" id="alpha" value="0.05" step="0.01" min="0.01" max="0.5">
                </div>
                <div class="control-group">
                    <label for="testType">Test Type</label>
                    <select id="testType" class="control-select">
                        <option value="two-sided">Two-sided</option>
                        <option value="right-tailed">Right-tailed</option>
                        <option value="left-tailed">Left-tailed</option>
                    </select>
                </div>
            `,
            
            'risk': `
                <div class="control-group">
                    <label for="portfolioValue">Portfolio Value ($)</label>
                    <input type="number" id="portfolioValue" value="1000000" step="10000" min="1000">
                </div>
                <div class="control-group">
                    <label for="expectedReturn">Expected Annual Return</label>
                    <input type="number" id="expectedReturn" value="0.08" step="0.01" min="-0.5" max="0.5">
                </div>
                <div class="control-group">
                    <label for="portfolioVolatility">Portfolio Volatility</label>
                    <input type="number" id="portfolioVolatility" value="0.15" step="0.01" min="0.01" max="1">
                </div>
                <div class="control-group">
                    <label for="timeHorizon">Time Horizon (days)</label>
                    <input type="number" id="timeHorizon" value="10" step="1" min="1" max="252">
                </div>
                <div class="control-group">
                    <label for="confidenceLevel">Confidence Level</label>
                    <input type="number" id="confidenceLevel" value="0.95" step="0.01" min="0.9" max="0.99">
                </div>
                <div class="control-group">
                    <label for="distribution">Distribution Type</label>
                    <select id="distribution" class="control-select">
                        <option value="normal">Normal</option>
                        <option value="t">Student's t</option>
                        <option value="historical">Historical Simulation</option>
                    </select>
                </div>
            `,
            
            'markov': `
                <div class="control-group">
                    <label for="distributionType">Target Distribution</label>
                    <select id="distributionType" class="control-select">
                        <option value="normal">Standard Normal</option>
                        <option value="gamma">Gamma(2,1)</option>
                        <option value="beta">Beta(3,3)</option>
                        <option value="bimodal">Bimodal Mixture</option>
                        <option value="cauchy">Cauchy</option>
                        <option value="exponential">Exponential</option>
                    </select>
                </div>
                <div class="control-group">
                    <label for="burnIn">Burn-in Period</label>
                    <input type="number" id="burnIn" value="1000" step="100" min="0" max="10000">
                </div>
                <div class="control-group">
                    <label for="stepSize">Step Size</label>
                    <input type="number" id="stepSize" value="0.5" step="0.1" min="0.01" max="5">
                </div>
                <div class="control-group">
                    <label for="initialValue">Initial Value</label>
                    <input type="number" id="initialValue" value="0" step="0.1">
                </div>
            `
        };
        
        return controlsMap[type] || '';
    }

    updateFormula(type) {
        const formulas = {
            'pi': 'π ≈ 4 × (points inside circle) / (total points)',
            'integration': '∫ f(x)dx ≈ (b-a) × (1/n) × Σf(xᵢ)',
            'option-pricing': 'C = e^(-rT) × E[max(Sₜ - K, 0)]',
            'hypothesis': 'Power = P(reject H₀ | H₁ is true)',
            'risk': 'VaR_α = inf{x: P(L > x) ≤ 1 - α}',
            'markov': 'π(x′|x) = min(1, π(x′)/π(x)) [Metropolis-Hastings]'
        };
        
        const formulaDisplay = document.getElementById('formulaDisplay');
        formulaDisplay.textContent = formulas[type] || '';
    }

    getParameters(simulationType) {
        // Get common parameters
        const params = {
            n_simulations: parseInt(document.getElementById('numSimulations').value),
            batch_size: parseInt(document.getElementById('batchSize').value),
            update_frequency: parseInt(document.getElementById('updateFrequency').value)
        };
        
        // Add random seed if provided
        const seedInput = document.getElementById('randomSeed').value;
        if (seedInput) {
            params.seed = parseInt(seedInput);
        }
        
        // Add simulation-specific parameters
        switch (simulationType) {
            case 'integration':
                params.function_type = document.getElementById('functionType').value;
                params.lower_bound = parseFloat(document.getElementById('lowerBound').value);
                params.upper_bound = parseFloat(document.getElementById('upperBound').value);
                break;
                
            case 'option-pricing':
                params.stock_price = parseFloat(document.getElementById('stockPrice').value);
                params.strike_price = parseFloat(document.getElementById('strikePrice').value);
                params.volatility = parseFloat(document.getElementById('volatility').value);
                params.risk_free_rate = parseFloat(document.getElementById('riskFreeRate').value);
                params.time_to_maturity = parseFloat(document.getElementById('timeToMaturity').value);
                params.option_type = document.getElementById('optionType').value;
                break;
                
            case 'hypothesis':
                params.null_mean = parseFloat(document.getElementById('nullMean').value);
                params.alt_mean = parseFloat(document.getElementById('altMean').value);
                params.std_dev = parseFloat(document.getElementById('stdDev').value);
                params.sample_size = parseInt(document.getElementById('sampleSize').value);
                params.alpha = parseFloat(document.getElementById('alpha').value);
                params.test_type = document.getElementById('testType').value;
                break;
                
            case 'risk':
                params.portfolio_value = parseFloat(document.getElementById('portfolioValue').value);
                params.expected_return = parseFloat(document.getElementById('expectedReturn').value);
                params.portfolio_volatility = parseFloat(document.getElementById('portfolioVolatility').value);
                params.time_horizon = parseInt(document.getElementById('timeHorizon').value);
                params.confidence_level = parseFloat(document.getElementById('confidenceLevel').value);
                params.distribution = document.getElementById('distribution').value;
                break;
                
            case 'markov':
                params.distribution_type = document.getElementById('distributionType').value;
                params.burn_in = parseInt(document.getElementById('burnIn').value);
                params.step_size = parseFloat(document.getElementById('stepSize').value);
                params.initial_value = parseFloat(document.getElementById('initialValue').value);
                break;
        }
        
        return params;
    }
}

// Export as global
window.SimulationController = SimulationController;