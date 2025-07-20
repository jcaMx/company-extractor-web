import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";
// Use in axios calls: `${API_URL}/api/extract`

function App() {
  const [url, setUrl] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);


  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('http://localhost:5000/api/extract', { url });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <h1 className="app-title">Company Extractor</h1>
      
      <form onSubmit={handleSubmit} className="form">
        <label htmlFor="url">Enter Company URL:</label>
        <input
          type="text"
          id="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          required
          placeholder="https://example.com"
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Extracting...' : 'Extract'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {result && (  
        <div className="results">
          <h2>Results for: {result.company}</h2>
          {Object.entries(result.summaries || {}).map(([section, content]) => (
            <div key={section} className="section">
              <h3>{section.toUpperCase()}</h3>
              <p>{content.summary}</p>
              <a href={content.url} target="_blank" rel="noopener noreferrer">
                View original page
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;