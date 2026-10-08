import { useEffect, useState } from "react";
import { Link } from "@/router";
import {
  academicCalendar,
  homeEvents,
  homeNews,
  homeNewsLinks,
  inTheNews,
  videos,
  seizeToday,
} from "@/data/site";
import { ChevronCircle, PlayCircle } from "@/components/Icons";
import { asset } from "@/assets";
import infoOne from "@/assets/img/tile1.png";
import infoTwo from "@/assets/img/tile2.png";
import infoThree from "@/assets/img/tile3.png";
import infoFour from "@/assets/img/tile4.png";

const heroSlides = [
  {
    title: "Fighting infection and chronic pain with engineered cells",
    body:
      "Engineered cells could enable targeted therapies for infection and chronic pain that don't rely on broad medications, which may trigger new side effects or dangerous immune system reactions in some patients.",
    cta: "Read more about this research",
    to: "/_404.html",
    image: "/_images/b61e6a7c84cebdf5.jpg",
    align: "left" as const,
  },
  {
    title: "Rise Up, Corravale!",
    body: "Congratulations to the Corravale Women's Soccer team on capturing the National Championship! Go Ridgebacks!",
    cta: "Learn more",
    to: "/_404.html",
    image: "/_images/2571249505b54163.jpg",
    align: "right" as const,
  },
  {
    title: "Finding Rhythm in Stillness and Light",
    body:
      "The Corravale Residential College inspires a new generation of artists to find motion in metal and to hear music where there is only silence.",
    cta: "View the story",
    to: "/_404.html",
    image: "/_images/894a51cea9f9c6ec.jpg",
    align: "left" as const,
  },
  {
    title: "Ancient grassland runners were engineered for speed",
    body:
      "A Corravale study examining the fossilized ankle bones of an ancient grazing mammal has revealed that the animal was already evolving toward greater speed more than 6 million years before its fastest descendant.",
    cta: "Read more about this study",
    to: "/_404.html",
    image: "/_images/8d42f4956c45449e.jpg",
    align: "left" as const,
  },
];

const infographics = [
  {
    label: "18 schools and colleges — see the full list",
    span: "see the full list",
    to: "/schools-colleges/",
    image: infoOne,
  },
  { label: "More than 260 degree programs", to: "/_404.html", image: infoTwo },
  { label: "Corravale Research: $1.94 billion in research spending (FY2024)", to: "/_404.html", image: infoThree },
  { label: "95+ Top-Ranked Graduate Programs", to: "/_404.html", image: infoFour },
];

function PanelHeader({ id, title, tone }: { id?: string; title: string; tone: "dark" | "maize" | "light" }) {
  const color =
    tone === "maize" ? "text-[#636363] border-[#636363]" : tone === "light" ? "text-[#6189b7] border-[#6189b7]" : "text-white border-white/70";
  return (
    <div className="px-[10px] py-[20px] text-center text-[30px] uppercase tracking-[5px]">
      <h2 id={id} className={`m-0 border-b pb-[10px] font-['Roboto_Condensed'] text-[30px] font-normal ${color}`}>
        {title}
      </h2>
    </div>
  );
}

