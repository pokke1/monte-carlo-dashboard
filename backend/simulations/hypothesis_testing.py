import numpy as np
from typing import Dict, Any
from scipy import stats
from .base import BaseSimulation

class HypothesisTesting(BaseSimulation):
    """Monte Carlo simulation for hypothesis testing and power analysis"""
    
    def __init__(self, null_mean: float = 0.0, alt_mean: float = 0.5,
                 std_dev: float = 1.0, sample_size: int = 30,
                 alpha: float = 0.05, test_type: str = 'two-sided', **kwargs):
        super().__init__(**kwargs)
        
        # Test parameters
        self.null_mean = null_mean
        self.alt_mean = alt_mean
        self.std_dev = std_dev
        self.sample_size = sample_size
        self.alpha = alpha
        self.test_type = test_type
        
        # Calculate critical values based on test type
        if test_type == 'two-sided':
            self.critical_z = stats.norm.ppf(1 - alpha/2)
        elif test_type == 'right-tailed':
            self.critical_z = stats.norm.ppf(1 - alpha)
        elif test_type == 'left-tailed':
            self.critical_z = -stats.norm.ppf(1 - alpha)
        else:
            raise ValueError(f"Unknown test type: {test_type}")
        
        # Standard error for sample mean
        self.se = std_dev / np.sqrt(sample_size)
        
        # Results storage
        self.results = {
            'reject_count': 0,
            'total_tests': 0,
            'p_values': [],
            'test_statistics': [],
            'decisions': []  # For visualization
        }
        
        # Calculate theoretical power
        self.theoretical_power = self._calculate_theoretical_power()
    
    def _calculate_theoretical_power(self) -> float:
        """Calculate theoretical power using normal distribution"""
        effect_size = (self.alt_mean - self.null_mean) / self.se
        
        if self.test_type == 'two-sided':
            # Power = P(|Z| > z_critical | H1 is true)
            power = (1 - stats.norm.cdf(self.critical_z - effect_size) + 
                    stats.norm.cdf(-self.critical_z - effect_size))
        elif self.test_type == 'right-tailed':
            # Power = P(Z > z_critical | H1 is true)
            power = 1 - stats.norm.cdf(self.critical_z - effect_size)
        else:  # left-tailed
            # Power = P(Z < z_critical | H1 is true)
            power = stats.norm.cdf(self.critical_z - effect_size)
        
        return power
    
    async def simulate_batch(self, batch_size: int) -> Dict[str, Any]:
        """Run hypothesis tests"""
        reject_count = 0
        p_values = []
        test_statistics = []
        decisions = []
        
        for _ in range(batch_size):
            # Generate sample from alternative distribution
            sample = np.random.normal(self.alt_mean, self.std_dev, self.sample_size)
            sample_mean = np.mean(sample)
            
            # Calculate test statistic (z-score)
            z_score = (sample_mean - self.null_mean) / self.se
            
            # Calculate p-value
            if self.test_type == 'two-sided':
                p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
                reject = abs(z_score) > self.critical_z
            elif self.test_type == 'right-tailed':
                p_value = 1 - stats.norm.cdf(z_score)
                reject = z_score > self.critical_z
            else:  # left-tailed
                p_value = stats.norm.cdf(z_score)
                reject = z_score < self.critical_z
            
            if reject:
                reject_count += 1
            
            # Store for visualization (limit total stored)
            if len(self.results['p_values']) < 5000:
                p_values.append(float(p_value))
                test_statistics.append(float(z_score))
                decisions.append(reject)
        
        return {
            'reject_count': reject_count,
            'total_tests': batch_size,
            'p_values': p_values,
            'test_statistics': test_statistics,
            'decisions': decisions
        }
    
    def calculate_statistics(self) -> Dict[str, float]:
        """Calculate power and related statistics"""
        if self.results['total_tests'] == 0:
            return {
                'estimate': 0.0,  # Estimated power
                'std_error': 0.0,
                'lower_ci': 0.0,
                'upper_ci': 0.0,
                'theoretical_power': self.theoretical_power,
                'type_i_error_rate': self.alpha
            }
        
        # Estimated power (proportion of rejections)
        power_estimate = self.results['reject_count'] / self.results['total_tests']
        
        # Standard error for proportion
        std_error = np.sqrt(power_estimate * (1 - power_estimate) / 
                           self.results['total_tests'])
        
        # Confidence interval
        lower_ci, upper_ci = self.calculate_confidence_interval(power_estimate, std_error)
        
        # Calculate actual Type I error rate if we have p-values
        type_i_estimate = None
        if self.results['p_values']:
            # This would be more accurate with samples from null distribution
            # Here we're approximating based on rejection rate
            type_i_estimate = self.alpha  # Theoretical value
        
        return {
            'estimate': power_estimate,
            'std_error': std_error,
            'lower_ci': lower_ci,
            'upper_ci': upper_ci,
            'theoretical_power': self.theoretical_power,
            'error': abs(power_estimate - self.theoretical_power),
            'relative_error': (abs(power_estimate - self.theoretical_power) / 
                             self.theoretical_power * 100 
                             if self.theoretical_power > 0 else 0),
            'type_i_error_rate': self.alpha,
            'effect_size': (self.alt_mean - self.null_mean) / self.std_dev,
            'parameters': {
                'null_mean': self.null_mean,
                'alt_mean': self.alt_mean,
                'std_dev': self.std_dev,
                'sample_size': self.sample_size,
                'alpha': self.alpha,
                'test_type': self.test_type
            }
        }
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """Get data for visualization"""
        # Prepare p-value distribution
        p_values = self.results['p_values'][-1000:]  # Last 1000 p-values
        test_stats = self.results['test_statistics'][-1000:]
        
        # Create histogram data for p-values
        if p_values:
            hist, bin_edges = np.histogram(p_values, bins=20, range=(0, 1))
            p_value_hist = {
                'bins': [(bin_edges[i] + bin_edges[i+1])/2 for i in range(len(hist))],
                'counts': hist.tolist()
            }
        else:
            p_value_hist = {'bins': [], 'counts': []}
        
        # Create data for sampling distribution visualization
        x_range = np.linspace(-4, 4, 100)
        null_dist = stats.norm.pdf(x_range, 0, 1)  # Null distribution (standard normal)
        alt_dist = stats.norm.pdf(x_range, (self.alt_mean - self.null_mean) / self.se, 1)
        
        # Critical regions
        if self.test_type == 'two-sided':
            critical_regions = [(-4, -self.critical_z), (self.critical_z, 4)]
        elif self.test_type == 'right-tailed':
            critical_regions = [(self.critical_z, 4)]
        else:  # left-tailed
            critical_regions = [(-4, self.critical_z)]
        
        return {
            'type': 'hypothesis_test',
            'p_value_histogram': p_value_hist,
            'test_statistics': test_stats,
            'sampling_distributions': {
                'x': x_range.tolist(),
                'null': null_dist.tolist(),
                'alternative': alt_dist.tolist()
            },
            'critical_regions': critical_regions,
            'critical_value': self.critical_z,
            'alpha': self.alpha,
            'rejection_rate': (self.results['reject_count'] / self.results['total_tests']
                             if self.results['total_tests'] > 0 else 0)
        }