import { cn } from "../../utils/cn";
import React from "react";

const Input = React.forwardRef(({ className, type, label, error, ...props }, ref) => {
    return (
        <div className="w-full space-y-2">
            {label && <label className="text-sm font-medium text-secondary">{label}</label>}
            <input
                type={type}
                className={cn(
                    "flex h-11 w-full rounded-lg border border-surface-hover bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:border-transparent disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-200 hover:border-muted",
                    error && "border-error focus-visible:ring-error",
                    className
                )}
                ref={ref}
                {...props}
            />
            {error && <p className="text-xs text-error animate-pulse">{error}</p>}
        </div>
    );
});

Input.displayName = "Input";

export { Input };
