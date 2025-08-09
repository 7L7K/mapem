// frontend/src/shared/components/ui/Input.jsx
import React from "react";

export default function Input({
    type = "text",
    value,
    onChange,
    placeholder = "",
    className = "",
    disabled = false,
    ...rest
}) {
    return (
        <input
            type={type}
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            disabled={disabled}
            className={
                "w-full bg-[var(--surface)]/90 text-[var(--text)] placeholder:text-[color:var(--dim)] " +
                "border border-[color:var(--border)] rounded-md px-3 py-2 " +
                "focus:outline-none focus:ring-2 focus:ring-white/20 focus:border-white/10 " +
                "transition-shadow " +
                className
            }
            {...rest}
        />
    );
}


