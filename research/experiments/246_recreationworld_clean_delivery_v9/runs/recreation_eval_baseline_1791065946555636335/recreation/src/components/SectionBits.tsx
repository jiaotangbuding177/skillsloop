import type { ReactNode } from "react";
import type { GalleryShot } from "@/data/site";
import { asset } from "@/assets";

export function SectionHeading({ title, tone = "dark" }: { title: string; tone?: "dark" | "light" }) {
  return (
    <div className="px-[10px] py-[20px] text-center text-[30px] uppercase tracking-[5px]">
      <h2
        className={`m-0 border-b pb-[10px] font-['Roboto_Condensed'] text-[30px] font-normal ${
          tone === "dark" ? "border-white/70 text-white" : "border-[#3f6ea6] text-[#3f6ea6]"
        }`}
      >
        {title}
      </h2>
    </div>
  );
}

export function FeatureBanner({ src, alt, caption }: { src: string; alt: string; caption?: string }) {
  return (
    <section className="relative">
      <img src={asset(src)} alt={alt} className="block h-[340px] w-full object-cover lg:h-[440px]" />
      {caption ? (
        <div className="absolute bottom-[30px] left-[10%] max-w-[300px] bg-[rgba(0,39,76,0.78)] p-[18px] text-[15px] italic leading-[1.4] text-white">
          <span className="mb-[6px] block text-right text-[12px] not-italic">^</span>
          {caption}
        </div>
      ) : null}
    </section>
  );
}

export function GalleryStrip({ shots, columns = 4 }: { shots: GalleryShot[]; columns?: number }) {
  const cls =
    columns === 4 ? "h-[152px] w-[152px]" : columns === 3 ? "h-[180px] w-[180px]" : "h-[140px] w-full";
  return (
    <ul className="m-0 list-none p-0 text-center">
      {shots.map((s, i) => (
        <li key={i} className={`group relative m-[4px_2px] inline-block overflow-hidden rounded-[2px] align-top ${cls}`}>
          <img
            src={asset(s.src)}
            alt={s.alt}
            className="absolute inset-0 m-auto h-full w-full object-cover transition-opacity duration-300 group-hover:opacity-60"
          />
          <span className="absolute bottom-0 left-0 block bg-black p-[4px] font-['Roboto_Condensed'] text-[0.8em] text-[#efefef]">
            {s.time}
          </span>
        </li>
      ))}
    </ul>
  );
}

export function Prose({ children }: { children: ReactNode }) {
  return <div className="mx-auto max-w-[900px] px-[10px] py-[20px] text-[16px] leading-[1.7] text-[#333]">{children}</div>;
}
