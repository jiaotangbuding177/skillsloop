import privacy from "@/data/privacy.json";

type Node = { t: string; v: string };
const nodes = privacy as Node[];

export default function Privacy() {
  return (
    <div className="panel panel-light content clear">
      <div className="panel-header">
        <h2>Corravale Privacy Notice</h2>
      </div>
      <div className="privacy-body">
        {nodes.map((n, i) => {
          if (n.t === "h4" || n.t === "h3" || n.t === "h2") {
            return <h3 key={i}>{n.v}</h3>;
          }
          if (n.t === "li") {
            return (
              <ul key={i} style={{ margin: "0 0 12px 0" }}>
                <li>{n.v}</li>
              </ul>
            );
          }
          return <p key={i}>{n.v}</p>;
        })}
      </div>
    </div>
  );
}
