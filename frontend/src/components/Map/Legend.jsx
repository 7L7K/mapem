import React, { useMemo } from 'react';
import { colorForPerson } from '../../utils/colors';


const Legend = ({ movements }) => {
  // build unique map of person_id → name
  const entries = useMemo(() => {
    const map = {};
    movements.forEach(m => {
      if (!map[m.person_id]) {
        map[m.person_id] = m.person_name;
      }
    });
    return Object.entries(map);
  }, [movements]);

  if (entries.length === 0) return null;
  return (
    <div className="fixed bottom-4 right-4 bg-black bg-opacity-60 text-white text-sm p-2 rounded shadow-lg max-h-60 overflow-y-auto z-40">
      <h4 className="font-semibold mb-1">Legend</h4>
      <ul className="space-y-1">
        {entries.map(([pid, name]) => (
          <li key={pid} className="flex items-center gap-2">
            <span
              className="w-4 h-4 rounded"
              style={{ backgroundColor: colorForPerson(pid) }}
            />
            {name}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Legend;
