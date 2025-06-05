import numpy as np
from typing import Dict, Any
from .base import BaseSimulation

class MonteCarloIntegration(BaseSimulation):
    """Monte Carlo integration for various functions"""
    
    def __init__(self, function_type: str = 'gaussian', 
                 lower_bound: float = -2.0, upper_bound: float = 2.0, **kwargs):
        super().__init__(**kwargs)
        
        self.function_type = function_type
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.range = upper_bound - lower_bound
        
        # Define functions
        self.functions = {
            'gaussian': lambda x: np.exp(-x**2),
            'sine': lambda x: np.sin(x),
            'polynomial': lambda x: x**3 - 2*x**2 + x,
            'exponential': lambda x: np.exp(-np.abs(x)),
            'reciprocal': lambda x: 1 / (1 + x**2)
        }
        
        if function_type not in self.functions:
            raise ValueError(f"Unknown function type: {function_type}")
        
        self.function = self.functions[function_type]
        
        # Results storage
        self.results = {
            'sum': 0.0,
            'sum_squared': 0.0,
            'count': 0,
            'sample_points': []
        }
        
        # Calculate analytical result if available
        self.analytical_result = self._get_analytical_result()
    
    def _get_analytical_result(self) -> float:
        """Get analytical result for comparison (if available)"""
        if self.function_type == 'polynomial':
            # ∫(x³ - 2x² + x)dx from a to b
            a, b = self.lower_bound, self.upper_bound
            return (b**4/4 - 2*b**3/3 + b**2/2) - (a**4/4 - 2*a**3/3 + a**2/2)
        elif self.function_type == 'sine':
            # ∫sin(x)dx from a to b
            a, b = self.lower_bound, self.upper_bound
            return -np.cos(b) + np.cos(a)
        elif self.function_type == 'gaussian' and self.lower_bound == -np.inf and self.upper_bound == np.inf:
            # ∫e^(-x²)dx from -∞ to ∞ = √π
            return np.sqrt(np.pi)
        else:
            # No simple analytical form
            return None
    
    async def simulate_batch(self, batch_size: int) -> Dict[str, Any]:
        """Perform Monte Carlo integration"""
        # Generate random points in the integration domain
        x_values = np.random.uniform(self.lower_bound, self.upper_bound, batch_size)
        
        # Evaluate function at these points
        y_values = self.function(x_values)
        
        # Store samples for visualization (limit to 1000 points)
        sample_points = []
        if len(self.results['sample_points']) < 1000:
            n_samples = min(50, batch_size, 1000 - len(self.results['sample_points']))
            if n_samples > 0:
                indices = np.random.choice(batch_size, n_samples, replace=False)
                sample_points = [(float(x_values[i]), float(y_values[i])) 
                               for i in indices]
        
        # Sum for Monte Carlo integration
        batch_sum = float(np.sum(y_values))
        batch_sum_squared = float(np.sum(y_values ** 2))
        
        return {
            'sum': batch_sum,
            'sum_squared': batch_sum_squared,
            'count': batch_size,
            'sample_points': sample_points
        }
    
    def calculate_statistics(self) -> Dict[str, float]:
        """Calculate integral estimate and statistics"""
        if self.results['count'] == 0:
            return {
                'estimate': 0.0,
                'std_error': 0.0,
                'lower_ci': 0.0,
                'upper_ci': 0.0,
                'analytical_result': self.analytical_result,
                'error': 0.0
            }
        
        # Monte Carlo estimate: (b-a) * (1/n) * Σf(xi)
        n = self.results['count']
        estimate = self.range * self.results['sum'] / n
        
        # Calculate variance and standard error
        mean_f = self.results['sum'] / n
        mean_f_squared = self.results['sum_squared'] / n
        variance_f = mean_f_squared - mean_f ** 2
        
        # Standard error of the integral estimate
        std_error = self.range * np.sqrt(variance_f / n)
        
        # Confidence interval
        lower_ci, upper_ci = self.calculate_confidence_interval(estimate, std_error)
        
        result = {
            'estimate': estimate,
            'std_error': std_error,
            'lower_ci': lower_ci,
            'upper_ci': upper_ci,
            'function_type': self.function_type,
            'bounds': [self.lower_bound, self.upper_bound]
        }
        
        if self.analytical_result is not None:
            result['analytical_result'] = self.analytical_result
            result['error'] = abs(estimate - self.analytical_result)
            result['relative_error'] = (abs(estimate - self.analytical_result) / 
                                       abs(self.analytical_result) * 100 
                                       if self.analytical_result != 0 else 0)
        
        return result
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """Get function plot data for visualization"""
        # Generate smooth function curve for visualization
        x_smooth = np.linspace(self.lower_bound, self.upper_bound, 200)
        y_smooth = self.function(x_smooth)
        
        # Prepare scatter points
        sample_points = self.results['sample_points']
        if len(sample_points) > 500:
            # Randomly sample 500 points for visualization
            indices = np.random.choice(len(sample_points), 500, replace=False)
            sample_points = [sample_points[i] for i in indices]
        
        return {
            'type': 'function_integration',
            'function_curve': {
                'x': x_smooth.tolist(),
                'y': y_smooth.tolist()
            },
            'sample_points': sample_points,
            'bounds': [self.lower_bound, self.upper_bound],
            'shaded_area': True  # Indicate to shade area under curve
        }