export function HomePage() {
  const [slide, setSlide] = useState(0);
  const active = heroSlides[slide];

  useEffect(() => {
    const t = window.setInterval(() => setSlide((s) => (s + 1) % heroSlides.length), 7000);
    return () => window.clearInterval(t);
  }, []);

  return (
    <>
      {/* Hero / featured stories */}
      <section id="features" className="relative overflow-hidden bg-[#333]" aria-label="Featured Stories">
        <h2 className="hidden-label">Featured Stories</h2>
        <div className="relative h-[780px] overflow-hidden lg:h-[900px]">
          {heroSlides.map((s, i) => (
            <div
              key={s.title}
              className={`absolute inset-0 transition-opacity duration-700 ${i === slide ? "opacity-100" : "opacity-0"}`}
              aria-hidden={i !== slide}
            >
              <div className="absolute inset-0 bg-cover bg-top bg-no-repeat" style={{ backgroundImage: `url(${asset(s.image)})` }} />
            </div>
          ))}
          <div className="relative z-10 mx-auto max-w-[1200px] px-[10px] pt-[200px]">
            <div
              className={`w-full max-w-[440px] rounded-[2px] bg-[rgba(51,51,51,.79)] p-[20px] font-['Roboto_Condensed'] text-white ${
                active.align === "right" ? "ml-auto" : ""
              }`}
            >
              <h2 className="border-b-0 pb-[10px] text-[30px] font-normal uppercase leading-[1.05] tracking-[5px]">{active.title}</h2>
              <p className="m-0 text-[15px] leading-[22px] tracking-[0.5px]">{active.body}</p>
              <p className="mt-[6px]">
                <Link
                  to={active.to}
                  className="inline-block border-b border-dotted border-transparent text-white no-underline hover:border-[#ffcb0b] hover:text-[#ffcb0b]"
                >
                  <span>{active.cta}</span>
                  <ChevronCircle className="ml-[8px] inline" />
                </Link>
              </p>
            </div>
          </div>
          <button
            type="button"
            aria-label="Previous story"
            onClick={() => setSlide((s) => (s - 1 + heroSlides.length) % heroSlides.length)}
            className="absolute left-[10px] top-1/2 z-20 hidden h-[46px] w-[46px] -translate-y-1/2 rounded-full border-[3px] border-white bg-[rgba(51,51,51,.3)] text-[30px] leading-[36px] text-white opacity-70 hover:opacity-100 lg:block"
          >
            ‹
          </button>
          <button
            type="button"
            aria-label="Next story"
            onClick={() => setSlide((s) => (s + 1) % heroSlides.length)}
            className="absolute right-[10px] top-1/2 z-20 hidden h-[46px] w-[46px] -translate-y-1/2 rounded-full border-[3px] border-white bg-[rgba(51,51,51,.3)] text-[30px] leading-[36px] text-white opacity-70 hover:opacity-100 lg:block"
          >
            ›
          </button>
        </div>

        <ul className="relative z-20 mx-auto -mt-[150px] mb-[45px] max-w-[1200px] list-none px-[10px] text-center lg:-mt-[300px]">
          {infographics.map((c, i) => (
            <li key={c.label} className="mb-[10px] inline-block align-top lg:mx-[8px]">
              <Link
                to={c.to}
                className="group relative float-left flex h-[231px] w-[200px] flex-col justify-end overflow-hidden rounded-[2px] p-0 text-white no-underline"
                style={{ backgroundImage: `url(${asset(c.image)})`, backgroundSize: "100% 100%" }}
              >
                <span className="relative z-[2] block bg-[#073262] px-[15px] py-[6px] font-[Roboto] text-[14px] leading-[18px] group-hover:bg-black">
                  {c.span ?? c.label}
                </span>
                <span className="hidden-label">{c.label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {/* News */}
      <section id="news" className="bg-[#333] text-[#a1a1a1]" role="region" aria-label="News">
        <PanelHeader id="news-label" title="News" tone="dark" />
        <div className="mx-auto flex max-w-[1200px] flex-wrap px-[10px] pb-[25px]">
          <div className="w-full px-[20px] lg:w-1/2 lg:border-r lg:border-[#555]">
            <h3 className="pb-[10px] text-[24px] font-normal uppercase tracking-[2px] text-[#72b4ff]">News</h3>
            <ul className="m-0 list-none p-0">
              {homeNews.map((n, i) => (
                <li
                  key={n.label}
                  className={`py-[10px] font-[Roboto] text-[16px] leading-[22px] ${i > 0 ? "border-t border-dotted border-[#8e8c8c]" : ""}`}
                >
                  <Link to={n.to} className="block text-[#ffcb0b] no-underline hover:[&>span]:border-b hover:[&>span]:border-dotted hover:[&>span]:border-[#ffcb0b]">
                    <span>{n.label}</span>
                  </Link>
                </li>
              ))}
            </ul>
            {homeNewsLinks.map((l) => (
              <h4 key={l.label} className="py-[10px] text-[15px] font-bold uppercase tracking-[1px]">
                <Link to={l.to} className="inline-block text-[#85beff] no-underline hover:[&>span]:border-b hover:[&>span]:border-dotted">
                  <span>
                    {l.label} <ChevronCircle className="ml-[10px] inline text-[#ffcb0b]" />
                  </span>
                </Link>
              </h4>
            ))}
          </div>
          <div className="w-full px-[20px] lg:w-1/2">
            <h3 className="pb-[10px] text-[24px] font-normal uppercase tracking-[2px] text-[#72b4ff]">In The News</h3>
            <ul className="m-0 list-none p-0">
              {inTheNews.map((n, i) => (
                <li
                  key={n.label}
                  className={`py-[10px] font-[Roboto] text-[16px] leading-[22px] ${i > 0 ? "border-t border-dotted border-[#8e8c8c]" : ""}`}
                >
                  <Link to={n.to} className="block text-[#ffcb0b] no-underline hover:[&>span]:border-b hover:[&>span]:border-dotted hover:[&>span]:border-[#ffcb0b]">
                    <span className="block text-[#ddd]">
                      {n.source}
                      <span className="mt-[4px] block text-[#ffcb0b]">{n.label}</span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
            <h4 className="py-[10px] text-[15px] font-bold uppercase tracking-[1px]">
              <Link to="/_404.html" className="inline-block text-[#85beff] no-underline hover:[&>span]:border-b hover:[&>span]:border-dotted">
                <span>
                  See more In The News <ChevronCircle className="ml-[10px] inline text-[#ffcb0b]" />
                </span>
              </Link>
            </h4>
          </div>
        </div>
      </section>

      {/* Videos */}
      <section id="videos" className="bg-[#ffcb0b] text-[#333]" role="region" aria-label="Videos">
        <PanelHeader id="videos-label" title="Videos" tone="maize" />
        <div className="mx-auto max-w-[1200px] px-[10px] pb-[10px]">
          <ul className="m-0 list-none p-0">
            {videos.map((v) => (
              <li key={v.title} className="mb-[10px] block w-full p-[20px] align-top lg:mb-0 lg:inline-block lg:w-1/3">
                <Link to={v.to} className="block text-inherit no-underline">
                  <h3 className="pb-[10px] text-center text-[18px] uppercase leading-[1.2] tracking-[1px]">{v.title}</h3>
                  <span className="group relative block rounded-[3px] bg-[#333]">
                    <img src={asset(v.image)} alt={v.alt} className="block w-full rounded-[2px] transition-all duration-200 group-hover:opacity-80" />
                    <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-[50px] text-white opacity-60 transition-all duration-200 group-hover:opacity-100">
                      <PlayCircle />
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
          <p className="px-[20px] text-right">
            <Link
              to="/_404.html"
              className="uppercase text-[#333333] no-underline hover:[&>span]:border-b hover:[&>span]:border-dotted hover:[&>span]:border-[#333333]"
            >
              <span>
                Watch More Clips <ChevronCircle className="ml-[8px] inline" />
              </span>
            </Link>
          </p>
        </div>
      </section>

      {/* Happening @ Corravale */}
      <section id="events" className="bg-[#00274c] text-[#a1a1a1]" role="region" aria-label="Happening @ Corravale">
        <PanelHeader id="events-label" title="Happening @ Corravale" tone="dark" />
        <div className="mx-auto flex max-w-[1200px] flex-wrap px-[10px] pb-[25px]">
          <div className="w-full px-[20px] lg:w-2/3">
            <h3 className="pb-[10px] text-[24px] font-normal uppercase tracking-[2px] text-[#72b4ff]">Events</h3>
            <ul className="m-0 list-none p-0">
              {homeEvents.map((e, i) => (
                <li
                  key={e.title}
                  className={`text-[16px] leading-[20px] ${
                    i === 0 ? "block w-full pt-0 lg:float-left lg:w-1/2 lg:pr-[20px]" : "block w-full py-[10px] lg:float-right lg:w-1/2 lg:clear-right"
                  } ${i > 1 ? "border-t border-dotted border-[#8e8c8c]" : ""}`}
                >
                  <Link to={e.to} className="block text-[#ffcb0b] no-underline hover:[&_.ev-title]:underline">
                    {e.image ? (
                      <span className="mb-[15px] block text-center">
                        <img src={asset(e.image)} alt={e.alt} className="max-w-full rounded-[2px]" />
                      </span>
                    ) : null}
                    <span className="flex items-start">
                      <span className="float-left m-0 w-[70px] rounded-[2px] bg-[#4a4a4a] px-[8px] py-[4px] text-center font-['Roboto_Condensed'] font-bold uppercase tracking-[1px] text-white">
                        {e.month}
                        <span className="block text-[35px] leading-[35px]">{e.day}</span>
                      </span>
                      <span className="ml-[80px] flex-1">
                        <span className={`ev-title block uppercase ${i === 0 ? "text-[20px]" : "text-[16px]"}`}>{e.title}</span>
                        {e.location ? <span className="block uppercase text-white">{e.location}</span> : null}
                      </span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
            <h4 className="clear-right py-[10px] text-right text-[16px] font-bold uppercase tracking-[1px]">
              <Link to="/_404.html" className="inline-block text-[#85beff] no-underline hover:[&>span]:border-b hover:[&>span]:border-dotted">
                <span>
                  See What's On @ Corravale <ChevronCircle className="ml-[10px] inline text-[#ffcb0b]" />
                </span>
              </Link>
            </h4>
          </div>
          <div className="w-full px-[20px] pt-[10px] lg:w-1/3">
            <div className="rounded-[2px] border border-[#656565] bg-[#4a4a4a] p-[15px]">
              <h3 className="pb-[10px] text-[24px] font-normal uppercase tracking-[2px] text-[#72b4ff]">Academic Calendar</h3>
              <ul className="m-0 list-none p-0 text-white">
                {academicCalendar.map((c, i) => (
                  <li key={c.dates} className={`py-[10px] ${i > 0 ? "border-t border-dotted border-[#8e8c8c]" : ""}`}>
                    <ul className="m-0 list-none p-0">
                      <li>{c.dates}</li>
                    </ul>
                    {c.label}
                  </li>
                ))}
              </ul>
            </div>
            <h4 className="py-[10px] text-[16px] font-bold uppercase tracking-[1px]">
              <Link to="/_404.html" className="inline-block text-[#85beff] no-underline hover:[&>span]:border-b hover:[&>span]:border-dotted">
                <span>
                  See the Full Calendar <ChevronCircle className="ml-[10px] inline text-[#ffcb0b]" />
                </span>
              </Link>
            </h4>
          </div>
        </div>
      </section>

      {/* Seize Today */}
      <section id="gallery" className="bg-white pb-[40px]" role="region" aria-label="Seize Today">
        <div className="mx-auto max-w-[1200px] px-[10px]">
          <PanelHeader id="gallery-label" title="Seize Today" tone="light" />
          <div className="my-[1%] flex flex-wrap items-start">
            <div className="w-full lg:w-1/2">
              <div className="flex items-center border-r-0 border-[#a1a1a1] px-[6%] lg:border-r lg:pr-[6%]">
                <img src={asset("/includes/panels/gallery/images/block-m-maize.png")} alt="Block C" className="h-[200px] w-auto max-w-[202px]" />
              </div>
            </div>
            <div className="w-full lg:w-1/2">
              <div className="flex items-center justify-center px-[6%]">
                <img src={asset("/includes/panels/gallery/images/24-hours.png")} alt="24 Hours" className="h-[200px] w-auto max-w-[202px]" />
              </div>
            </div>
          </div>
          <div className="mx-auto max-w-[960px]">
            <div className="my-[1%] mb-[3%] text-[18px] leading-[24px] tracking-[1px]">
              <h3 className="pb-[10px] text-[26px] font-normal uppercase tracking-[2px] text-[#4B4B4B]">All Corravale, all the time</h3>
              <p className="font-['Roboto_Condensed'] text-[#757575]">
                There's always something remarkable unfolding at Corravale. Whether it's here on campus or somewhere across the globe, our
                students, faculty, staff and alumni are out seizing the moment. A selection of images gathered over the years is featured in
                the gallery below.
              </p>
            </div>
            <ul className="m-0 list-none p-0 text-center">
              {seizeToday.map((s, i) => (
                <li
                  key={i}
                  className="group relative m-[4px_2px] inline-block h-[152px] w-[152px] overflow-hidden rounded-[2px] align-top"
                >
                  <img
                    src={asset(s.src)}
                    alt={s.alt}
                    className="absolute inset-0 m-auto h-full min-h-full w-full min-w-full max-w-none object-cover group-hover:opacity-60"
                  />
                  <span className="absolute bottom-0 left-0 block bg-black p-[4px] font-['Roboto_Condensed'] text-[0.8em] text-[#efefef]">
                    {s.time}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </>
  );
}
