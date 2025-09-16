# Add this at the very top of your main.py file, before any other imports
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import sqlite3
import yfinance as yf
from requests_cache import CachedSession 
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio
import aiohttp
import json
import io
import csv
from dataclasses import dataclass
from enum import Enum
import os
import time
import random
from contextlib import asynccontextmanager
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests_cache import CachedSession




app = FastAPI(title="ETF & Stock AI Briefs", version="1.0.0")

# CORS middleware - MUST be here, right after app creation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Create a persistent session for yfinance with caching
session = CachedSession("yfinance_cache", expire_after=300)


# In-memory cache for API responses
CACHE = {}
CACHE_TTL = 300  # seconds (5 minutes)



# Configure requests session with retries
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Add headers to avoid being blocked
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session



class TimeRange(str, Enum):
    SEVEN_DAYS = "7d"
    ONE_MONTH = "1mo"
    SIX_MONTHS = "6mo"
    ONE_YEAR = "1y"

@dataclass
class Metrics:
    returns: float
    volatility: float
    max_drawdown: float
    current_price: float
    price_change: float
    price_change_pct: float

# Database setup
def init_db():
    conn = sqlite3.connect("market_data.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            symbol TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            PRIMARY KEY (symbol, date)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            symbol TEXT,
            as_of TEXT,
            text TEXT,
            horizon TEXT,
            PRIMARY KEY (symbol, as_of, horizon)
        )
    """)
    
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    pass


def get_db_connection():
    return sqlite3.connect("market_data.db")

def yf_range_to_period(range_str: str) -> str:
    """Convert our range format to yfinance period"""
    mapping = {
        "7d": "7d",
        "1mo": "1mo", 
        "6mo": "6mo",
        "1y": "1y"
    }
    return mapping.get(range_str, "1mo")

def calculate_metrics(prices_df: pd.DataFrame) -> Metrics:
    """Calculate key financial metrics from price data"""
    if len(prices_df) < 2:
        return Metrics(0, 0, 0, 0, 0, 0)
    
    # Sort by date to ensure chronological order
    prices_df = prices_df.sort_values('date')
    closes = prices_df['close'].values
    
    # Returns (total period return)
    total_return = (closes[-1] - closes[0]) / closes[0]
    
    # Daily returns for volatility calculation
    daily_returns = np.diff(closes) / closes[:-1]
    volatility = np.std(daily_returns) * np.sqrt(252)  # Annualized
    
    # Max drawdown
    cumulative = (1 + daily_returns).cumprod()
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = np.min(drawdown)
    
    # Current metrics
    current_price = closes[-1]
    price_change = closes[-1] - closes[-2] if len(closes) > 1 else 0
    price_change_pct = price_change / closes[-2] if len(closes) > 1 and closes[-2] != 0 else 0
    
    return Metrics(
        returns=total_return,
        volatility=volatility,
        max_drawdown=max_drawdown,
        current_price=current_price,
        price_change=price_change,
        price_change_pct=price_change_pct
    )

def create_sample_data(symbol: str, days: int = 30):
    """Create sample data if yfinance fails - for demo purposes"""
    print(f"Creating sample data for {symbol}")
    
    # Base price depends on symbol
    base_prices = {
        'AAPL': 180.0,
        'MSFT': 350.0, 
        'GOOGL': 140.0,
        'SPY': 450.0,
        'QQQ': 380.0,
        'TSLA': 200.0
    }
    
    base_price = base_prices.get(symbol, 100.0)
    
    # Generate sample price data
    dates = []
    prices = []
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=days-i-1)).strftime("%Y-%m-%d")
        # Simple random walk with slight upward bias
        if i == 0:
            price = base_price
        else:
            change = random.uniform(-0.03, 0.035)  # -3% to +3.5% daily change
            price = prices[-1] * (1 + change)
            price = max(price, base_price * 0.7)  # Don't go below 70% of base
        
        dates.append(date)
        prices.append(price)
    
    # Create DataFrame
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        volume = random.randint(10000000, 100000000)  # Random volume
        high = price * random.uniform(1.0, 1.03)
        low = price * random.uniform(0.97, 1.0)
        open_price = random.uniform(low, high)
        
        data.append({
            'date': date,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(price, 2),
            'volume': volume
        })
    
    return data

def fetch_yfinance_with_retry(symbol: str, period: str, max_retries: int = 2):
    """Fetch data from yfinance with retry logic, cache, and fallback to sample data"""
    
    cache_key = (symbol, period)
    now = time.time()

    # Check cache first
    if cache_key in CACHE:
        data, timestamp = CACHE[cache_key]
        if now - timestamp < CACHE_TTL:
            print(f"Cache hit for {symbol} {period} (age: {int(now - timestamp)}s)")
            return data
        else:
            print(f"Cache expired for {symbol} {period}")
            del CACHE[cache_key]

    print(f"=== Fetching data for {symbol} with period {period} ===")

    for attempt in range(max_retries):
        try:
            print(f"yfinance attempt {attempt + 1}/{max_retries} for {symbol}")

            # Session for yfinance
            ticker = yf.Ticker(symbol, session=session)

            # Retry delay
            if attempt > 0:
                delay = random.uniform(2, 5)
                print(f"Waiting {delay:.1f}s before retry...")
                time.sleep(delay)

            ticker = yf.Ticker(symbol, session=session)

            hist = ticker.history(
                period=period,
                interval="1d",
                auto_adjust=True,
                prepost=False,
                repair=True,
                timeout=10
            )

            if hist is not None and not hist.empty and len(hist) >= 2:
                print(f"SUCCESS: Got {len(hist)} records from yfinance for {symbol}")

                data = [
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"]),
                    }
                    for date, row in hist.iterrows()
                ]

                # Store in cache
                CACHE[cache_key] = (data, now)
                return data

        except Exception as e:
            print(f"yfinance attempt {attempt + 1} failed: {e}")
            continue

    # Fallback to sample data
    print(f"yfinance failed for {symbol}, using sample data for demo")
    days = 30 if period in ["1mo", "7d"] else (180 if period == "6mo" else 365)
    data = create_sample_data(symbol, days)

    # Store fallback in cache too
    CACHE[cache_key] = (data, now)
    return data




@app.get("/prices")
async def get_prices(
    symbol: str = Query(..., description="Stock/ETF symbol"),
    range: TimeRange = Query(TimeRange.ONE_MONTH, description="Time range")
):
    """Fetch and cache price data for a symbol"""
    
    symbol = symbol.upper().strip()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we have recent data (within last 4 hours)
    four_hours_ago = (datetime.now() - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        SELECT COUNT(*) FROM prices 
        WHERE symbol = ? AND date >= DATE('now', '-1 day')
    """, (symbol,))
    
    has_recent_data = cursor.fetchone()[0] > 0
    
    if not has_recent_data:
        try:
            period = yf_range_to_period(range.value)
            price_data = fetch_yfinance_with_retry(symbol, period)
            
            # Clear old data for this symbol
            cursor.execute("DELETE FROM prices WHERE symbol = ?", (symbol,))
            
            # Insert new data
            for row in price_data:
                cursor.execute("""
                    INSERT OR REPLACE INTO prices 
                    (symbol, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol,
                    row['date'],
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    row['volume']
                ))
            
            conn.commit()
            print(f"Stored {len(price_data)} records for {symbol}")
            
        except Exception as e:
            conn.close()
            raise HTTPException(status_code=500, detail=f"Error processing data for {symbol}: {str(e)}")
    
    # Retrieve data for the requested range
    end_date = datetime.now()
    if range.value == "7d":
        start_date = end_date - timedelta(days=7)
    elif range.value == "1mo":
        start_date = end_date - timedelta(days=30)
    elif range.value == "6mo":
        start_date = end_date - timedelta(days=180)
    else:  # 1y
        start_date = end_date - timedelta(days=365)
    
    cursor.execute("""
        SELECT date, open, high, low, close, volume 
        FROM prices 
        WHERE symbol = ? AND date >= ?
        ORDER BY date
    """, (symbol, start_date.strftime("%Y-%m-%d")))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
    
    # Convert to DataFrame for metrics calculation
    df = pd.DataFrame(rows, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    metrics = calculate_metrics(df)
    
    # Format response
    price_data = [
        {
            "date": row[0],
            "open": row[1],
            "high": row[2],
            "low": row[3],
            "close": row[4],
            "volume": row[5]
        }
        for row in rows
    ]
    
    print(f"Returning {len(price_data)} data points for {symbol}")
    
    return {
        "symbol": symbol,
        "range": range.value,
        "data": price_data,
        "metrics": {
            "returns": round(metrics.returns * 100, 2),
            "volatility": round(metrics.volatility * 100, 2),
            "max_drawdown": round(metrics.max_drawdown * 100, 2),
            "current_price": round(metrics.current_price, 2),
            "price_change": round(metrics.price_change, 2),
            "price_change_pct": round(metrics.price_change_pct * 100, 2)
        }
    }

@app.post("/summarize")
async def generate_summary(
    symbol: str = Query(..., description="Stock/ETF symbol"),
    range: TimeRange = Query(TimeRange.ONE_MONTH, description="Time range")
):
    """Generate AI summary for a symbol"""
    
    # Check cache first
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT text FROM summaries 
        WHERE symbol = ? AND as_of = ? AND horizon = ?
    """, (symbol.upper(), today, range.value))
    
    cached = cursor.fetchone()
    if cached:
        conn.close()
        return {"symbol": symbol.upper(), "summary": cached[0], "cached": True}
    
    # Get price data and metrics
    try:
        price_response = await get_prices(symbol, range)
        metrics = price_response["metrics"]
        data = price_response["data"]
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Could not fetch price data: {str(e)}")
    
    # Generate summary
    summary = generate_mock_summary(symbol.upper(), metrics, range.value)
    
    # Cache the summary
    cursor.execute("""
        INSERT OR REPLACE INTO summaries (symbol, as_of, text, horizon)
        VALUES (?, ?, ?, ?)
    """, (symbol.upper(), today, summary, range.value))
    
    conn.commit()
    conn.close()
    
    return {"symbol": symbol.upper(), "summary": summary, "cached": False}

