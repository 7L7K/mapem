// src/components/SearchPanel.jsx
import React, { useState } from 'react';

const SearchPanel = ({ onSearch }) => {
  const [query, setQuery] = useState('');

  const handleSearch = () => {
    if (onSearch) onSearch(query);
  };

  return (
    <div>
      <h2>Search Panel</h2>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search names, locations, etc..."
      />
      <button onClick={handleSearch}>Search</button>
    </div>
  );
};

export default SearchPanel;
