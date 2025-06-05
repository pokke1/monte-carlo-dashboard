import numpy as np
from typing import Dict, Any, List
from scipy import stats
from .base import BaseSimulation

class ValueAtRisk(BaseSimulation):
    """Monte Carlo simulation for Value at Risk (VaR) calculation"""
    
    def __init__(self, portfolio_value: float = 1000000, 
                 expected_return: float = 0.08,
                 portfolio_volatility: float = 0.15,
                 time_horizon: int = 10,
                 confidence_level: float = 0.95,
                 distribution: str = 'normal', **kwargs):
        super().__init__(**kwargs)
        
        # Portfolio parameters
        self.portfolio_value = portfolio_value
        self.expected_return = expected_return
        self.volatility = portfolio_volatility
        self.time_horizon = time_horizon  # in days
        self.confidence_level = confidence_level
        self.distribution = distribution
        
        # Convert annual parameters to daily
        self.daily_return = expected_return / 252  # Assuming 252 trading days
        self.daily_volatility = portfolio_volatility / np.sqrt(252)
        
        # Calculate time-adjusted parameters
        self.period_return = self.daily_return * time_horizon
        self.period_volatility = self.daily_volatility * np.sqrt(time_horizon)
        
        # Results storage
        self.results = {
            'returns': [],
            'portfolio_values': [],
            'losses': []
        }
        
        # Calculate analytical VaR for normal distribution
        self.analytical_var = self._calculate_analytical_var()
    
    def _calculate_analytical_var(self) -> float:
        """Calculate analytical VaR for normal distribution"""
        if self.distribution == 'normal':
            # VaR = -μ + σ * Φ^(-1)(α)
            z_score = stats.norm.ppf(1 - self.confidence_level)
            var_return = -self.period_return + self.period_volatility * (-z_score)
            return self.portfolio_value * var_return
        else:
            return None
    
    async def simulate_batch(self, batch_size: int) -> Dict[str, Any]:
        """Simulate portfolio returns"""
        portfolio_returns = []
        final_values = []
        losses = []
        
        for _ in range(batch_size):
            # Generate returns for each day in the time horizon
            if self.distribution == 'normal':
                # Geometric Brownian Motion
                daily_returns = np.random.normal(
                    self.daily_return, 
                    self.daily_volatility, 
                    self.time_horizon
                )
                # Compound returns
                cumulative_return = np.prod(1 + daily_returns) - 1
                
            elif self.distribution == 't':
                # Student's t-distribution (heavier tails)
                df = 5  # degrees of freedom
                daily_shocks = np.random.standard_t(df, self.time_horizon)
                # Scale to match volatility
                daily_shocks = daily_shocks / np.sqrt(df / (df - 2))
                daily_returns = self.daily_return + self.daily_volatility * daily_shocks
                cumulative_return = np.prod(1 + daily_returns) - 1
                
            elif self.distribution == 'historical':
                # In practice, this would use historical data
                # Here we simulate with a mixture model
                if np.random.random() < 0.95:
                    # Normal market conditions
                    daily_returns = np.random.normal(
                        self.daily_return, 
                        self.daily_volatility, 
                        self.time_horizon
                    )
                else:
                    # Market stress (higher volatility)
                    daily_returns = np.random.normal(
                        self.daily_return - 0.02,  # Lower return in stress
                        self.daily_volatility * 3,  # Triple volatility
                        self.time_horizon
                    )
                cumulative_return = np.prod(1 + daily_returns) - 1
            
            # Calculate final portfolio value and loss
            final_value = self.portfolio_value * (1 + cumulative_return)
            loss = self.portfolio_value - final_value
            
            portfolio_returns.append(cumulative_return)
            final_values.append(final_value)
            losses.append(loss)
        
        return {
            'returns': portfolio_returns,
            'portfolio_values': final_values,
            'losses': losses
        }
    
    def calculate_statistics(self) -> Dict[str, float]:
        """Calculate VaR and related risk metrics"""
        if len(self.results['returns']) == 0:
            return {
                'estimate': 0.0,  # VaR estimate
                'std_error': 0.0,
                'lower_ci': 0.0,
                'upper_ci': 0.0,
                'analytical_var': self.analytical_var,
                'expected_shortfall': 0.0
            }
        
        # Convert to numpy arrays for easier calculation
        returns = np.array(self.results['returns'])
        losses = np.array(self.results['losses'])
        
        # Calculate VaR (loss at the (1-α) percentile)
        var_percentile = (1 - self.confidence_level) * 100
        var_estimate = np.percentile(losses, 100 - var_percentile)
        
        # Calculate Expected Shortfall (CVaR) - average loss beyond VaR
        losses_beyond_var = losses[losses > var_estimate]
        expected_shortfall = np.mean(losses_beyond_var) if len(losses_beyond_var) > 0 else var_estimate
        
        # Bootstrap confidence interval for VaR
        n_bootstrap = 1000
        var_estimates = []
        n_samples = len(losses)
        
        for _ in range(n_bootstrap):
            bootstrap_indices = np.random.choice(n_samples, n_samples, replace=True)
            bootstrap_losses = losses[bootstrap_indices]
            bootstrap_var = np.percentile(bootstrap_losses, 100 - var_percentile)
            var_estimates.append(bootstrap_var)
        
        std_error = np.std(var_estimates)
        lower_ci = np.percentile(var_estimates, 2.5)
        upper_ci = np.percentile(var_estimates, 97.5)
        
        # Additional risk metrics
        mean_return = np.mean(returns)
        volatility = np.std(returns)
        sharpe_ratio = mean_return / volatility if volatility > 0 else 0
        max_loss = np.max(losses)
        
        result = {
            'estimate': var_estimate,
            'std_error': std_error,
            'lower_ci': lower_ci,
            'upper_ci': upper_ci,
            'expected_shortfall': expected_shortfall,
            'mean_return': mean_return * 100,  # As percentage
            'volatility': volatility * 100,  # As percentage
            'sharpe_ratio': sharpe_ratio,
            'max_loss': max_loss,
            'confidence_level': self.confidence_level,
            'time_horizon': self.time_horizon,
            'parameters': {
                'portfolio_value': self.portfolio_value,
                'expected_return': self.expected_return,
                'volatility': self.portfolio_volatility,
                'distribution': self.distribution
            }
        }
        
        if self.analytical_var is not None:
            result['analytical_var'] = self.analytical_var
            result['error'] = abs(var_estimate - self.analytical_var)
            result['relative_error'] = (abs(var_estimate - self.analytical_var) / 
                                       self.analytical_var * 100)
        
        return result
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """Get data for risk visualization"""
        returns = self.results['returns'][-5000:]  # Last 5000 returns
        losses = self.results['losses'][-5000:]
        
        if not returns:
            return {
                'type': 'value_at_risk',
                'returns_histogram': {'bins': [], 'counts': []},
                'losses_histogram': {'bins': [], 'counts': []},
                'var_line': 0,
                'es_line': 0
            }
        
        # Create histogram data for returns
        ret_hist, ret_bins = np.histogram(returns, bins=50)
        returns_histogram = {
            'bins': [(ret_bins[i] + ret_bins[i+1])/2 for i in range(len(ret_hist))],
            'counts': ret_hist.tolist()
        }
        
        # Create histogram data for losses
        loss_hist, loss_bins = np.histogram(losses, bins=50)
        losses_histogram = {
            'bins': [(loss_bins[i] + loss_bins[i+1])/2 for i in range(len(loss_hist))],
            'counts': loss_hist.tolist()
        }
        
        # Calculate current VaR and ES for visualization
        var_percentile = (1 - self.confidence_level) * 100
        current_var = np.percentile(losses, 100 - var_percentile)
        losses_beyond_var = [l for l in losses if l > current_var]
        current_es = np.mean(losses_beyond_var) if losses_beyond_var else current_var
        
        # Create return time series for line chart (sample if too many)
        if len(self.results['returns']) > 1000:
            step = len(self.results['returns']) // 1000
            sampled_returns = self.results['returns'][::step]
        else:
            sampled_returns = self.results['returns']
        
        return {
            'type': 'value_at_risk',
            'returns_histogram': returns_histogram,
            'losses_histogram': losses_histogram,
            'return_series': sampled_returns,
            'var_line': current_var,
            'es_line': current_es,
            'confidence_level': self.confidence_level,
            'portfolio_value': self.portfolio_value
        }