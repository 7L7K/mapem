import React, { useEffect } from "react";

const QuickFilterBar = ({ filterState, setFilterState, onToggleDrawer }) => {
  useEffect(() => {
    console.log("⚙️ [QuickFilterBar] state:", filterState);
  }, [filterState]);

  const handleYearChange = (idx, val) => {
    const y = [...filterState.year];
    y[idx] = parseInt(val, 10);
    setFilterState({ ...filterState, year: y });
  };

  /** NOTE:  NO  `fixed top-0`  here anymore  **/
  return (
    <div className="bg-neutral-900 text-white w-full p-2 shadow flex flex-wrap items-center gap-4 border-b border-neutral-800">
      <span className="text-sm">View:</span>
      <select
        value={filterState.view}
        onChange={(e) => setFilterState({ ...filterState, view: e.target.value })}
        className="bg-neutral-800 px-2 py-1 rounded text-sm"
      >
        <option value="person">Person</option>
        <option value="family">Family</option>
        <option value="group">Group</option>
      </select>

      <span className="text-sm ml-4">Years:</span>
      <input
        type="number"
        value={filterState.year[0]}
        onChange={(e) => handleYearChange(0, e.target.value)}
        className="w-20 bg-neutral-800 px-2 py-1 rounded text-sm"
      />
      <span className="text-sm">to</span>
      <input
        type="number"
        value={filterState.year[1]}
        onChange={(e) => handleYearChange(1, e.target.value)}
        className="w-20 bg-neutral-800 px-2 py-1 rounded text-sm"
      />

      <label className="flex items-center gap-1 text-sm ml-4">
        <input
          type="checkbox"
          checked={filterState.vague}
          onChange={(e) => setFilterState({ ...filterState, vague: e.target.checked })}
        />
        Show Vague
      </label>

      <button
        onClick={onToggleDrawer}
        className="ml-auto bg-emerald-600 hover:bg-emerald-700 px-3 py-1 rounded text-sm font-semibold"
      >
        🧠 Advanced
      </button>
    </div>
  );
};

export default QuickFilterBar;
