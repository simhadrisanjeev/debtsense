import { type HTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/utils";

// ─── Card Root ───────────────────────────────────────────────────────────────

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

function Card({ className, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-gray-200 bg-white shadow-sm",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ─── Card Header ─────────────────────────────────────────────────────────────

interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

function CardHeader({ className, children, ...props }: CardHeaderProps) {
  return (
    <div
      className={cn("border-b border-gray-200 px-6 py-4", className)}
      {...props}
    >
      {children}
    </div>
  );
}

// ─── Card Body ───────────────────────────────────────────────────────────────

interface CardBodyProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

function CardBody({ className, children, ...props }: CardBodyProps) {
  return (
    <div className={cn("px-6 py-4", className)} {...props}>
      {children}
    </div>
  );
}

// ─── Card Footer ─────────────────────────────────────────────────────────────

interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

function CardFooter({ className, children, ...props }: CardFooterProps) {
  return (
    <div
      className={cn(
        "border-t border-gray-200 bg-gray-50 px-6 py-3 rounded-b-xl",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export { Card, CardHeader, CardBody, CardFooter };
