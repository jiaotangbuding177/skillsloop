import type { ReactNode } from "react";
import { cn } from "@/utils/cn";

export function SectionTitle({
  children,
  variant = "light",
}: {
  children: ReactNode;
  variant?: "light" | "dark";
}) {
  return (
    <h2
      className={cn(
        "mb-8 text-center font-cond text-[26px] tracking-[0.22em] uppercase md:text-[32px]",
        variant === "light" ? "text-white/90" : "text-[#555]"
      )}
    >
      {children}
    </h2>
  );
}
