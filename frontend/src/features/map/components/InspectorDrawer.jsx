import React, { useMemo } from "react";
import Drawer from "@shared/components/ui/Drawer";

export default function InspectorDrawer({ open, onClose, selection }) {
    const details = useMemo(() => {
        if (!selection) return null;
        if (selection.type === "arc") {
            const s = selection.data;
            return {
                title: (s?.names && s.names[0]) || "Movement",
                items: [
                    ["From", `${s?.from?.lat?.toFixed?.(3)}, ${s?.from?.lng?.toFixed?.(3)} ${s?.from?.date || ""}`],
                    ["To", `${s?.to?.lat?.toFixed?.(3)}, ${s?.to?.lng?.toFixed?.(3)} ${s?.to?.date || ""}`],
                    ["Type", s?.event_type || "move"],
                ],
            };
        }
        if (selection.type === "point") {
            const p = selection.data;
            return {
                title: p?.name || "Event",
                items: [
                    ["Year", p?.year ?? "?"],
                    ["Type", p?.event_type || ""],
                    ["Person ID", p?.person_id || ""],
                ],
            };
        }
        return null;
    }, [selection]);

    return (
        <Drawer open={!!open} onClose={onClose} width="w-[420px]">
            <div className="p-4 space-y-4">
                <div className="flex items-center justify-between">
                    <h4 className="font-semibold">Inspector</h4>
                    <button onClick={onClose} className="text-white/70 hover:text-white">✕</button>
                </div>
                {details && (
                    <div className="space-y-2">
                        <div className="text-lg font-bold">{details.title}</div>
                        <ul className="space-y-1 text-sm">
                            {details.items.map(([k, v]) => (
                                <li key={k} className="flex justify-between gap-4">
                                    <span className="text-white/60">{k}</span>
                                    <span className="text-white">{String(v)}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
                <div className="pt-3 border-t border-white/10">
                    <button className="px-3 py-2 bg-yellow-400 text-black rounded font-semibold hover:bg-yellow-300">Re-resolve place</button>
                </div>
            </div>
        </Drawer>
    );
}


