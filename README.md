# Monte Carlo Statistical Simulation Dashboard

A high-performance Monte Carlo simulation platform with Python backend and interactive web frontend.

## Features

- **High-Performance Backend**: Python/NumPy for fast numerical computation
- **Real-time Updates**: WebSocket streaming for live results
- **Multiple Simulation Types**: π estimation, option pricing, hypothesis testing, VaR, MCMC
- **Interactive Visualization**: Real-time charts with Chart.js
- **RESTful API**: For batch processing and integration
- **Export Capabilities**: Save results as JSON, CSV, or images

## Repository Structure

```
monte-carlo-dashboard/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # Pydantic models
│   │   ├── websocket.py         # WebSocket handlers
│   │   └── api/
│   │       ├── __init__.py
│   │       └── routes.py        # REST API endpoints
│   ├── simulations/
│   │   ├── __init__.py
│   │   ├── base.py              # Base simulation class
│   │   ├── pi_estimation.py
│   │   ├── integration.py
│   │   ├── option_pricing.py
│   │   ├── hypothesis_testing.py
│   │   ├── value_at_risk.py
│   │   └── markov_chain.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── statistics.py        # Statistical utilities
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
│       └── test_simulations.py
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── app.js               # Main application
│   │   ├── api-client.js        # WebSocket/API client
│   │   ├── charts.js            # Chart management
│   │   ├── simulations.js       # Simulation controls
│   │   └── utils.js             # Utility functions
│   └── assets/
│       └── favicon.ico
├── notebooks/
│   ├── simulation_examples.ipynb
│   └── performance_analysis.ipynb
├── docker-compose.yml
├── README.md
├── LICENSE
└── .gitignore
```

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js (optional, for frontend development)
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/monte-carlo-dashboard.git
cd monte-carlo-dashboard
```

2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Open your browser to `http://localhost:8000`

### Using Docker

```bash
docker-compose up
```

## API Documentation

Once running, visit:
- Interactive API docs: `http://localhost:8000/docs`
- WebSocket endpoint: `ws://localhost:8000/ws/simulate`

## Development

### Running Tests
```bash
cd backend
pytest tests/
```

### Frontend Development
The frontend is served directly by FastAPI in development. For production, consider using a CDN or nginx.

## License

MIT License - see LICENSE file for details.