def generate_mock_summary(symbol: str, metrics: dict, range_val: str) -> str:
    """Generate a mock AI summary"""
    
    if metrics['returns'] > 5:
        trend = "strong upward"
    elif metrics['returns'] > 0:
        trend = "modest upward"
    elif metrics['returns'] > -5:
        trend = "sideways to slightly negative"
    else:
        trend = "significant downward"
    
    if metrics['volatility'] > 30:
        risk_level = "high"
    elif metrics['volatility'] > 20:
        risk_level = "moderate to high"
    elif metrics['volatility'] > 15:
        risk_level = "moderate"
    else:
        risk_level = "relatively low"
    
    if abs(metrics['price_change_pct']) > 3:
        daily_note = "with notable volatility in today's session"
    elif metrics['price_change_pct'] > 1:
        daily_note = "showing strength in today's trading"
    elif metrics['price_change_pct'] < -1:
        daily_note = "under pressure in today's session"
    else:
        daily_note = "trading relatively flat today"
    
    summary = f"""{symbol} has shown a {trend} trend over the past {range_val}, with a total return of {metrics['returns']}% and currently trading at ${metrics['current_price']}. The stock is {daily_note}, with a daily change of {metrics['price_change_pct']}%.

From a risk perspective, {symbol} exhibits {risk_level} volatility at {metrics['volatility']}% annualized, with a maximum drawdown of {metrics['max_drawdown']}% during this period. This suggests investors should be prepared for potential price swings of this magnitude.

The recent price action reflects broader market dynamics and sector-specific factors that typically influence securities in this category. Current trading volumes and price levels suggest {('continued interest from institutional and retail investors' if metrics['returns'] >= 0 else 'some profit-taking or risk-off sentiment among market participants')}."""
    
    return summary.strip()

