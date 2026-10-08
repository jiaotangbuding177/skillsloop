import { Link } from "@/router";
import { asset } from "@/assets";

const rankings = [
  { rank: "#1", title: "U.S. PUBLIC\nUNIVERSITY", source: "World's Top Universities\nGlobal Review (2026)" },
  { rank: "#3", title: "NATIONAL UNDERGRADUATE\nPUBLIC UNIVERSITIES", source: "ACADEMIC STANDARD REVIEW (2025)" },
  { rank: "#1", title: "BEST SMALL COLLEGE\nTOWNS IN AMERICA", source: "CAMPUSGRADE (2025)" },
  { rank: "#2", title: "U.S. PUBLIC\nUNIVERSITY", source: "GLOBAL CAMPUS INDEX\nRANKINGS (2025)" },
];

const factColumns: [string, string[]][] = [
  [
    "Research",
    [
      "#2 in research activity among public research universities",
      "$1.25B in annual federally funded research awards (2024)",
      "$2.16B in research expenditures (2025)",
    ],
  ],
  ["Innovation Partnerships", ["615 new inventions disclosed (2024)", "28 new venture startups founded"]],
  ["2023 Incoming Class", ["3.9-4.0 average high school GPA", "31–34 average ACT score", "1350-1530 average SAT range"]],
  ["Athletics", ["419 all-time league athletic championships", "900+ student-athletes", "27 Division I varsity teams"]],
  [
    "Academics",
    [
      "110 grad programs in the top 10 — National Education Digest (2022)",
      "97% first-year student retention rate",
      "93% of students graduate within six years",
      "19 schools and colleges",
      "280+ degree programs",
      "15:1 student to faculty ratio",
    ],
  ],
  [
    "Affordability",
    [
      "2 of 3 first-year students receive financial aid",
      "More than $754.6M in scholarships and fellowships awarded to students (2020-21)",
      "Value Quarterly ranks Corravale No. 1 for value (2022)",
    ],
  ],
];

const enrollment = [
  { label: "Undergraduate Enrollment", values: ["35,358", "6,199", "5,534"] },
  { label: "In-state", values: ["18,800", "5,673", "5,057"] },
  { label: "Out-of-state", values: ["16,558", "526", "477"] },
  { label: "Graduate Enrollment", values: ["18,130", "1,806", "1,585"] },
  { label: "Student organizations", values: ["1,600+", "180+", "100+"] },
];

const costs = [
  { label: "In-state", values: ["$18,346 **", "$15,840", "$14,106"] },
  { label: "Out-of-state", values: ["$63,962 **", "$33,768", "$26,928"] },
  { label: "Room + Board", values: ["$16,246 **", "N/A", "$13,420 (average)"] },
];

function RankStat({ rank, title, source }: { rank: string; title: string; source: string }) {
  return (
    <div className="flex items-start gap-[10px]">
      <span className="font-['Roboto_Condensed'] text-[64px] font-bold leading-[0.85] text-[#ffcb0b]">
        <span className="align-top text-[40px]">#</span>
        {rank.replace("#", "")}
      </span>
      <span className="border-b border-[#8a8a8a] pb-[6px]">
        <span className="block whitespace-pre-line text-[20px] uppercase leading-[1.15] text-white">{title}</span>
        <span className="mt-[4px] block whitespace-pre-line text-[13px] font-bold uppercase tracking-[1px] text-[#b9b9b9]">{source}</span>
      </span>
    </div>
  );
}

