import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator
import asyncio

class BaseSimulation(ABC):
    """Base class for all Monte Carlo simulations"""
    
    def __init__(self, n_simulations: int = 10000, batch_size: int = 1000, 
                 update_frequency: int = 1000, seed: int = None):
        self.n_simulations = n_simulations
        self.batch_size = min(batch_size, n_simulations)
        self.update_frequency = update_frequency
        self.current_iteration = 0
        self.is_running = True
        
        # Set random seed for reproducibility
        if seed is not None:
            np.random.seed(seed)
        
        # Results storage
        self.results = {}
        self.convergence_history = []
    
    @abstractmethod
    async def simulate_batch(self, batch_size: int) -> Dict[str, Any]:
        """Run a batch of simulations and return results"""
        pass
    
    @abstractmethod
    def calculate_statistics(self) -> Dict[str, float]:
        """Calculate current statistics (estimate, std error, etc.)"""
        pass
    
    @abstractmethod
    def get_visualization_data(self) -> Dict[str, Any]:
        """Get data for visualization"""
        pass
    
    async def run(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Main simulation loop"""
        self.is_running = True
        self.current_iteration = 0
        
        while self.current_iteration < self.n_simulations and self.is_running:
            # Calculate batch size for this iteration
            remaining = self.n_simulations - self.current_iteration
            current_batch_size = min(self.batch_size, remaining)
            
            # Run batch simulation
            batch_results = await self.simulate_batch(current_batch_size)
            self.current_iteration += current_batch_size
            
            # Update accumulated results
            self.update_results(batch_results)
            
            # Check if we should send an update
            if (self.current_iteration % self.update_frequency == 0 or 
                self.current_iteration == self.n_simulations):
                
                stats = self.calculate_statistics()
                
                # Store convergence history
                self.convergence_history.append({
                    'iteration': self.current_iteration,
                    'estimate': stats['estimate'],
                    'std_error': stats['std_error']
                })
                
                # Yield update
                yield {
                    'iteration': self.current_iteration,
                    'progress': self.current_iteration / self.n_simulations,
                    'statistics': stats,
                    'visualization': self.get_visualization_data(),
                    'convergence_history': self.get_convergence_data()
                }
            
            # Allow other tasks to run
            await asyncio.sleep(0)
    
    def update_results(self, batch_results: Dict[str, Any]):
        """Update accumulated results with batch results"""
        for key, value in batch_results.items():
            if key not in self.results:
                self.results[key] = value
            else:
                # Handle different types of accumulation
                if isinstance(value, (int, float, np.number)):
                    self.results[key] += value
                elif isinstance(value, np.ndarray):
                    self.results[key] = np.concatenate([self.results[key], value])
                elif isinstance(value, list):
                    self.results[key].extend(value)
    
    def get_convergence_data(self, max_points: int = 100) -> list:
        """Get convergence history, downsampled if necessary"""
        if len(self.convergence_history) <= max_points:
            return self.convergence_history
        
        # Downsample to max_points
        indices = np.linspace(0, len(self.convergence_history) - 1, max_points, dtype=int)
        return [self.convergence_history[i] for i in indices]
    
    def calculate_confidence_interval(self, estimate: float, std_error: float, 
                                    confidence: float = 0.95) -> tuple:
        """Calculate confidence interval"""
        z_score = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%
        lower = estimate - z_score * std_error
        upper = estimate + z_score * std_error
        return lower, upper
    
    def stop(self):
        """Stop the simulation"""
        self.is_running = False
    
    def get_final_results(self) -> Dict[str, Any]:
        """Get final results after simulation completes"""
        stats = self.calculate_statistics()
        return {
            'total_iterations': self.current_iteration,
            'statistics': stats,
            'convergence_history': self.convergence_history,
            'visualization': self.get_visualization_data()
        }