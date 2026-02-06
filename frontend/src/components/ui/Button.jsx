import { cva } from "class-variance-authority";
import { cn } from "../../utils/cn";
import React from "react";

const buttonVariants = cva(
    "inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-50 disabled:pointer-events-none active:scale-[0.98]",
    {
        variants: {
            variant: {
                primary: "bg-accent text-white hover:bg-accent-hover shadow-lg shadow-accent/25 hover:shadow-accent/40",
                secondary: "bg-surface text-primary hover:bg-surface-hover border border-surface-hover hover:border-muted/50",
                ghost: "hover:bg-surface-hover text-primary",
                destructive: "bg-error text-white hover:bg-red-600 shadow-lg shadow-error/25",
                outline: "border-2 border-accent text-accent hover:bg-accent hover:text-white",
            },
            size: {
                default: "h-11 px-6 py-2",
                sm: "h-9 px-4 rounded-md text-xs",
                lg: "h-14 px-8 rounded-xl text-lg",
                icon: "h-11 w-11",
            },
            width: {
                default: "",
                full: "w-full",
            }
        },
        defaultVariants: {
            variant: "primary",
            size: "default",
            width: "default",
        },
    }
);

const Button = React.forwardRef(({ className, variant, size, width, ...props }, ref) => {
    return (
        <button
            className={cn(buttonVariants({ variant, size, width, className }))}
            ref={ref}
            {...props}
        />
    );
});

Button.displayName = "Button";

export { Button, buttonVariants };
