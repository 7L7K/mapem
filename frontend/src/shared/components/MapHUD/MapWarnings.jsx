import React, { useMemo } from 'react';

export default function MapWarnings({ segments = [] }) {
    const { suspicious, impossible } = useMemo(() => {
        let s = 0, imp = 0;
        for (const seg of segments) {
            if (seg?.impossible) imp += 1;
            else if (seg?.suspicious) s += 1;
        }
        return { suspicious: s, impossible: imp };
    }, [segments]);

    if (!suspicious && !impossible) return null;

    return (
        <div className="absolute left-4 top-4 z-50 bg-black/70 text-white text-xs px-3 py-2 rounded-md border border-white/10 space-x-3">
            {suspicious > 0 && <span>⚠️ {suspicious} suspicious</span>}
            {impossible > 0 && <span>🚫 {impossible} impossible</span>}
        </div>
    );
}


