import numpy as np
from typing import Dict, Any
from .base import BaseSimulation

class OptionPricing(BaseSimulation):
    """Monte Carlo simulation for option pricing using Black-Scholes model"""
    
    def __init__(self, stock_price: float = 100, strike_price: float = 110,
                 volatility: float = 0.2, risk_free_rate: float = 0.05,
                 time_to_maturity: float = 1.0, option_type: str = 'call', **kwargs):
        super().__init__(**kwargs)
        
        # Option parameters
        self.S0 = stock_price
        self.K = strike_price
        self.sigma = volatility
        self.r = risk_free_rate
        self.T = time_to_maturity
        self.option_type = option_type.lower()
        
        # Pre-calculate constants
        self.discount_factor = np.exp(-self.r * self.T)
        self.drift = (self.r - 0.5 * self.sigma ** 2) * self.T
        self.diffusion = self.sigma * np.sqrt(self.T)
        
        # Results storage
        self.results = {
            'payoff_sum': 0.0,
            'payoff_sum_squared': 0.0,
            'count': 0,
            'sample_paths': []  # For visualization
        }
        
        # Calculate analytical Black-Scholes price for comparison
        self.analytical_price = self._black_scholes_price()
    
    def _black_scholes_price(self) -> float:
        """Calculate analytical Black-Scholes price for comparison"""
        from scipy.stats import norm
        
        d1 = (np.log(self.S0 / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * np.sqrt(self.T))
        d2 = d1 - self.sigma * np.sqrt(self.T)
        
        if self.option_type == 'call':
            price = self.S0 * norm.cdf(d1) - self.K * np.exp(-self.r * self.T) * norm.cdf(d2)
        else:  # put
            price = self.K * np.exp(-self.r * self.T) * norm.cdf(-d2) - self.S0 * norm.cdf(-d1)
        
        return price
    
    async def simulate_batch(self, batch_size: int) -> Dict[str, Any]:
        """Simulate option price paths"""
        # Generate random shocks
        Z = np.random.standard_normal(batch_size)
        
        # Calculate terminal stock prices
        ST = self.S0 * np.exp(self.drift + self.diffusion * Z)
        
        # Calculate payoffs
        if self.option_type == 'call':
            payoffs = np.maximum(ST - self.K, 0)
        else:  # put
            payoffs = np.maximum(self.K - ST, 0)
        
        # Discount payoffs
        discounted_payoffs = payoffs * self.discount_factor
        
        # Store sample paths for visualization (limit to 100 paths)
        sample_paths = []
        if len(self.results['sample_paths']) < 100:
            n_paths = min(10, batch_size, 100 - len(self.results['sample_paths']))
            if n_paths > 0:
                # Generate full paths for visualization
                time_steps = 50
                dt = self.T / time_steps
                times = np.linspace(0, self.T, time_steps + 1)
                
                for i in range(n_paths):
                    path = [self.S0]
                    S = self.S0
                    for t in range(time_steps):
                        dW = np.random.standard_normal() * np.sqrt(dt)
                        S = S * np.exp((self.r - 0.5 * self.sigma ** 2) * dt + self.sigma * dW)
                        path.append(S)
                    sample_paths.append({
                        'times': times.tolist(),
                        'prices': path,
                        'final_payoff': float(np.maximum(path[-1] - self.K, 0) if self.option_type == 'call' 
                                            else np.maximum(self.K - path[-1], 0))
                    })
        
        return {
            'payoff_sum': float(np.sum(discounted_payoffs)),
            'payoff_sum_squared': float(np.sum(discounted_payoffs ** 2)),
            'count': batch_size,
            'sample_paths': sample_paths
        }
    
    def calculate_statistics(self) -> Dict[str, float]:
        """Calculate option price estimate and statistics"""
        if self.results['count'] == 0:
            return {
                'estimate': 0.0,
                'std_error': 0.0,
                'lower_ci': 0.0,
                'upper_ci': 0.0,
                'analytical_price': self.analytical_price,
                'error': 0.0
            }
        
        # Monte Carlo estimate
        estimate = self.results['payoff_sum'] / self.results['count']
        
        # Standard error
        mean_squared = self.results['payoff_sum_squared'] / self.results['count']
        variance = mean_squared - estimate ** 2
        std_error = np.sqrt(variance / self.results['count'])
        
        # Confidence interval
        lower_ci, upper_ci = self.calculate_confidence_interval(estimate, std_error)
        
        return {
            'estimate': estimate,
            'std_error': std_error,
            'lower_ci': lower_ci,
            'upper_ci': upper_ci,
            'analytical_price': self.analytical_price,
            'error': abs(estimate - self.analytical_price),
            'relative_error': abs(estimate - self.analytical_price) / self.analytical_price * 100 if self.analytical_price > 0 else 0,
            'option_type': self.option_type,
            'parameters': {
                'S0': self.S0,
                'K': self.K,
                'sigma': self.sigma,
                'r': self.r,
                'T': self.T
            }
        }
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """Get path data for visualization"""
        paths = self.results['sample_paths']
        
        # Prepare data for different visualizations
        return {
            'type': 'paths',
            'paths': paths[:50],  # Limit to 50 paths for performance
            'strike_price': self.K,
            'initial_price': self.S0,
            'payoff_distribution': self._get_payoff_distribution()
        }
    
    def _get_payoff_distribution(self) -> Dict[str, Any]:
        """Get payoff distribution for histogram"""
        # This would be computed from stored results in a real implementation
        # For now, return empty data
        return {
            'bins': [],
            'frequencies': []
        }