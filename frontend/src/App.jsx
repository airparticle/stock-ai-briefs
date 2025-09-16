import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Bar } from 'recharts';
import { Search, Download, TrendingUp, TrendingDown, Activity, DollarSign, AlertCircle, Calendar, BarChart3 } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const StockDashboard = () => {
  const [symbol, setSymbol] = useState('AAPL');
  const [range, setRange] = useState('1mo');
  const [priceData, setPriceData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [showSearch, setShowSearch] = useState(false);
  const [error, setError] = useState(null);

  const timeRanges = [
    { value: '7d', label: '7 Days' },
    { value: '1mo', label: '1 Month' },
    { value: '6mo', label: '6 Months' },
    { value: '1y', label: '1 Year' }
  ];

  const fetchPriceData = async (sym = symbol, rng = range) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/prices?symbol=${sym}&range=${rng}`);
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      const data = await response.json();
      setPriceData(data);
    } catch (err) {
      setError(err.message);
      setPriceData(null);
    } finally {
      setLoading(false);
    }
  };

  const generateSummary = async () => {
    setSummaryLoading(true);
    try {
      const response = await fetch(`${API_BASE}/summarize?symbol=${symbol}&range=${range}`, {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      const data = await response.json();
      setSummary(data);
    } catch (err) {
      setError(`Summary generation failed: ${err.message}`);
    } finally {
      setSummaryLoading(false);
    }
  };

  const searchSymbols = async (query) => {
    if (query.length < 1) {
      setSearchResults([]);
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/search/${query}`);
      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (err) {
      console.error('Search error:', err);
    }
  };

  const selectSymbol = (selectedSymbol) => {
    setSymbol(selectedSymbol);
    setShowSearch(false);
    setSearchResults([]);
    setSummary(null);
  };

  const exportData = async () => {
    try {
      const response = await fetch(`${API_BASE}/export/${symbol}?range=${range}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${symbol}_${range}_data.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(`Export failed: ${err.message}`);
    }
  };

  useEffect(() => {
    fetchPriceData();
  }, [symbol, range]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatPercent = (value) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const formatVolume = (value) => {
    if (value >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
    if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
    if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
    return value.toString();
  };

  const getChangeColor = (value) => {
    return value >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const getChangeIcon = (value) => {
    return value >= 0 ? TrendingUp : TrendingDown;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            ETF & Stock AI Briefs
          </h1>
          <p className="text-gray-600">
            AI-powered market analysis and insights dashboard
          </p>
        </div>

        {/* Search and Controls */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <div className="flex flex-col sm:flex-row gap-4 items-end">
            {/* Symbol Search */}
            <div className="flex-1 relative">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Stock/ETF Symbol
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={symbol}
                  onChange={(e) => {
                    setSymbol(e.target.value.toUpperCase());
                    searchSymbols(e.target.value);
                    setShowSearch(true);
                  }}
                  onFocus={() => setShowSearch(true)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter symbol (e.g., AAPL)"
                />
                
                {/* Search Results */}
                {showSearch && searchResults.length > 0 && (
                  <div className="absolute top-full left-0 right-0 z-10 bg-white border border-gray-200 rounded-lg shadow-lg mt-1 max-h-48 overflow-y-auto">
                    {searchResults.map((result, index) => (
                      <div
                        key={index}
                        onClick={() => selectSymbol(result.symbol)}
                        className="px-4 py-2 hover:bg-gray-50 cursor-pointer"
                      >
                        <div className="font-semibold">{result.symbol}</div>
                        <div className="text-sm text-gray-600">{result.name}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Time Range Selector */}
            <div className="sm:min-w-[140px]">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Time Range
              </label>
              <div className="flex bg-gray-100 rounded-lg p-1">
                {timeRanges.map((tr) => (
                  <button
                    key={tr.value}
                    onClick={() => setRange(tr.value)}
                    className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                      range === tr.value
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    {tr.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Export Button */}
            <button
              onClick={exportData}
              disabled={!priceData}
              className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Download className="h-4 w-4" />
              Export CSV
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2 text-red-800">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="bg-white rounded-xl shadow-lg p-8 mb-6">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">Loading market data...</span>
            </div>
          </div>
        )}

        {/* Main Content */}
        {priceData && !loading && (
          <>
            {/* Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Current Price</p>
                    <p className="text-2xl font-bold text-gray-800">
                      {formatCurrency(priceData.metrics.current_price)}
                    </p>
                  </div>
                  <DollarSign className="h-8 w-8 text-blue-600" />
                </div>
                <div className={`flex items-center gap-1 mt-2 ${getChangeColor(priceData.metrics.price_change_pct)}`}>
                  {React.createElement(getChangeIcon(priceData.metrics.price_change_pct), { className: "h-4 w-4" })}
                  <span className="text-sm font-medium">
                    {formatCurrency(priceData.metrics.price_change)} ({formatPercent(priceData.metrics.price_change_pct)})
                  </span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Return</p>
                    <p className={`text-2xl font-bold ${getChangeColor(priceData.metrics.returns)}`}>
                      {formatPercent(priceData.metrics.returns)}
                    </p>
                  </div>
                  <BarChart3 className="h-8 w-8 text-green-600" />
                </div>
                <p className="text-xs text-gray-500 mt-2">For selected period</p>
              </div>

              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Volatility</p>
                    <p className="text-2xl font-bold text-gray-800">
                      {formatPercent(priceData.metrics.volatility)}
                    </p>
                  </div>
                  <Activity className="h-8 w-8 text-orange-600" />
                </div>
                <p className="text-xs text-gray-500 mt-2">Annualized</p>
              </div>

              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Max Drawdown</p>
                    <p className="text-2xl font-bold text-red-600">
                      {formatPercent(priceData.metrics.max_drawdown)}
                    </p>
                  </div>
                  <TrendingDown className="h-8 w-8 text-red-600" />
                </div>
                <p className="text-xs text-gray-500 mt-2">Worst decline</p>
              </div>
            </div>

            {/* Price Chart */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800">Price Chart</h2>
                <Calendar className="h-5 w-5 text-gray-500" />
              </div>
              
              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={priceData.data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#666"
                      fontSize={12}
                      tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { 
                        month: 'short', 
                        day: 'numeric' 
                      })}
                    />
                    <YAxis 
                      yAxisId="price"
                      stroke="#666"
                      fontSize={12}
                      tickFormatter={(value) => `$${value.toFixed(2)}`}
                    />
                    <YAxis 
                      yAxisId="volume"
                      orientation="right"
                      stroke="#666"
                      fontSize={12}
                      tickFormatter={formatVolume}
                    />
                    <Tooltip 
                      formatter={(value, name) => {
                        if (name === 'Close Price') return [formatCurrency(value), name];
                        if (name === 'Volume') return [formatVolume(value), name];
                        return [value, name];
                      }}
                      labelFormatter={(date) => new Date(date).toLocaleDateString()}
                      contentStyle={{
                        backgroundColor: '#fff',
                        border: '1px solid #ccc',
                        borderRadius: '8px'
                      }}
                    />
                    <Bar 
                      yAxisId="volume"
                      dataKey="volume" 
                      fill="#e5e7eb" 
                      opacity={0.3}
                      name="Volume"
                    />
                    <Line 
                      yAxisId="price"
                      type="monotone" 
                      dataKey="close" 
                      stroke="#2563eb" 
                      strokeWidth={2}
                      dot={false}
                      name="Close Price"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* AI Summary Section */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800">AI Analysis</h2>
                <button
                  onClick={generateSummary}
                  disabled={summaryLoading}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {summaryLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Generating...
                    </>
                  ) : (
                    <>
                      <Activity className="h-4 w-4" />
                      Generate Brief
                    </>
                  )}
                </button>
              </div>
              
              {summary ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                      {summary.cached ? 'Cached' : 'Fresh Analysis'}
                    </span>
                    <span>for {summary.symbol}</span>
                  </div>
                  <div className="prose prose-sm max-w-none">
                    <p className="text-gray-700 leading-relaxed whitespace-pre-line">
                      {summary.summary}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Activity className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p>Click "Generate Brief" to get AI-powered analysis</p>
                  <p className="text-sm mt-1">Get insights on trends, risks, and market movements</p>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default StockDashboard;