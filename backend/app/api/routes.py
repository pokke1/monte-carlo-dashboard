from fastapi import APIRouter, HTTPException, Response
from typing import List, Optional
import json
import csv
from io import StringIO
from datetime import datetime
import uuid

from app.models import (
    SimulationResult, 
    ExportFormat,
    ErrorResponse
)

api_router = APIRouter()

# In-memory storage for simulation results (in production, use a database)
simulation_results = {}

@api_router.get("/simulations/history", response_model=List[SimulationResult])
async def get_simulation_history(limit: int = 10, offset: int = 0):
    """Get history of simulation results"""
    # Sort by timestamp (newest first)
    sorted_results = sorted(
        simulation_results.values(), 
        key=lambda x: x.get('timestamp', 0), 
        reverse=True
    )
    
    # Apply pagination
    return sorted_results[offset:offset + limit]

@api_router.get("/simulations/{simulation_id}", response_model=SimulationResult)
async def get_simulation_result(simulation_id: str):
    """Get a specific simulation result"""
    if simulation_id not in simulation_results:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return simulation_results[simulation_id]

@api_router.post("/simulations/{simulation_id}/save")
async def save_simulation_result(simulation_id: str, result: SimulationResult):
    """Save simulation result (called internally by WebSocket handler)"""
    result.simulation_id = simulation_id
    simulation_results[simulation_id] = {
        **result.dict(),
        'timestamp': datetime.utcnow().isoformat()
    }
    return {"message": "Simulation result saved", "id": simulation_id}

@api_router.get("/simulations/{simulation_id}/export")
async def export_simulation_result(
    simulation_id: str,
    format: ExportFormat = ExportFormat.JSON
):
    """Export simulation results in various formats"""
    if simulation_id not in simulation_results:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    result = simulation_results[simulation_id]
    
    if format == ExportFormat.JSON:
        # Return as JSON
        return Response(
            content=json.dumps(result, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=simulation_{simulation_id}.json"
            }
        )
    
    elif format == ExportFormat.CSV:
        # Convert to CSV format
        output = StringIO()
        writer = csv.writer(output)
        
        # Write basic info
        writer.writerow(["Simulation Results"])
        writer.writerow(["ID", simulation_id])
        writer.writerow(["Type", result['simulation_type']])
        writer.writerow(["Total Iterations", result['total_iterations']])
        writer.writerow([])
        
        # Write statistics
        writer.writerow(["Statistics"])
        writer.writerow(["Metric", "Value"])
        for key, value in result['statistics'].items():
            writer.writerow([key, value])
        writer.writerow([])
        
        # Write convergence history
        if result.get('convergence_history'):
            writer.writerow(["Convergence History"])
            history = result['convergence_history']
            if history:
                headers = list(history[0].keys())
                writer.writerow(headers)
                for row in history:
                    writer.writerow([row.get(h, '') for h in headers])
        
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=simulation_{simulation_id}.csv"
            }
        )

@api_router.delete("/simulations/{simulation_id}")
async def delete_simulation_result(simulation_id: str):
    """Delete a simulation result"""
    if simulation_id not in simulation_results:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    del simulation_results[simulation_id]
    return {"message": "Simulation result deleted"}

@api_router.get("/simulations/stats/summary")
async def get_simulation_stats():
    """Get summary statistics of all simulations"""
    total_simulations = len(simulation_results)
    
    if total_simulations == 0:
        return {
            "total_simulations": 0,
            "by_type": {},
            "average_iterations": 0,
            "total_iterations": 0
        }
    
    by_type = {}
    total_iterations = 0
    
    for result in simulation_results.values():
        sim_type = result['simulation_type']
        by_type[sim_type] = by_type.get(sim_type, 0) + 1
        total_iterations += result.get('total_iterations', 0)
    
    return {
        "total_simulations": total_simulations,
        "by_type": by_type,
        "average_iterations": total_iterations / total_simulations,
        "total_iterations": total_iterations
    }