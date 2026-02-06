import { cn } from "../../utils/cn";
import React from "react";

const Card = React.forwardRef(({ className, ...props }, ref) => (
    <div
        ref={ref}
        className={cn(
            "rounded-xl border border-surface-hover bg-surface/50 p-6 text-primary shadow-sm backdrop-blur-sm",
            className
        )}
        {...props}
    />
));
Card.displayName = "Card";

export { Card };
