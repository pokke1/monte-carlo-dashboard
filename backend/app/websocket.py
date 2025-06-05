from fastapi import WebSocket
import asyncio
import json
from typing import Dict, Any

from simulations.pi_estimation import PiEstimation
from simulations.integration import MonteCarloIntegration
from simulations.option_pricing import OptionPricing
from simulations.hypothesis_testing import HypothesisTesting
from simulations.value_at_risk import ValueAtRisk
from simulations.markov_chain import MarkovChain

class SimulationWebSocket:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.current_simulation = None
        self.is_running = False
        
        # Map simulation types to classes
        self.simulation_classes = {
            'pi': PiEstimation,
            'integration': MonteCarloIntegration,
            'option-pricing': OptionPricing,
            'hypothesis': HypothesisTesting,
            'risk': ValueAtRisk,
            'markov': MarkovChain
        }
    
    async def connect(self):
        await self.websocket.accept()
        await self.send_message({
            'type': 'connection',
            'status': 'connected',
            'message': 'WebSocket connection established'
        })
    
    async def disconnect(self):
        self.is_running = False
        if self.current_simulation:
            self.current_simulation.stop()
    
    async def handle_message(self, data: Dict[str, Any]):
        message_type = data.get('type')
        
        if message_type == 'start_simulation':
            await self.start_simulation(data)
        elif message_type == 'stop_simulation':
            await self.stop_simulation()
        elif message_type == 'get_status':
            await self.send_status()
        else:
            await self.send_error(f"Unknown message type: {message_type}")
    
    async def start_simulation(self, data: Dict[str, Any]):
        if self.is_running:
            await self.send_error("Simulation already running")
            return
        
        simulation_type = data.get('simulation_type')
        params = data.get('params', {})
        
        if simulation_type not in self.simulation_classes:
            await self.send_error(f"Unknown simulation type: {simulation_type}")
            return
        
        # Create simulation instance
        SimulationClass = self.simulation_classes[simulation_type]
        self.current_simulation = SimulationClass(**params)
        self.is_running = True
        
        # Send start confirmation
        await self.send_message({
            'type': 'simulation_started',
            'simulation_type': simulation_type,
            'params': params
        })
        
        # Run simulation
        try:
            async for result in self.current_simulation.run():
                if not self.is_running:
                    break
                
                await self.send_message({
                    'type': 'simulation_update',
                    'data': result
                })
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
            
            # Send completion message
            if self.is_running:
                await self.send_message({
                    'type': 'simulation_complete',
                    'final_results': self.current_simulation.get_final_results()
                })
        
        except Exception as e:
            await self.send_error(f"Simulation error: {str(e)}")
        
        finally:
            self.is_running = False
            self.current_simulation = None
    
    async def stop_simulation(self):
        if self.is_running and self.current_simulation:
            self.is_running = False
            self.current_simulation.stop()
            await self.send_message({
                'type': 'simulation_stopped',
                'message': 'Simulation stopped by user'
            })
    
    async def send_status(self):
        await self.send_message({
            'type': 'status',
            'is_running': self.is_running,
            'simulation_type': type(self.current_simulation).__name__ if self.current_simulation else None
        })
    
    async def send_message(self, message: Dict[str, Any]):
        await self.websocket.send_json(message)
    
    async def send_error(self, error: str):
        await self.send_message({
            'type': 'error',
            'error': error
        })