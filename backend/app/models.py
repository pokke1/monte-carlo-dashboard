from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from enum import Enum

class SimulationType(str, Enum):
    PI = "pi"
    INTEGRATION = "integration"
    OPTION_PRICING = "option-pricing"
    HYPOTHESIS = "hypothesis"
    RISK = "risk"
    MARKOV = "markov"

class BaseSimulationParams(BaseModel):
    n_simulations: int = Field(10000, ge=1000, le=10000000)
    batch_size: int = Field(1000, ge=100, le=50000)
    update_frequency: int = Field(1000, ge=100, le=50000)
    seed: Optional[int] = None

class IntegrationParams(BaseSimulationParams):
    function_type: str = Field("gaussian", pattern="^(gaussian|sine|polynomial|exponential|reciprocal)$")
    lower_bound: float = Field(-2.0)
    upper_bound: float = Field(2.0)
    
    @validator('upper_bound')
    def validate_bounds(cls, v, values):
        if 'lower_bound' in values and v <= values['lower_bound']:
            raise ValueError('Upper bound must be greater than lower bound')
        return v

class OptionPricingParams(BaseSimulationParams):
    stock_price: float = Field(100.0, gt=0)
    strike_price: float = Field(110.0, gt=0)
    volatility: float = Field(0.2, gt=0, le=2)
    risk_free_rate: float = Field(0.05, ge=-0.1, le=0.5)
    time_to_maturity: float = Field(1.0, gt=0, le=10)
    option_type: str = Field("call", pattern="^(call|put)$")

class HypothesisParams(BaseSimulationParams):
    null_mean: float = Field(0.0)
    alt_mean: float = Field(0.5)
    std_dev: float = Field(1.0, gt=0)
    sample_size: int = Field(30, ge=2, le=1000)
    alpha: float = Field(0.05, gt=0, lt=1)
    test_type: str = Field("two-sided", pattern="^(two-sided|right-tailed|left-tailed)$")

class RiskParams(BaseSimulationParams):
    portfolio_value: float = Field(1000000, gt=0)
    expected_return: float = Field(0.08, ge=-1, le=1)
    portfolio_volatility: float = Field(0.15, gt=0, le=2)
    time_horizon: int = Field(10, ge=1, le=252)
    confidence_level: float = Field(0.95, gt=0.5, lt=1)
    distribution: str = Field("normal", pattern="^(normal|t|historical)$")

class MarkovParams(BaseSimulationParams):
    distribution_type: str = Field("normal", pattern="^(normal|gamma|beta|bimodal|cauchy|exponential)$")
    burn_in: int = Field(1000, ge=0, le=100000)
    step_size: float = Field(0.5, gt=0, le=10)
    initial_value: float = Field(0.0)

class SimulationRequest(BaseModel):
    simulation_type: SimulationType
    params: Dict[str, Any]

class SimulationUpdate(BaseModel):
    iteration: int
    progress: float
    statistics: Dict[str, float]
    visualization: Dict[str, Any]
    convergence_history: List[Dict[str, float]]

class SimulationResult(BaseModel):
    simulation_id: Optional[str] = None
    simulation_type: SimulationType
    total_iterations: int
    statistics: Dict[str, float]
    convergence_history: List[Dict[str, float]]
    visualization: Dict[str, Any]
    parameters: Dict[str, Any]
    execution_time: Optional[float] = None

class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None