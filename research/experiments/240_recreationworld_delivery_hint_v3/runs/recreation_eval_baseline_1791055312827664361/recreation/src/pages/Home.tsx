import { useMemo, useState } from "react";
import { Link } from "@/lib/router";
import home from "@/data/home.json";
import gallery from "@/data/gallery.json";
import {
  ArrowCircleRight,
  ChevronLeft,
  ChevronRight,
  PlayIcon,
} from "@/components/Icons";
import { media } from "@/lib/assets";

type Feature = {
  title: string;
  body: string;
  link: string;
  href: string;
  bg: string;
};

const features: Feature[] = home.features;
const infographics = home.infographics;
const newsLinks = home.news as [string, string][];

const NEWS_TITLES = newsLinks.slice(0, 5);
const IN_THE_NEWS = newsLinks.slice(5);

const VIDEOS = [
  {
    title: "Meet the Incoming University President",
    img: "/media/1edd5970e96fbddd.jpg",
    alt: "A welcome message from President-elect Marion Halcombe.",
  },
  {
    title:
      "Harnessing Innovation to Renew the American Dream: The Corravale Task Force",
    img: "/media/4ae7aa5aaab80c54.jpg",
    alt: "",
  },
  {
    title: "Relocating the Historic Founders",
    img: "/media/ebf5ca139005cbae.jpg",
    alt: "",
  },
];

const EVENTS = [
  {
    date: "March",
    day: "17",
    title:
      "The Corravale Framework for Siting Renewable Energy: Policy, Practice, and Impact",
    location: "Arts and Architecture Hall",
    img: "/media/2eb6869096259dcd.jpg",
  },
  {
    date: "Mar",
    day: "12",
    title: "SNL: Saturday Night Laughs, a FREE Improv Comedy Show!",
    location: "",
    img: "",
  },
  {
    date: "Mar",
    day: "14",
    title: "From Lecture Halls to Language Models: Placing GenAI in Learning",
    location: "",
    img: "",
  },
  {
    date: "Apr",
    day: "17",
    title: "Corravale Careers: A Workshop Series for Life After Graduation",
    location: "",
    img: "",
  },
  {
    date: "Apr",
    day: "17",
    title: "Green Market: Spring Seedling",
    location: "",
    img: "",
  },
];

const CALENDAR = [
  { date: "Apr 21", label: "Classes end" },
  { date: "Apr 22, 25-26", label: "Study days" },
  { date: "Apr 23-30", label: "Examinations" },
  { date: "May 1-3", label: "Commencement Activities" },
];

