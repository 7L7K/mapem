// SearchPanel component
import React, { useState } from 'react';
import { search } from '../services/api';

const SearchPanel = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);

  const handleSearch = async () => {
    try {
      const res = await search(query);
      setResults(res.data.results);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <h2>Search Panel</h2>
      <input
        type="text"
        placeholder="Enter search query"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button onClick={handleSearch}>Search</button>
      {results && (
        <div>
          <h3>Results:</h3>
          <pre>{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default SearchPanel;
