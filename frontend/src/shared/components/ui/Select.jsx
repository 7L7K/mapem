// frontend/src/shared/components/ui/Select.jsx
import React from "react";

export default function Select({
    value,
    onChange,
    children,
    className = "",
    disabled = false,
    ...rest
}) {
    return (
        <select
            value={value}
            onChange={onChange}
            disabled={disabled}
            className={
                "w-full bg-[var(--surface)]/90 text-[var(--text)] " +
                "border border-[color:var(--border)] rounded-md px-3 py-2 " +
                "focus:outline-none focus:ring-2 focus:ring-white/20 focus:border-white/10 " +
                "transition-shadow " +
                className
            }
            {...rest}
        >
            {children}
        </select>
    );
}


