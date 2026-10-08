import { Link } from "@/lib/router";
import NavBlock, { type ContentBlock } from "@/components/NavBlock";
import { ArrowCircleRight } from "@/components/Icons";
import pages from "@/data/pages.json";
import contactRows from "@/data/contact.json";

type ContactData = {
  title: string;
  description: string;
  blocks: ContentBlock[];
  secondaryBlocks: ContentBlock[];
};

const data = (pages as unknown as Record<string, ContactData>).contact;
const rows = contactRows as string[][];

export default function Contact() {
  const secondary = data.secondaryBlocks?.[0];
  return (
    <div className="panel panel-grey content clear">
      <div className="panel-header">
        <h2>{data.title}</h2>
      </div>
      <div className="wrap panel-content">
        <div className="panel-description" style={{ textAlign: "left", padding: "0 10px 40px" }}>
          <p>{data.description}</p>
        </div>
        <div className="panel-body">
          <div className="primary">
            <nav className="nav-block" aria-label="Most Frequently Reached Campus">
              <div>
                <h3>Most Frequently Reached Campus</h3>
                <ul className="contact-table">
                  {rows.map((row, i) => (
                    <li key={i}>
                      <dl>
                        <dt>Department</dt>
                        <dd>
                          <Link to="/_404.html" onClick={(e) => e.preventDefault()}>
                            {row[0]}
                          </Link>
                        </dd>
                        {row.slice(1).map((v, j) => (
                          <dd key={j}>{v}</dd>
                        ))}
                      </dl>
                    </li>
                  ))}
                </ul>
              </div>
            </nav>
          </div>
          {secondary ? (
            <div className="secondary">
              <nav className="nav-block" aria-label={secondary.title}>
                <div>
                  <h3>{secondary.title}</h3>
                  <ul>
                    {secondary.items.map((it, i) =>
                      it.k === "a" ? (
                        <li className="has-arrow" key={i}>
                          <Link
                            to={it.href}
                            onClick={(e) => it.href === "/_404.html" && e.preventDefault()}
                          >
                            {it.label}
                            <span className="arrow">
                              <ArrowCircleRight size={13} />
                            </span>
                          </Link>
                        </li>
                      ) : null,
                    )}
                  </ul>
                  {(secondary.extraTitles ?? []).map((t, i) => (
                    <h3 key={i}>{t}</h3>
                  ))}
                  {(secondary.paras ?? []).map((p, i) => (
                    <p key={i}>{p}</p>
                  ))}
                </div>
              </nav>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
