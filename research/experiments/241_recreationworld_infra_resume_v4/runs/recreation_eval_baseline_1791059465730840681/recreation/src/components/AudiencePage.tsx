import { Link } from "@/lib/router";
import NavBlock, { type ContentBlock } from "@/components/NavBlock";
import { ChevronUp } from "@/components/Icons";
import { media } from "@/lib/assets";

export type AudiencePageData = {
  route: string;
  title: string;
  description: string;
  color: string;
  blocks: ContentBlock[];
  secondaryBlocks?: ContentBlock[];
  featureImg: string;
  caption: string;
  captionLink: { href: string; label: string } | null;
  sharingImg: string;
  sharingCaption: string;
};

export default function AudiencePage({ data }: { data: AudiencePageData }) {
  return (
    <>
      <div className={"panel panel-" + (data.color || "grey") + " audience clear"}>
        <div className="panel-header">
          <h2>{data.title}</h2>
        </div>
        <div className="wrap panel-content">
          {data.description ? (
            <div className="panel-description">
              <p>{data.description}</p>
            </div>
          ) : null}
          <div className="panel-body">
            <div className="primary">
              {data.blocks.map((b, i) => (
                <NavBlock block={b} key={i} />
              ))}
            </div>
            {data.secondaryBlocks && data.secondaryBlocks.length > 0 ? (
              <div className="secondary">
                {data.secondaryBlocks.map((b, i) => (
                  <NavBlock block={b} key={i} />
                ))}
              </div>
            ) : data.featureImg ? (
              <div className="secondary">
                <div className="feature">
                  <img src={media(data.featureImg)} alt="" />
                  <p className="caption">
                    {data.caption}
                    {data.captionLink ? (
                      <span>
                        <Link to={data.captionLink.href}>
                          {data.captionLink.label}
                        </Link>
                      </span>
                    ) : null}
                  </p>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {data.sharingImg ? (
        <div className="sharing" role="region" aria-label="Voices of Our Campus">
          <img src={media(data.sharingImg)} alt="" />
          <div className="wrap">
            <div className="sharing-caption">
              <div className="inner">
                <ChevronUp size={16} />
                <p>{data.sharingCaption}</p>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
