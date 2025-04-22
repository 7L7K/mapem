import React, { createContext, useContext, useReducer } from 'react';

const SearchContext = createContext();

const initialState = {
  query: '',
  mode: 'person',        // 'person' | 'family' | 'compare'
  filters: {
    eventTypes: { birth: true, death: true, residence: true },
    relations: { direct: true, siblings: false, cousins: false, inlaws: false },
    sources: { gedcom: true, census: true, manual: true, ai: true },
    vague: false,
  },
  decade: [1900, 2020],
  faintLevel: 0.5,       // opacity 0–1
  wholeTree: false,
  showFilters: false,
  selectedPerson: null,
};

function reducer(state, action) {
  switch (action.type) {
    case 'SET_QUERY':       return { ...state, query: action.payload };
    case 'SET_MODE':        return { ...state, mode: action.payload };
    case 'TOGGLE_FILTER':   {
      const { group, key } = action.payload;
      return {
        ...state,
        filters: {
          ...state.filters,
          [group]: {
            ...state.filters[group],
            [key]: !state.filters[group][key],
          },
        },
      };
    }
    case 'SET_DECADE':      return { ...state, decade: action.payload };
    case 'SET_FAINT':       return { ...state, faintLevel: action.payload };
    case 'TOGGLE_WHOLETREE':return { ...state, wholeTree: !state.wholeTree };
    case 'TOGGLE_DRAWER':   return { ...state, showFilters: !state.showFilters };
    case 'SET_PERSON':      return { ...state, selectedPerson: action.payload };
    default: return state;
  }
}

export function SearchProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  const value = {
    ...state,
    setQuery: (q) => dispatch({ type: 'SET_QUERY', payload: q }),
    setMode: (m) => dispatch({ type: 'SET_MODE', payload: m }),
    toggleFilter: (group, key) => dispatch({ type: 'TOGGLE_FILTER', payload: { group, key } }),
    setDecade: (range) => dispatch({ type: 'SET_DECADE', payload: range }),
    setFaintLevel: (val) => dispatch({ type: 'SET_FAINT', payload: val }),
    toggleWholeTree: () => dispatch({ type: 'TOGGLE_WHOLETREE' }),
    toggleFilters: () => dispatch({ type: 'TOGGLE_DRAWER' }),
    setSelectedPerson: (p) => dispatch({ type: 'SET_PERSON', payload: p }),
  };

  return <SearchContext.Provider value={value}>{children}</SearchContext.Provider>;
}

export const useSearch = () => {
  const ctx = useContext(SearchContext);
  if (!ctx) throw new Error('useSearch must be inside SearchProvider');
  return ctx;
};
