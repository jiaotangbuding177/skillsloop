import { Link } from "@/lib/router";
import { img, homeGallery } from "@/data/assets";
import { CircleArrowRight, Play } from "@/components/Icons";
import { SectionTitle } from "@/components/Bits";

const featured = {
  title: "Fighting infection and chronic pain with engineered cells",
  body: "Engineered cells could enable targeted therapies for infection and chronic pain that don't rely on broad medications, which may trigger new side effects or dangerous immune system reactions in some patients.",
  link: "Read more about this research",
};

const infographics = [
  { label: "18 schools and colleges — see the full list", to: "/schools-colleges/" },
  { label: "More than 260 degree programs", to: "/_404.html" },
  { label: "Corravale Research: $1.94 billion in research spending (FY2024)", to: "/_404.html" },
  { label: "95+ Top-Ranked Graduate Programs", to: "/_404.html" },
];

const news = [
  "Leadership transition update",
  "Sky survey completes planned 3D map of the cosmos, keeps exploring",
  "Corravale Minds podcast: Fake flavors and real cravings drive our addiction to processed foods",
  "Pregnancy-related deaths rose during the pandemic and remain high for many new mothers",
  "Regional identity is a personal choice, not always tied to family ancestry",
];

const inTheNews = [
  { source: "Northshore Public Radio", headline: "As floodwaters rise, aging dams near failure: State needs $1B in repairs" },
  { source: "Gaceta Sur (Spain)", headline: "How a breakout artist redefined global fame" },
  { source: "Riverside Post", headline: "Commentary: Line-drying clothes and the math of small climate wins" },
  { source: "The Daily", headline: "How one cereal maker shaped how the nation ate breakfast" },
];

const videos = [
  { title: "Meet the Incoming University President", img: img.video1, alt: "A welcome message from President-elect Marion Halcombe." },
  { title: "Harnessing Innovation to Renew the American Dream: The Corravale Task Force", img: img.video2, alt: "" },
  { title: "Relocating the Historic Founders", img: img.video3, alt: "Corravale University carefully relocated a piece of history, adding a new chapter to the legacy of alumnus Anders Holmquist." },
];

const events = [
  { month: "March", day: "17", title: "The Corravale Framework for Siting Renewable Energy: Policy, Practice, and Impact", location: "Arts and Architecture Hall", image: img.event },
  { month: "Mar", day: "12", title: "SNL: Saturday Night Laughs, a FREE Improv Comedy Show!" },
  { month: "Mar", day: "14", title: "From Lecture Halls to Language Models: Placing GenAI in Learning" },
  { month: "Apr", day: "17", title: "Corravale Careers: A Workshop Series for Life After Graduation" },
  { month: "Apr", day: "17", title: "Green Market: Spring Seedling" },
];

const calendar = [
  { date: "Apr 21", label: "Classes end" },
  { date: "Apr 22, 25-26", label: "Study days" },
  { date: "Apr 23-30", label: "Examinations" },
  { date: "May 1-3", label: "Commencement Activities" },
];