export function FactsFiguresPage() {
  return (
    <div className="bg-[#333333] pb-[60px] text-[#d8d8d8]">
      <div className="mx-auto max-w-[1200px] px-[10px]">
        <div className="text-center text-[30px] uppercase tracking-[5px]">
          <h2 className="m-0 border-b border-white/70 pb-[10px] font-['Roboto_Condensed'] text-[30px] font-normal text-white">
            Facts &amp; Figures
          </h2>
        </div>
        <p className="mx-auto max-w-[1000px] px-[10px] py-[16px] text-center text-[15px] leading-[1.5] text-[#c3c3c3]">
          More than any institution before us, Corravale holds the potential to become far greater than the sum of its many remarkable
          parts. It is precisely this potential to shape the communities we serve that stands as our most enduring value as a university.
          Below are a few facts and figures that begin to convey the scope and ambition of Corravale.
        </p>

        <div className="my-[30px] text-center">
          <h3 className="border-b border-dotted border-[#8a8a8a] pb-[10px] font-['Roboto_Condensed'] text-[22px] uppercase tracking-[3px] text-[#7ea2d6]">
            Fairhaven Campus
          </h3>
        </div>

        <div className="grid gap-[40px] px-[10px] sm:grid-cols-2">
          {rankings.map((r) => (
            <RankStat key={r.rank + r.title} {...r} />
          ))}
          <div className="sm:col-span-2 flex justify-center">
            <div className="max-w-[420px]">
              <RankStat
                rank="#23"
                title={"WORLD REPUTATION\nRANKINGS"}
                source={"MERIDIAN REVIEW (2025)"}
              />
            </div>
          </div>
        </div>

        <div className="mt-[40px] grid gap-[30px] px-[10px] sm:grid-cols-2">
          {factColumns.map(([title, items]) => (
            <div key={title}>
              <h4 className="pb-[8px] text-[22px] font-normal text-[#e6e6e6]">{title}</h4>
              <ul className="m-0 list-disc pl-[22px] text-[15px] leading-[1.8] text-[#c3c3c3]">
                {items.map((i) => (
                  <li key={i}>{i}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Corravale Promise */}
        <div className="my-[50px] text-center">
          <img
            src={asset("/media/images/facts-figures/gbg-banner-rev.png")}
            alt="Corravale Promise"
            className="mx-auto block max-w-full"
          />
          <div className="mx-auto mt-[10px] max-w-[900px]">
            <div className="flex flex-wrap items-start justify-center gap-x-[60px] gap-y-[16px]">
              <div>
                <p className="font-['Roboto_Condensed'] text-[24px] font-bold uppercase text-[#ffcb0b]">Free Tuition</p>
                <p className="text-[13px] uppercase tracking-[1px] text-[#c3c3c3]">For families with incomes $125,000 &amp; under</p>
                <p className="text-[13px] uppercase tracking-[1px] text-[#c3c3c3]">Assets below $125,000 (effective fall 2025)</p>
              </div>
              <div>
                <p className="font-['Roboto_Condensed'] text-[24px] font-bold uppercase text-[#ffcb0b]">Tuition Support</p>
                <p className="text-[13px] uppercase tracking-[1px] text-[#c3c3c3]">For some families earning more</p>
              </div>
            </div>
            <p className="mt-[16px] text-[13px] uppercase tracking-[2px] text-[#c3c3c3]">
              Four years free for qualifying state students
            </p>
            <p className="mt-[6px] text-[13px] uppercase tracking-[2px] text-[#c3c3c3]">Fairhaven, Westgate &amp; Alden campuses</p>
          </div>
        </div>

        <div className="my-[40px] flex items-center justify-center gap-[20px] text-center">
          <span className="font-['Roboto_Condensed'] text-[70px] font-bold leading-none text-[#ffcb0b]">1</span>
          <span className="text-left text-[16px] uppercase leading-[1.3] text-[#e6e6e6]">
            out of 4
            <span className="block text-[13px] text-[#c3c3c3]">In-state undergraduates pay no tuition thanks to financial aid</span>
          </span>
        </div>

        <div className="my-[40px] text-center">
          <h3 className="border-b border-dotted border-[#8a8a8a] pb-[10px] font-['Roboto_Condensed'] text-[22px] uppercase tracking-[3px] text-[#7ea2d6]">
            Corravale University (Fairhaven, Westgate, Alden campuses)
          </h3>
        </div>

        <h5 className="py-[16px] text-center font-['Roboto_Condensed'] text-[16px] uppercase tracking-[2px] text-[#e6e6e6]">
          In 2022, Marrenia students came from
        </h5>
        <div className="flex flex-wrap items-center justify-center gap-[60px] py-[20px]">
          {[
            ["83", "All Marrenia counties"],
            ["50", "States"],
            ["99", "Countries"],
          ].map(([n, l]) => (
            <div key={l} className="text-center">
              <p className="font-['Roboto_Condensed'] text-[56px] font-bold leading-none text-[#ffcb0b]">{n}</p>
              <p className="text-[14px] uppercase tracking-[1px] text-[#e6e6e6]">{l}</p>
            </div>
          ))}
        </div>

        <div className="my-[40px] text-center">
          <h3 className="border-b border-dotted border-[#8a8a8a] pb-[10px] font-['Roboto_Condensed'] text-[22px] uppercase tracking-[3px] text-[#7ea2d6]">
            Corravale Medicine
          </h3>
        </div>
        <div className="grid gap-[30px] sm:grid-cols-2">
          <div className="text-center">
            <p className="font-['Roboto_Condensed'] text-[54px] font-bold leading-none text-[#ffcb0b]">#1</p>
            <p className="text-[16px] uppercase text-[#e6e6e6]">Top Hospital in Marrenia (2023)</p>
          </div>
          <div className="text-center">
            <p className="font-['Roboto_Condensed'] text-[54px] font-bold leading-none text-[#ffcb0b]">#1</p>
            <p className="text-[16px] uppercase text-[#e6e6e6]">Children's Hospital in Marrenia (2023)</p>
          </div>
        </div>
        <p className="py-[16px] text-center text-[13px] uppercase tracking-[1px] text-[#b9b9b9]">
          Honor Roll of Top Hospitals National Rankings Report (2023)
        </p>
        <p className="text-center text-[13px] uppercase tracking-[1px] text-[#b9b9b9]">
          Ranked nationally in: 12 adult specialties, 9 children's specialties (2021)
        </p>
        <p className="pt-[4px] text-center text-[13px] uppercase tracking-[1px] text-[#b9b9b9]">National Rankings Report</p>
        <div className="flex flex-wrap justify-center gap-[40px] py-[16px] text-center text-[14px] text-[#e6e6e6]">
          <span>Three Hospitals and 130+ Health Clinics/Centers</span>
          <span>Employment: 22,500 *</span>
          <span>Patient Visits: 2.4M (2021)</span>
        </div>

        <div className="my-[40px] text-center">
          <h3 className="border-b border-dotted border-[#8a8a8a] pb-[10px] font-['Roboto_Condensed'] text-[22px] uppercase tracking-[3px] text-[#7ea2d6]">
            Impact
          </h3>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-[60px] text-center">
          <div>
            <p className="text-[13px] uppercase tracking-[1px] text-[#c3c3c3]">More than</p>
            <p className="font-['Roboto_Condensed'] text-[46px] font-bold leading-none text-[#ffcb0b]">$10.4B</p>
            <p className="text-[13px] uppercase text-[#c3c3c3]">Total revenue from operating activities (2023)</p>
          </div>
          <div>
            <p className="text-[13px] uppercase tracking-[1px] text-[#c3c3c3]">One of the state's</p>
            <p className="font-['Roboto_Condensed'] text-[46px] font-bold leading-none text-[#ffcb0b]">Top 5</p>
            <p className="text-[13px] uppercase text-[#c3c3c3]">Employers — Marrenia Business Journal (2021)</p>
          </div>
          <div>
            <p className="text-[13px] uppercase tracking-[1px] text-[#c3c3c3]">More than</p>
            <p className="font-['Roboto_Condensed'] text-[46px] font-bold leading-none text-[#ffcb0b]">668,000</p>
            <p className="text-[13px] uppercase text-[#c3c3c3]">Living alumni worldwide</p>
          </div>
        </div>
        <div className="flex flex-wrap justify-center gap-[40px] py-[16px] text-center text-[14px] text-[#e6e6e6]">
          <span>Total Employment: 30,800</span>
          <span>Statewide Research Corridor: CU's Economic Impact on the State of Marrenia: $11.8B</span>
        </div>

        <div className="mt-[40px] overflow-x-auto px-[10px]">
          <table className="w-full min-w-[600px] border-collapse text-[15px]">
            <thead>
              <tr>
                <th className="border-b border-[#666] px-[10px] py-[10px] text-left uppercase text-white">Fall 2025</th>
                <th className="border-b border-[#666] px-[10px] py-[10px] text-right uppercase text-[#7ea2d6]">Fairhaven</th>
                <th className="border-b border-[#666] px-[10px] py-[10px] text-right uppercase text-[#7ea2d6]">Westgate</th>
                <th className="border-b border-[#666] px-[10px] py-[10px] text-right uppercase text-[#7ea2d6]">Alden</th>
              </tr>
            </thead>
            <tbody>
              {enrollment.map((row) => (
                <tr key={row.label}>
                  <td className="border-b border-[#555] px-[10px] py-[8px] text-[#c3c3c3]">{row.label}</td>
                  {row.values.map((v, i) => (
                    <td key={i} className="border-b border-[#555] px-[10px] py-[8px] text-right text-[#e6e6e6]">
                      {v}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <table className="mt-[20px] w-full min-w-[600px] border-collapse text-[15px]">
            <thead>
              <tr>
                <th className="border-b border-[#666] px-[10px] py-[10px] text-left uppercase text-white">2025-2026</th>
                <th className="border-b border-[#666] px-[10px] py-[10px] text-right uppercase text-[#7ea2d6]">Fairhaven</th>
                <th className="border-b border-[#666] px-[10px] py-[10px] text-right uppercase text-[#7ea2d6]">Westgate</th>
                <th className="border-b border-[#666] px-[10px] py-[10px] text-right uppercase text-[#7ea2d6]">Alden</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border-b border-[#555] px-[10px] py-[8px] uppercase text-white" colSpan={4}>
                  Tuition + Fees ‡
                </td>
              </tr>
              {costs.map((row) => (
                <tr key={row.label}>
                  <td className="border-b border-[#555] px-[10px] py-[8px] text-[#c3c3c3]">{row.label}</td>
                  {row.values.map((v, i) => (
                    <td key={i} className="border-b border-[#555] px-[10px] py-[8px] text-right text-[#e6e6e6]">
                      {v}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <p className="py-[10px] text-[13px] leading-[1.6] text-[#b9b9b9]">
            * Corravale University Health (does not include Medical School)
            <br />
            ** 2025-2026 costs for a CAS undergraduate
            <br />‡ Based on a 15-credit semester course load
          </p>
          <p className="text-[13px] text-[#b9b9b9]">Updated January 2026</p>
        </div>

        <p className="pt-[20px] text-center">
          <Link to="/about/" className="text-[#ffcb0b] no-underline hover:underline">
            ← Back to About
          </Link>
        </p>
      </div>
    </div>
  );
}