@app.get("/export/{symbol}")
async def export_data(symbol: str, range: TimeRange = Query(TimeRange.ONE_MONTH)):
    """Export price data and metrics to CSV"""
    try:
        price_response = await get_prices(symbol, range)
        data = price_response["data"]
        metrics = price_response["metrics"]
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["Symbol", symbol.upper()])
        writer.writerow(["Range", range.value])
        writer.writerow(["Export Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow([])
        
        writer.writerow(["Metrics"])
        writer.writerow(["Current Price", f"${metrics['current_price']}"])
        writer.writerow(["Price Change", f"${metrics['price_change']} ({metrics['price_change_pct']}%)"])
        writer.writerow(["Total Return", f"{metrics['returns']}%"])
        writer.writerow(["Volatility", f"{metrics['volatility']}%"])
        writer.writerow(["Max Drawdown", f"{metrics['max_drawdown']}%"])
        writer.writerow([])
        
        writer.writerow(["Date", "Open", "High", "Low", "Close", "Volume"])
        for row in data:
            writer.writerow([
                row["date"],
                row["open"],
                row["high"],
                row["low"],
                row["close"],
                row["volume"]
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={symbol}_{range.value}_data.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/search/{query}")
async def search_symbols(query: str):
    """Search for stock/ETF symbols"""
    common_symbols = {
        "SPY": "SPDR S&P 500 ETF Trust",
        "QQQ": "Invesco QQQ Trust",
        "VTI": "Vanguard Total Stock Market ETF",
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corporation",
        "GOOGL": "Alphabet Inc. Class A",
        "AMZN": "Amazon.com Inc.",
        "TSLA": "Tesla Inc.",
        "NVDA": "NVIDIA Corporation",
        "META": "Meta Platforms Inc.",
        "BRK-B": "Berkshire Hathaway Inc. Class B",
        "JNJ": "Johnson & Johnson",
        "V": "Visa Inc.",
        "WMT": "Walmart Inc.",
        "JPM": "JPMorgan Chase & Co."
    }
    
    query_upper = query.upper()
    matches = []
    
    for symbol, name in common_symbols.items():
        if (query_upper in symbol or 
            query_upper in name.upper() or
            symbol.startswith(query_upper)):
            matches.append({"symbol": symbol, "name": name})
    
    return {"results": matches[:10]}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
