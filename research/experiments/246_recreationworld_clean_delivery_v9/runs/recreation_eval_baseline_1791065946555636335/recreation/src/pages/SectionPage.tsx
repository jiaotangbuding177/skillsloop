import { Link } from "@/router";
import { navGroups } from "@/data/navGroups";
import { FeatureBanner, GalleryStrip, SectionHeading } from "@/components/SectionBits";
import { ChevronCircle } from "@/components/Icons";
import { studentGallery } from "@/data/site";
import { asset } from "@/assets";

export interface SectionConfig {
  path: string;
  heading: string;
  intro: string;
  sideImage: string;
  sideCaption: string;
  featureImage: string;
  featureAlt: string;
  featureCaption: string;
  tone?: "dark" | "light";
  gallery?: "seize" | "student";
  galleryTitle?: string;
  galleryCopy?: string;
}

function NavBlockPanel({ title, items }: { title: string; items: { label: string; to: string; note?: string }[] }) {
  return (
    <div className="h-full min-h-[275px] rounded-[2px] border border-[#4b4b4b] bg-[#222222] p-[15px]">
      <h4 className="m-0 pb-[15px] text-[16px] font-bold uppercase text-[#72b4ff]">{title}</h4>
      <ul className="m-0 list-none p-0">
        {items.map((it, i) => (
          <li key={it.label + i} className={`relative py-[10px] ${i > 0 ? "border-t border-dotted border-[#8e8c8c]" : ""}`}>
            <Link
              to={it.to}
              className="cu-panel-link relative block pr-[25px] leading-[1.2em] tracking-[0.5px] text-white no-underline"
            >
              <span>{it.label}</span>
              {it.note ? <em className="block pt-[3px] text-[12px] italic leading-[1em] text-gray-300">{it.note}</em> : null}
              <ChevronCircle className="absolute right-0 top-0 text-[#ffcb0b]" />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function SectionPage({ config }: { config: SectionConfig }) {
  const groups = navGroups[config.path] ?? [];
  const gallery = config.gallery ? studentGallery : null;

  return (
    <>
      <section className="bg-[#333333] pb-[30px]">
        <div className="mx-auto max-w-[1200px] px-[10px]">
          <SectionHeading title={config.heading} tone={config.tone} />
          <p className="mx-auto max-w-[1000px] px-[10px] text-center text-[14px] leading-[1.5] text-[#cfcfcf]">{config.intro}</p>
          <div className="mt-[20px] flex flex-wrap gap-[10px]">
            <div className="grid w-full grid-cols-1 items-stretch gap-[10px] sm:grid-cols-2 lg:w-4/5 lg:grid-cols-3">
              {groups.map((g) => (
                <NavBlockPanel key={g.title} title={g.title} items={g.items} />
              ))}
            </div>
            <aside className="w-full lg:w-[19%]">
              <img src={asset(config.sideImage)} alt={config.featureAlt} className="block w-full" />
              <p className="mt-[6px] text-[14px] italic leading-[1.4] text-[#cfcfcf]">{config.sideCaption}</p>
            </aside>
          </div>
        </div>
      </section>

      <FeatureBanner src={config.featureImage} alt={config.featureAlt} caption={config.featureCaption} />

      {gallery ? (
        <section className="bg-white pb-[40px]">
          <div className="mx-auto max-w-[960px] px-[10px]">
            <h3 className="pb-[10px] pt-[26px] text-center font-['Roboto_Condensed'] text-[26px] font-normal uppercase tracking-[2px] text-[#4B4B4B]">
              {config.galleryTitle}
            </h3>
            <p className="mb-[20px] text-center font-['Roboto_Condensed'] text-[#757575]">{config.galleryCopy}</p>
            <GalleryStrip shots={gallery} columns={4} />
          </div>
        </section>
      ) : null}
    </>
  );
}
