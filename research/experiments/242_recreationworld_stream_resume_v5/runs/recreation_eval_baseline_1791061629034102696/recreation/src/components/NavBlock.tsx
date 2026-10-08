import { Link } from "@/lib/router";
import { ArrowCircleRight } from "@/components/Icons";

export type BlockItem =
  | { k: "a"; href: string; label: string }
  | { k: "d"; label: string; children: string[] };

export type ContentBlock = {
  title: string;
  extraTitles?: string[];
  items: BlockItem[];
  paras?: string[];
};

/** Renders one nav block panel (the dark card grid used across content pages). */
export default function NavBlock({
  block,
  className,
}: {
  block: ContentBlock;
  className?: string;
}) {
  const titles = [block.title, ...(block.extraTitles ?? [])].filter(Boolean);
  return (
    <nav className={"nav-block " + (className ?? "")} aria-label={block.title || undefined}>
      <div>
        {titles.map((t, i) => (
          <h3 key={i}>{t}</h3>
        ))}
        <ul>
          {block.items.map((item, i) => {
            if (item.k === "d") {
              return (
                <li className="has-arrow" key={i}>
                  <details>
                    <summary>{item.label}</summary>
                    <div className="dropdown-content">
                      <ul>
                        {item.children.map((c, j) => (
                          <li key={j}>
                            {c}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </details>
                </li>
              );
            }
            const external = item.href === "/_404.html";
            return (
              <li className="has-arrow" key={i}>
                <Link
                  to={item.href}
                  onClick={(e) => external && e.preventDefault()}
                >
                  {item.label}
                  <span className="arrow">
                    <ArrowCircleRight size={13} />
                  </span>
                </Link>
              </li>
            );
          })}
          {(block.paras ?? []).map((p, i) => (
            <li key={"p" + i}>
              <p>{p}</p>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
