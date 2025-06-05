import numpy as np
from typing import Dict, Any, Callable
from scipy import stats
from .base import BaseSimulation

class MarkovChain(BaseSimulation):
    """Markov Chain Monte Carlo (MCMC) simulation using Metropolis-Hastings algorithm"""
    
    def __init__(self, distribution_type: str = 'normal', 
                 burn_in: int = 1000,
                 step_size: float = 0.5,
                 initial_value: float = 0.0, **kwargs):
        # Adjust n_simulations to account for burn-in
        adjusted_n_simulations = kwargs.get('n_simulations', 10000) + burn_in
        kwargs['n_simulations'] = adjusted_n_simulations
        
        super().__init__(**kwargs)
        
        self.distribution_type = distribution_type
        self.burn_in = burn_in
        self.step_size = step_size
        self.initial_value = initial_value
        
        # Current state of the chain
        self.current_state = initial_value
        
        # Target distributions
        self.target_distributions = {
            'normal': lambda x: np.exp(-0.5 * x**2),  # Standard normal
            'gamma': lambda x: x * np.exp(-x) if x > 0 else 0,  # Gamma(2, 1)
            'beta': lambda x: x**(2) * (1-x)**(2) * 30 if 0 < x < 1 else 0,  # Beta(3, 3)
            'bimodal': lambda x: 0.5 * np.exp(-0.5 * (x-2)**2) + 0.5 * np.exp(-0.5 * (x+2)**2),
            'cauchy': lambda x: 1 / (np.pi * (1 + x**2)),
            'exponential': lambda x: np.exp(-x) if x > 0 else 0
        }
        
        if distribution_type not in self.target_distributions:
            raise ValueError(f"Unknown distribution type: {distribution_type}")
        
        self.target_density = self.target_distributions[distribution_type]
        
        # Results storage
        self.results = {
            'samples': [],
            'accepted': 0,
            'total_proposed': 0,
            'states': []  # For trace plot
        }
        
        # Theoretical statistics for comparison
        self.theoretical_stats = self._get_theoretical_stats()
    
    def _get_theoretical_stats(self) -> Dict[str, float]:
        """Get theoretical mean and variance for known distributions"""
        stats_dict = {
            'normal': {'mean': 0.0, 'variance': 1.0},
            'gamma': {'mean': 2.0, 'variance': 2.0},  # Gamma(2, 1)
            'beta': {'mean': 0.5, 'variance': 0.05},  # Beta(3, 3)
            'bimodal': {'mean': 0.0, 'variance': 5.0},  # Approximate
            'cauchy': {'mean': None, 'variance': None},  # Undefined
            'exponential': {'mean': 1.0, 'variance': 1.0}
        }
        return stats_dict.get(self.distribution_type, {'mean': None, 'variance': None})
    
    def _propose_new_state(self, current: float) -> float:
        """Propose a new state using random walk"""
        return current + np.random.normal(0, self.step_size)
    
    async def simulate_batch(self, batch_size: int) -> Dict[str, Any]:
        """Run MCMC sampling"""
        samples = []
        accepted_count = 0
        states = []
        
        for _ in range(batch_size):
            # Propose new state
            proposed = self._propose_new_state(self.current_state)
            
            # Calculate acceptance ratio (Metropolis-Hastings)
            current_density = self.target_density(self.current_state)
            proposed_density = self.target_density(proposed)
            
            if current_density > 0:
                acceptance_ratio = proposed_density / current_density
            else:
                acceptance_ratio = 1.0 if proposed_density > 0 else 0.0
            
            # Accept or reject
            if np.random.random() < acceptance_ratio:
                self.current_state = proposed
                accepted_count += 1
            
            # Store state for trace plot
            states.append(self.current_state)
            
            # Only store samples after burn-in period
            if self.current_iteration >= self.burn_in:
                samples.append(self.current_state)
        
        return {
            'samples': samples,
            'accepted': accepted_count,
            'total_proposed': batch_size,
            'states': states
        }
    
    def calculate_statistics(self) -> Dict[str, float]:
        """Calculate MCMC statistics"""
        # Only use samples after burn-in
        post_burnin_samples = self.results['samples']
        
        if not post_burnin_samples:
            return {
                'estimate': 0.0,  # Mean estimate
                'std_error': 0.0,
                'lower_ci': 0.0,
                'upper_ci': 0.0,
                'acceptance_rate': 0.0,
                'effective_sample_size': 0
            }
        
        samples = np.array(post_burnin_samples)
        
        # Basic statistics
        mean_estimate = np.mean(samples)
        variance_estimate = np.var(samples)
        
        # Calculate autocorrelation for effective sample size
        ess = self._calculate_ess(samples)
        
        # Standard error accounting for autocorrelation
        std_error = np.sqrt(variance_estimate / ess) if ess > 0 else np.inf
        
        # Confidence interval
        lower_ci, upper_ci = self.calculate_confidence_interval(mean_estimate, std_error)
        
        # Acceptance rate
        acceptance_rate = (self.results['accepted'] / self.results['total_proposed'] 
                          if self.results['total_proposed'] > 0 else 0)
        
        # Additional statistics
        percentiles = np.percentile(samples, [2.5, 25, 50, 75, 97.5])
        
        result = {
            'estimate': mean_estimate,
            'std_error': std_error,
            'lower_ci': lower_ci,
            'upper_ci': upper_ci,
            'variance': variance_estimate,
            'acceptance_rate': acceptance_rate,
            'effective_sample_size': ess,
            'actual_sample_size': len(samples),
            'percentiles': {
                '2.5%': percentiles[0],
                '25%': percentiles[1],
                '50%': percentiles[2],
                '75%': percentiles[3],
                '97.5%': percentiles[4]
            },
            'distribution_type': self.distribution_type,
            'parameters': {
                'burn_in': self.burn_in,
                'step_size': self.step_size,
                'initial_value': self.initial_value
            }
        }
        
        # Add theoretical values if available
        theoretical = self.theoretical_stats
        if theoretical['mean'] is not None:
            result['theoretical_mean'] = theoretical['mean']
            result['mean_error'] = abs(mean_estimate - theoretical['mean'])
        if theoretical['variance'] is not None:
            result['theoretical_variance'] = theoretical['variance']
            result['variance_error'] = abs(variance_estimate - theoretical['variance'])
        
        return result
    
    def _calculate_ess(self, samples: np.ndarray, max_lag: int = None) -> float:
        """Calculate effective sample size using autocorrelation"""
        n = len(samples)
        if n < 10:
            return n
        
        if max_lag is None:
            max_lag = min(int(n / 4), 1000)
        
        # Calculate autocorrelation function
        mean = np.mean(samples)
        var = np.var(samples)
        if var == 0:
            return 1
        
        acf = []
        for lag in range(max_lag):
            if lag == 0:
                acf.append(1.0)
            else:
                c_k = np.mean((samples[:-lag] - mean) * (samples[lag:] - mean)) / var
                acf.append(c_k)
                
                # Stop if autocorrelation becomes negligible
                if abs(c_k) < 0.05:
                    break
        
        # Calculate sum of autocorrelations
        sum_acf = 1 + 2 * sum(acf[1:])
        
        # Effective sample size
        ess = n / sum_acf if sum_acf > 0 else n
        return min(ess, n)
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """Get data for MCMC visualization"""
        samples = self.results['samples'][-5000:]  # Last 5000 samples
        states = self.results['states'][-1000:]   # Last 1000 states for trace
        
        if not samples:
            return {
                'type': 'markov_chain',
                'histogram': {'bins': [], 'counts': []},
                'trace_plot': [],
                'autocorrelation': [],
                'target_density': {'x': [], 'y': []}
            }
        
        # Create histogram
        hist, bins = np.histogram(samples, bins=50, density=True)
        histogram = {
            'bins': [(bins[i] + bins[i+1])/2 for i in range(len(hist))],
            'counts': hist.tolist()
        }
        
        # Create target density curve for comparison
        x_range = np.linspace(min(samples) - 1, max(samples) + 1, 200)
        y_target = [self.target_density(x) for x in x_range]
        
        # Normalize target density for visualization
        if max(y_target) > 0:
            normalization = np.trapz(y_target, x_range)
            if normalization > 0:
                y_target = [y / normalization for y in y_target]
        
        # Calculate autocorrelation for visualization
        acf_data = []
        if len(samples) > 20:
            sample_array = np.array(samples)
            mean = np.mean(sample_array)
            var = np.var(sample_array)
            
            for lag in range(min(50, len(samples) // 2)):
                if var > 0:
                    if lag == 0:
                        acf = 1.0
                    else:
                        acf = np.mean((sample_array[:-lag] - mean) * 
                                    (sample_array[lag:] - mean)) / var
                    acf_data.append({'lag': lag, 'acf': acf})
        
        return {
            'type': 'markov_chain',
            'histogram': histogram,
            'trace_plot': states,
            'autocorrelation': acf_data,
            'target_density': {
                'x': x_range.tolist(),
                'y': y_target
            },
            'acceptance_rate': (self.results['accepted'] / self.results['total_proposed'] 
                              if self.results['total_proposed'] > 0 else 0),
            'current_state': self.current_state
        }