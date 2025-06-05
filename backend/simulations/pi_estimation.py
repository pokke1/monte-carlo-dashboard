import numpy as np
from typing import Dict, Any
from .base import BaseSimulation

class PiEstimation(BaseSimulation):
    """Monte Carlo simulation for estimating π"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.results = {
            'inside_circle': 0,
            'total_points': 0,
            'sample_points': []  # For visualization
        }
        self.max_viz_points = 5000
    
    async def simulate_batch(self, batch_size: int) -> Dict[str, Any]:
        """Generate random points and check if they're inside the unit circle"""
        # Generate random points in [-1, 1] x [-1, 1]
        points = np.random.uniform(-1, 1, size=(batch_size, 2))
        
        # Check which points are inside the unit circle
        distances_squared = np.sum(points ** 2, axis=1)
        inside = np.sum(distances_squared <= 1)
        
        # Sample points for visualization (limit total stored)
        current_viz_count = len(self.results['sample_points'])
        if current_viz_count < self.max_viz_points:
            # Sample proportionally to maintain distribution
            sample_size = min(100, batch_size, self.max_viz_points - current_viz_count)
            if sample_size > 0:
                indices = np.random.choice(batch_size, sample_size, replace=False)
                sample_points = points[indices].tolist()
            else:
                sample_points = []
        else:
            sample_points = []
        
        return {
            'inside_circle': int(inside),
            'total_points': batch_size,
            'sample_points': sample_points
        }
    
    def calculate_statistics(self) -> Dict[str, float]:
        """Calculate π estimate and statistics"""
        if self.results['total_points'] == 0:
            return {
                'estimate': 0.0,
                'std_error': 0.0,
                'lower_ci': 0.0,
                'upper_ci': 0.0,
                'true_value': np.pi,
                'error': 0.0
            }
        
        # π ≈ 4 * (points inside circle) / (total points)
        p = self.results['inside_circle'] / self.results['total_points']
        estimate = 4 * p
        
        # Standard error using binomial variance
        variance = p * (1 - p) / self.results['total_points']
        std_error = 4 * np.sqrt(variance)
        
        # Confidence interval
        lower_ci, upper_ci = self.calculate_confidence_interval(estimate, std_error)
        
        return {
            'estimate': estimate,
            'std_error': std_error,
            'lower_ci': lower_ci,
            'upper_ci': upper_ci,
            'true_value': np.pi,
            'error': abs(estimate - np.pi),
            'relative_error': abs(estimate - np.pi) / np.pi * 100
        }
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """Get scatter plot data for visualization"""
        # Limit points for performance
        points = self.results['sample_points']
        if len(points) > 1000:
            # Randomly sample 1000 points
            indices = np.random.choice(len(points), 1000, replace=False)
            points = [points[i] for i in indices]
        
        return {
            'type': 'scatter',
            'points': points,
            'x_range': [-1, 1],
            'y_range': [-1, 1],
            'inside_ratio': (self.results['inside_circle'] / self.results['total_points'] 
                           if self.results['total_points'] > 0 else 0)
        }