export default function Home() {
  const [active, setActive] = useState(1);
  const slideCount = features.length;

  const go = (delta: number) =>
    setActive((i) => (i + delta + slideCount) % slideCount);

  const current = features[active];
  const overlayStyle = useMemo(
    () => ({ backgroundImage: `url(${media(current.bg)})` }),
    [current.bg],
  );

  return (
    <>
      {/* Featured stories carousel */}
      <section className="hero" aria-label="Featured Stories" id="features">
        <div className="hero-slide current">
          <div className="hero-media" style={overlayStyle} />
          <div className="hero-overlay">
            <div className="wrap" style={{ width: "100%" }}>
              <div className="hero-copy">
                <h2>{current.title}</h2>
                <p>{current.body}</p>
                <p>
                  <Link to={current.href} onClick={(e) => e.preventDefault()}>
                    {current.link} <ArrowCircleRight size={14} />
                  </Link>
                </p>
              </div>
            </div>
          </div>
          <div className="hero-nav">
            <button type="button" aria-label="Previous story" onClick={() => go(-1)}>
              <ChevronLeft size={16} />
            </button>
            <button type="button" aria-label="Next story" onClick={() => go(1)}>
              <ChevronRight size={16} />
            </button>
          </div>
        </div>

        {/* Infographics */}
        <div className="infographics" role="region" aria-label="Infographics & Special Features">
          <div className="wrap">
            <ul>
              {infographics.map((info, i) => (
                <li key={i}>
                  <Link
                    to={info.href}
                    onClick={(e) => info.href === "/_404.html" && e.preventDefault()}
                  >
                    {info.hidden}
                    {info.span ? (
                      <span style={{ display: "block" }}>
                        {info.span} <ArrowCircleRight size={13} />
                      </span>
                    ) : null}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* News */}
      <section className="panel panel-grey clear" id="news" aria-label="News">
        <div className="panel-header">
          <h2>News</h2>
        </div>
        <div className="wrap">
          <div className="news-grid">
            <div className="news-col">
              <h3>News</h3>
              <ul className="news-list">
                {NEWS_TITLES.map(([title], i) => (
                  <li key={i}>
                    <Link to="/_404.html" onClick={(e) => e.preventDefault()}>
                      {title}
                    </Link>
                  </li>
                ))}
              </ul>
              <div className="panel-cta">
                <Link to="/_404.html" onClick={(e) => e.preventDefault()}>
                  Visit Corravale News <ArrowCircleRight size={14} />
                </Link>
                <Link to="/_404.html" onClick={(e) => e.preventDefault()}>
                  Explore Key Issues <ArrowCircleRight size={14} />
                </Link>
                <Link to="/_404.html" onClick={(e) => e.preventDefault()}>
                  Visit the Campus Chronicle <ArrowCircleRight size={14} />
                </Link>
              </div>
            </div>
            <div className="news-col">
              <h3>In The News</h3>
              <ul className="news-list">
                {IN_THE_NEWS.map(([title], i) => {
                  const split = title.match(/^(.*?(?:Radio|\(Spain\)|Post|Daily))\s(.*)$/);
                  return (
                    <li key={i}>
                      <Link to="/_404.html" onClick={(e) => e.preventDefault()}>
                        {split ? (
                          <>
                            <span className="news-source">{split[1]}</span>
                            {split[2]}
                          </>
                        ) : (
                          title
                        )}
                      </Link>
                    </li>
                  );
                })}
              </ul>
              <div className="panel-cta">
                <Link to="/_404.html" onClick={(e) => e.preventDefault()}>
                  See more In The News <ArrowCircleRight size={14} />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Videos */}
      <section className="panel panel-maize clear" id="videos" aria-label="Videos">
        <div className="panel-header">
          <h2>Videos</h2>
        </div>
        <div className="wrap">
          <div className="videos-grid">
            {VIDEOS.map((v, i) => (
              <Link
                to="/_404.html"
                className="video-card"
                key={i}
                onClick={(e) => e.preventDefault()}
              >
                <h3>{v.title}</h3>
                <div className="video-thumb">
                  <img src={media(v.img)} alt={v.alt} loading="lazy" />
                  <span className="play-badge">
                    <PlayIcon />
                  </span>
                </div>
              </Link>
            ))}
          </div>
          <p className="watch-more">
            <Link to="/_404.html" onClick={(e) => e.preventDefault()}>
              Watch More Clips <ArrowCircleRight size={14} />
            </Link>
          </p>
        </div>
      </section>

      {/* Happening @ Corravale */}
      <section className="panel panel-blue clear" id="events" aria-label="Happening @ Corravale">
        <div className="panel-header">
          <h2>Happening @ Corravale</h2>
        </div>
        <div className="wrap">
          <div className="events-wrap">
            <div className="events-col">
              <h3>Events</h3>
              <ul className="event-list">
                {EVENTS.map((ev, i) => (
                  <li key={i}>
                    <Link to="/_404.html" onClick={(e) => e.preventDefault()}>
                      {ev.img ? (
                        <span className="event-image">
                          <img src={media(ev.img)} alt="" loading="lazy" />
                        </span>
                      ) : null}
                      <span className="event-date">
                        {ev.day === "17" ? (
                          <>
                            {ev.date}
                            <span className="event-date-big">{ev.day}</span>
                          </>
                        ) : (
                          `${ev.date} ${ev.day}`
                        )}
                      </span>
                      <span className="event-title">
                        {ev.title}
                        {ev.location ? (
                          <span className="event-location">{ev.location}</span>
                        ) : null}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
              <div className="panel-cta">
                <Link to="/_404.html" onClick={(e) => e.preventDefault()}>
                  See What's On @ Corravale <ArrowCircleRight size={14} />
                </Link>
              </div>
            </div>
            <div className="calendar-col">
              <h3>Academic Calendar</h3>
              <ul className="calendar-list">
                {CALENDAR.map((c, i) => (
                  <li key={i}>
                    <span className="calendar-date">{c.date}</span>
                    <span>{c.label}</span>
                  </li>
                ))}
              </ul>
              <div className="panel-cta">
                <Link to="/_404.html" onClick={(e) => e.preventDefault()}>
                  See the Full Calendar <ArrowCircleRight size={14} />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Seize Today gallery */}
      <section className="panel panel-white clear active" id="gallery" aria-label="Seize Today">
        <div className="panel-header">
          <h2>Seize Today</h2>
        </div>
        <div className="wrap">
          <div className="seize">
            <div className="seize-intro">
              <div className="seize-badges">
                <img src={media("/media/block-m-maize.png")} alt="Block C" loading="lazy" />
                <img src={media("/media/24-hours.png")} alt="24 Hours" loading="lazy" />
              </div>
              <div>
                <h3>All Corravale, all the time</h3>
                <p>
                  There's always something remarkable unfolding at Corravale.
                  Whether it's here on campus or somewhere across the globe, our
                  students, faculty, staff and alumni are out seizing the moment.
                  A selection of images gathered over the years is featured in the
                  gallery below.
                </p>
              </div>
            </div>
          </div>
        </div>
        <ul className="gallery-grid">
          {gallery.map((g, i) => (
            <li key={i}>
              <img src={media(g.img)} alt={g.alt} loading="lazy" />
              <span className="time">{g.time}</span>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
