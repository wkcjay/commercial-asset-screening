"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
};

export function Button({ children, className = "", ...props }: ButtonProps) {
  return (
    <button
      className={`inline-flex h-10 items-center justify-center gap-2 rounded border border-accent bg-accent px-3 text-sm font-semibold text-white shadow-panel transition hover:bg-[#17664b] disabled:cursor-not-allowed disabled:border-line disabled:bg-line disabled:text-slate-500 ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
