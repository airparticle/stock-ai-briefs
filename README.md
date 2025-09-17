# ETF & Stock AI Briefs

AI-powered market analysis and insights dashboard for stocks and ETFs

## Features

- **Real-time Stock Data** - Live price data powered by Yahoo Finance
- **AI-Generated Analysis** - Smart market insights and trend analysis
- **Interactive Charts** - Beautiful price and volume visualizations
- **Key Metrics** - Returns, volatility, max drawdown, and more
- **Symbol Search** - Quick search for stocks and ETFs
- **Data Export** - Export data to CSV for further analysis
- **Fast Performance** - Cached data for optimal speed
- **Responsive Design** - Works on desktop and mobile

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- npm or yarn

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/etf-stock-ai-briefs.git
cd etf-stock-ai-briefs
```

2. **Set up the backend**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

3. **Set up the frontend** (in a new terminal)
```bash
cd frontend
npm install
npm run dev
```

4. **Open your browser**  
Navigate to `http://localhost:5173` and start analyzing!

## Architecture

### Backend (FastAPI + Python)

- **FastAPI** - Modern, fast web framework
- **SQLite** - Lightweight database for caching
- **yfinance** - Yahoo Finance API integration
- **pandas** - Data processing and analysis
- **Uvicorn** - ASGI web server

### Frontend (React + TypeScript)

- **React 18** - Modern UI framework
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Recharts** - Beautiful and responsive charts
- **Lucide React** - Clean and consistent icons

## Project Structure

```
etf-stock-ai-briefs/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── market_data.db      # SQLite database (auto-created)
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Main React component
│   │   ├── main.jsx        # React entry point
│   │   └── index.css       # Tailwind styles
│   ├── package.json        # Node.js dependencies
│   └── vite.config.js      # Vite configuration
└── README.md
```

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Cache Settings
CACHE_TTL=300

# Database
DATABASE_URL=sqlite:///./market_data.db
```

### Supported Time Ranges

- **7d** - 7 Days
- **1mo** - 1 Month
- **6mo** - 6 Months
- **1y** - 1 Year

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/prices?symbol={symbol}&range={range}` | Get stock price data and metrics |
| `POST` | `/summarize?symbol={symbol}&range={range}` | Generate AI analysis |
| `GET` | `/search/{query}` | Search for stock symbols |
| `GET` | `/export/{symbol}?range={range}` | Export data as CSV |
| `GET` | `/health` | Health check endpoint |

### Example API Usage

```bash
# Get Apple stock data for 1 month
curl "http://localhost:8000/prices?symbol=AAPL&range=1mo"

# Generate AI summary for Tesla
curl -X POST "http://localhost:8000/summarize?symbol=TSLA&range=6mo"

# Search for symbols
curl "http://localhost:8000/search/apple"
```

## Screenshots

### Main Dashboard
Beautiful, clean interface showing key metrics and interactive charts.
<img width="1524" height="819" alt="Image" src="https://github.com/user-attachments/assets/a56dc463-c2c1-46bf-b283-0e7b14cbcdc2" />
### AI Analysis
Smart insights powered by market data analysis and trend detection.
<img width="1540" height="374" alt="Image" src="https://github.com/user-attachments/assets/e079db8e-70c0-4c44-991d-6bf3cfd91283" />
### Symbol Search
Quick and intuitive search for thousands of stocks and ETFs.
<img width="1531" height="125" alt="Image" src="https://github.com/user-attachments/assets/314976ad-79a7-4f41-b59f-319df0dca175" />
## Deployment

### Using Docker

```bash
# Build the image
docker build -t etf-stock-ai-briefs .

# Run the container
docker run -p 8000:8000 etf-stock-ai-briefs
```

### Using Docker Compose

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_PORT=8000
    volumes:
      - ./data:/app/data
```

### Production Build

```bash
# Build frontend for production
cd frontend
npm run build

# Start backend in production mode
cd ../backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Performance

- **Caching**: Intelligent data caching reduces API calls
- **Async Operations**: Non-blocking data fetching
- **Optimized Charts**: Smooth rendering of large datasets
- **Response Times**: < 100ms for cached data, < 2s for fresh data

## Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add some amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Setup

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt
pip install pytest black flake8  # Dev dependencies

# Install frontend dependencies
cd frontend
npm install
npm install --save-dev @types/react @types/react-dom  # Dev dependencies

# Run tests
npm test  # Frontend tests
pytest    # Backend tests
```

## Acknowledgments

- **Yahoo Finance** - For providing free market data
- **FastAPI** - For the excellent Python web framework
- **React Team** - For the amazing frontend library
- **Tailwind CSS** - For beautiful, utility-first styling
- **Recharts** - For responsive and customizable charts