export function HomePage() {
  return (
    <>
      <h1 className="sr-only">Corravale University</h1>

      {/* Hero */}
      <section aria-label="Featured Stories" className="relative">
        <div className="relative">
          <img src={img.hero} alt="" className="h-[560px] w-full object-cover md:h-[640px]" />
          <div className="absolute inset-0 bg-gradient-to-r from-[#0b1b2b]/70 via-[#0b1b2b]/25 to-transparent" />
          <h2 className="sr-only">Featured Stories</h2>
          <div className="absolute bottom-0 left-0 max-w-[620px] px-6 pb-40 md:px-16 md:pb-44">
            <h2 className="mb-3 font-cond text-[32px] leading-[1.05] font-bold tracking-[0.02em] text-white uppercase md:text-[48px]">
              {featured.title}
            </h2>
            <p className="mb-3 max-w-[480px] text-[14px] leading-relaxed text-white/85">
              {featured.body}
            </p>
            <Link
              to="/_404.html"
              className="inline-flex items-center gap-2 font-cond text-[14px] tracking-[0.04em] text-white underline decoration-maize decoration-2 underline-offset-4 hover:text-maize"
            >
              {featured.link}
              <CircleArrowRight size={14} className="text-maize" />
            </Link>
          </div>
        </div>
        <div className="relative mx-auto -mt-28 max-w-[1180px] px-5">
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {infographics.map((item) => (
              <li key={item.label}>
                <Link
                  to={item.to}
                  className="flex h-full min-h-[140px] flex-col items-center justify-center gap-3 bg-navy px-4 py-6 text-center text-white hover:bg-navy-panel"
                >
                  <em className="font-cond text-[17px] leading-snug font-normal not-italic">{item.label}</em>
                  <CircleArrowRight size={16} className="text-maize" />
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* News */}
      <section aria-label="News" className="bg-band py-10">
        <SectionTitle>News</SectionTitle>
        <div className="mx-auto grid max-w-[1180px] gap-10 px-5 md:grid-cols-2">
          <div>
            <h3 className="mb-4 font-cond text-[22px] tracking-[0.1em] text-sky uppercase">News</h3>
            <ul className="mb-5">
              {news.map((n, i) => (
                <li key={n} className={i > 0 ? "border-t border-white/15" : ""}>
                  <Link
                    to="/_404.html"
                    className="block py-3 text-[15px] leading-snug text-maize hover:underline"
                  >
                    {n}
                  </Link>
                </li>
              ))}
            </ul>
            <div className="space-y-3">
              <h4>
                <Link to="/_404.html" className="flex items-center gap-2 font-cond text-[15px] tracking-[0.08em] text-sky uppercase hover:text-white">
                  Visit Corravale News <CircleArrowRight size={14} className="text-sky" />
                </Link>
              </h4>
              <h4>
                <Link to="/_404.html" className="flex items-center gap-2 font-cond text-[15px] tracking-[0.08em] text-sky uppercase hover:text-white">
                  Explore Key Issues <CircleArrowRight size={14} className="text-sky" />
                </Link>
              </h4>
              <h4>
                <Link to="/_404.html" className="flex items-center gap-2 font-cond text-[15px] tracking-[0.08em] text-sky uppercase hover:text-white">
                  Visit the Campus Chronicle <CircleArrowRight size={14} className="text-sky" />
                </Link>
              </h4>
            </div>
          </div>
          <div>
            <h3 className="mb-4 font-cond text-[22px] tracking-[0.1em] text-sky uppercase">In The News</h3>
            <ul className="mb-5">
              {inTheNews.map((item, i) => (
                <li key={item.headline} className={i > 0 ? "border-t border-white/15" : ""}>
                  <Link to="/_404.html" className="block py-3 hover:underline">
                    <span className="block text-[13px] text-white/70">{item.source}</span>
                    <span className="block text-[15px] leading-snug text-maize">{item.headline}</span>
                  </Link>
                </li>
              ))}
            </ul>
            <h4>
              <Link to="/_404.html" className="flex items-center gap-2 font-cond text-[15px] tracking-[0.08em] text-sky uppercase hover:text-white">
                See more In The News <CircleArrowRight size={14} className="text-sky" />
              </Link>
            </h4>
          </div>
        </div>
      </section>

      {/* Videos */}
      <section aria-label="Videos" className="bg-maize py-10">
        <SectionTitle variant="dark">Videos</SectionTitle>
        <ul className="mx-auto grid max-w-[1180px] gap-6 px-5 md:grid-cols-3">
          {videos.map((v) => (
            <li key={v.title}>
              <Link to="/_404.html" className="group block">
                <h3 className="mb-3 min-h-[48px] font-cond text-[16px] leading-snug font-normal tracking-[0.02em] text-[#0b1b2b] uppercase">
                  {v.title}
                </h3>
                <span className="relative block">
                  <img src={v.img} alt={v.alt} className="h-[190px] w-full object-cover" loading="lazy" />
                  <span className="absolute inset-0 grid place-items-center">
                    <span className="grid h-[54px] w-[54px] place-items-center rounded-full border-2 border-white/90 text-white">
                      <Play size={18} />
                    </span>
                  </span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
        <p className="mx-auto mt-6 flex max-w-[1180px] justify-end px-5">
          <Link to="/_404.html" className="flex items-center gap-2 font-cond text-[15px] tracking-[0.08em] text-[#0b1b2b] uppercase hover:underline">
            Watch More Clips <CircleArrowRight size={15} />
          </Link>
        </p>
      </section>

      {/* Happening */}
      <section aria-label="Happening @ Corravale" className="bg-navy py-10">
        <SectionTitle>Happening @ Corravale</SectionTitle>
        <div className="mx-auto grid max-w-[1180px] gap-8 px-5 lg:grid-cols-[1fr_340px]">
          <div>
            <h3 className="mb-4 font-cond text-[20px] tracking-[0.1em] text-sky uppercase">Events</h3>
            <ul className="space-y-3">
              {events.map((e, i) => (
                <li key={e.title}>
                  <Link
                    to="/_404.html"
                    className={
                      i === 0
                        ? "grid grid-cols-[120px_auto_1fr] items-center gap-4"
                        : "grid grid-cols-[52px_1fr] items-center gap-4 border-b border-white/15 pb-3"
                    }
                  >
                    {i === 0 ? (
                      <>
                        <img src={e.image} alt="" className="h-[80px] w-[120px] object-cover" />
                        <span className="flex h-[72px] w-[64px] flex-col items-center justify-center bg-maize text-[#0b1b2b]">
                          <span className="font-cond text-[13px] tracking-[0.06em] uppercase">{e.month}</span>
                          <span className="font-cond text-[30px] leading-none font-bold">{e.day}</span>
                        </span>
                        <span>
                          <span className="block font-cond text-[16px] leading-snug font-bold text-white uppercase">{e.title}</span>
                          <span className="block text-[13px] text-white/70">{e.location}</span>
                        </span>
                      </>
                    ) : (
                      <>
                        <span className="flex items-center gap-1 font-cond text-[13px] text-maize uppercase">
                          {e.month}
                          <span className="font-bold">{e.day}</span>
                        </span>
                        <span className="text-[14px] leading-snug text-white/90">{e.title}</span>
                      </>
                    )}
                  </Link>
                </li>
              ))}
            </ul>
            <h4 className="mt-5">
              <Link to="/_404.html" className="flex items-center gap-2 font-cond text-[15px] tracking-[0.08em] text-sky uppercase hover:text-white">
                See What's On @ Corravale <CircleArrowRight size={14} className="text-sky" />
              </Link>
            </h4>
          </div>
          <div className="bg-[#2c2c2c] p-5">
            <h3 className="mb-4 font-cond text-[20px] tracking-[0.1em] text-sky uppercase">Academic Calendar</h3>
            <ul className="space-y-3">
              {calendar.map((c) => (
                <li key={c.label} className="border-b border-white/15 pb-3 text-white/90">
                  <span className="block font-cond text-[15px] text-white">{c.date}</span>
                  <span className="text-[14px]">{c.label}</span>
                </li>
              ))}
            </ul>
            <h4 className="mt-5">
              <Link to="/_404.html" className="flex items-center gap-2 font-cond text-[15px] tracking-[0.08em] text-sky uppercase hover:text-white">
                See the Full Calendar <CircleArrowRight size={14} className="text-sky" />
              </Link>
            </h4>
          </div>
        </div>
      </section>

      {/* Seize Today */}
      <section aria-label="Seize Today" className="bg-white py-10">
        <SectionTitle variant="dark">Seize Today</SectionTitle>
        <div className="mx-auto max-w-[1180px] px-5">
          <div className="mb-8 grid items-center gap-6 md:grid-cols-[220px_1fr]">
            <div className="flex items-center gap-6">
              <img src={img.blockm} alt="Block C" className="h-[96px] w-[96px] object-contain" />
              <img src={img.hours24} alt="24 Hours" className="h-[96px] w-[96px] object-contain" />
            </div>
            <div>
              <h3 className="mb-3 font-cond text-[22px] tracking-[0.08em] text-navy uppercase">
                All Corravale, all the time
              </h3>
              <p className="text-[14px] leading-relaxed text-[#333]">
                There's always something remarkable unfolding at Corravale. Whether it's here on campus or
                somewhere across the globe, our students, faculty, staff and alumni are out seizing the
                moment. A selection of images gathered over the years is featured in the gallery below.
              </p>
            </div>
          </div>
          <ul className="grid grid-cols-2 gap-[3px] md:grid-cols-4 lg:grid-cols-6">
            {homeGallery.map((g) => (
              <li key={g.time + g.src} className="group relative cursor-pointer overflow-hidden">
                <img src={g.src} alt={g.alt} className="h-[150px] w-full object-cover transition group-hover:scale-105" loading="lazy" />
                <span className="absolute bottom-0 left-0 bg-[#0b1b2b]/75 px-2 py-1 font-cond text-[12px] text-white">
                  {g.time}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </>
  );
}
