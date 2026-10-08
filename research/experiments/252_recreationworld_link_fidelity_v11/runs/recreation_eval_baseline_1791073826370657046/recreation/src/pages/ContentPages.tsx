import { Link } from "@/lib/router";
import { img } from "@/data/assets";
import { SidebarPage, Voices, PageTitle } from "@/components/Layout";
import { CircleArrowRight } from "@/components/Icons";
import { HomeGallery } from "./MorePages";

/* ---------------- About ---------------- */
export function AboutPage() {
  return (
    <>
      <SidebarPage
        title="About"
        intro="Welcome to Corravale University, a place shaped by enduring traditions and devoted to building brighter futures. We invite you to explore the spirited community that makes us the proud home of the Bold & Boundless."
        sidebarImage={img.aboutSidebar}
        sidebarCaption="Few institutions are as committed as we are to both affordability and excellence. Meet the people who make Corravale a leader in higher education, and explore the bold, limitless work we do in partnership with our community."
        groups={[
          { heading: "Facts & History", links: [
            { label: "Accreditation", to: "/_404.html" },
            { label: "Annual Report", to: "/_404.html" },
            { label: "Faculty Honors", to: "/_404.html" },
            { label: "Facts & Figures", to: "/facts-figures/" },
            { label: "Famous Alumni", to: "/_404.html" },
            { label: "Health System", to: "/_404.html" },
            { label: "Corravale Almanac", to: "/_404.html" },
            { label: "Mission", to: "/_404.html" },
            { label: "CU Heritage Project", to: "/_404.html" },
          ] },
          { heading: "Academic Units & Campuses", links: [
            { label: "All Colleges & Schools", to: "/schools-colleges/" },
            { label: "Health System", to: "/_404.html" },
            { label: "Westhaven Campus", to: "/_404.html" },
            { label: "Rowan Campus", to: "/_404.html" },
          ] },
          { heading: "Leadership & Administration", links: [
            { label: "Board of Regents", to: "/_404.html" },
            { label: "Office of the President", to: "/_404.html" },
            { label: "Office of the Provost", to: "/_404.html" },
            { label: "Executive Offices", to: "/_404.html" },
          ] },
          { heading: "State & Community", links: [
            { label: "Government Relations", to: "/_404.html" },
            { label: "Corporate Relations", to: "/_404.html" },
            { label: "Statewide Research Corridor", to: "/_404.html" },
          ] },
          { heading: "Jobs", links: [
            { label: "Job Postings", to: "/_404.html" },
            { label: "Human Resources", to: "/_404.html" },
            { label: "Benefits", to: "/_404.html" },
            { label: "Student Employment", to: "/_404.html" },
            { label: "Career Center", to: "/_404.html" },
          ] },
          { heading: "News & Events", links: [
            { label: "Corravale News", to: "/_404.html" },
            { label: "Events Calendar", to: "/_404.html" },
            { label: "Corravale Today", to: "/_404.html", note: "Alumni Magazine" },
            { label: "Corravale Daily", to: "/_404.html", note: "Student Newspaper" },
            { label: "The University Record", to: "/_404.html", note: "News for Faculty & Staff" },
            { label: "Key Issues", to: "/_404.html" },
          ] },
          { heading: "Academic, Research & Cultural Initiatives", links: [
            { label: "Arts & Culture", to: "/_404.html" },
            { label: "Entrepreneurship & Innovation", to: "/_404.html" },
            { label: "Global Corravale", to: "/_404.html" },
            { label: "Heritage", to: "/_404.html" },
            { label: "Presidential Initiatives & Focus Areas", to: "/_404.html" },
            { label: "Sustainability", to: "/_404.html" },
          ] },
          { heading: "Campus Information", links: [
            { label: "Campus Health Update", to: "/_404.html" },
            { label: "Clock Tower Lighting", to: "/_404.html" },
            { label: "Logistics, Transportation & Parking", to: "/_404.html" },
            { label: "Maps & Directions", to: "/_404.html" },
            { label: "Blue Line", to: "/_404.html" },
            { label: "Social Media Directory", to: "/_404.html" },
            { label: "Campus Information Centers", to: "/_404.html" },
            { label: "Art in Public Spaces", to: "/_404.html" },
          ] },
          { heading: "Visit", links: [
            { label: "Maps, Directions & Transportation", to: "/_404.html" },
            { label: "Admissions Tours", to: "/_404.html" },
            { label: "Westhaven Convention & Visitors Bureau", to: "/_404.html" },
          ] },
        ]}
      />
      <Voices
        label="Voices of Our Campus"
        image={img.aboutVoice}
        caption="Graduate students gather to review their final projects while relaxing in the sunlit atrium of the Halverson Business College."
      />
    </>
  );
}

/* ---------------- Academics ---------------- */
export function AcademicsPage() {
  return (
    <>
      <SidebarPage
        title="Academics"
        intro="Corravale's intellectual energy delivers distinction across every field and around the globe. We are counted among the leaders in higher education thanks to the outstanding strength of our 19 schools and colleges, globally respected faculty, and departments offering 250 degree programs."
        sidebarImage={img.academicsSidebar}
        sidebarCaption="Students attend a lecture on the central quad"
        groups={[
          { heading: "Schools, Colleges & Campuses", links: [
            { label: "Accreditation", to: "/_404.html" },
            { label: "Flagship Schools & Colleges", to: "/_404.html" },
            { label: "CV Westgate", to: "/_404.html" },
            { label: "CV Alden", to: "/_404.html" },
          ] },
          { heading: "Libraries", links: [
            { label: "Corravale Library", to: "/_404.html" },
            { label: "Catalog Search", to: "/_404.html" },
            { label: "All Branches", to: "/_404.html" },
          ] },
          { heading: "Undergraduate Programs", links: [
            { label: "Admissions", to: "/_404.html" },
            { label: "Majors", to: "/_404.html" },
            { label: "Undergraduate Colleges & Schools", to: "/_404.html" },
            { label: "Innovation & Entrepreneurship", to: "/_404.html" },
            { label: "Learning Networks", to: "/_404.html" },
          ] },
          { heading: "International & Away Programs", links: [
            { label: "Involvement Opportunities", to: "/_404.html" },
            { label: "Global Corravale", to: "/_404.html" },
            { label: "Metro Center", to: "/_404.html" },
          ] },
          { heading: "Graduate Programs", links: [
            { label: "Fields of Study", to: "/_404.html" },
            { label: "Innovation & Entrepreneurship", to: "/_404.html" },
            { label: "Graduate Schools & Colleges", to: "/_404.html" },
          ] },
          { heading: "Digital & Lifelong Learning", links: [
            { label: "Academic Innovation", to: "/_404.html" },
            { label: "Distance Education Disclosures", to: "/_404.html" },
            { label: "Executive Education", to: "/_404.html" },
            { label: "Lifelong Learning", to: "/_404.html" },
            { label: "Corravale Online Courses", to: "/_404.html" },
          ] },
          { heading: "Services & Resources", links: [
            { label: "Academic Support Services", to: "/_404.html" },
            { label: "Academic Calendar", to: "/_404.html" },
            { label: "First Generation Students", to: "/_404.html" },
            { label: "Computing on Campus", to: "/_404.html" },
            { label: "Arts Course Guide", to: "/_404.html" },
            { label: "Faculty Honors", to: "/_404.html" },
          ] },
          { heading: "Summer Programs", links: [
            { label: "Summer Programs Directory", to: "/_404.html" },
          ] },
        ]}
      />
      <Voices
        label="Voices of Our Campus"
        image={img.academicsSidebar}
        caption="A student paints in a bright studio at the Arts and Architecture Center on the north campus."
      />
    </>
  );
}

/* ---------------- Life at Corravale ---------------- */
export function LifePage() {
  return (
    <>
      <SidebarPage
        title="Life at Corravale"
        intro="Drawing gifted faculty, staff and students from across the globe, the landmark Corravale campus overflows with fresh perspectives, opportunities and events. Everything unfolds within the lively setting of Fairhaven, a city celebrated for its thriving arts scene, culture, parks and restaurants."
        sidebarImage={img.lifeSidebar}
        sidebarCaption="Cyclists coast past the cube sculpture at Founders Plaza on the main quad"
        groups={[
          { heading: "Campus Information", links: [
            { label: "Facts & Figures", to: "/facts-figures/" },
            { label: "Clock Tower Lighting", to: "/_404.html" },
            { label: "Campus Information Centers", to: "/_404.html" },
            { label: "Events Calendar", to: "/_404.html" },
            { label: "Maps, Directions & Transportation", to: "/_404.html" },
            { label: "Public Safety and Security", to: "/_404.html" },
            { label: "Social Media Directory", to: "/_404.html" },
            { label: "University Unions", to: "/_404.html" },
            { label: "Visiting Information", to: "/_404.html" },
          ] },
          { heading: "Student Resources", links: [
            { label: "Careers Office", to: "/_404.html" },
            { label: "Technology Services", to: "/_404.html" },
            { label: "Student Affairs", to: "/_404.html" },
            { label: "Eating", to: "/_404.html" },
            { label: "First-Generation Scholars", to: "/_404.html" },
            { label: "Lodging", to: "/_404.html" },
            { label: "Support for Students with Disabilities", to: "/_404.html" },
            { label: "Campus Employment Office", to: "/_404.html" },
            { label: "Campus Life", to: "/_404.html" },
            { label: "Campus Organizations", to: "/_404.html" },
            { label: "University Health & Wellness", to: "/_404.html" },
          ] },
          { heading: "Fairhaven", links: [
            { label: "City of Fairhaven", to: "/_404.html" },
            { label: "Convention & Tourism Bureau", to: "/_404.html" },
            { label: "Fairhaven News & Events", to: "/_404.html" },
          ] },
          { heading: "Arts & Heritage", links: [
            { label: "Arts & Heritage", to: "/_404.html" },
            { label: "Exhibits", to: "/_404.html" },
            { label: "University Concert Society", to: "/_404.html" },
            { label: "Corravale Botanical Gardens & Brightwood Arboretum", to: "/_404.html" },
          ] },
          { heading: "Athletics & Wellness", links: [
            { label: "Athletics", to: "/_404.html" },
            { label: "Corravale Recreation", to: "/_404.html" },
            { label: "Sports & Fitness Centers", to: "/_404.html" },
            { label: "Wellness Programs", to: "/_404.html" },
          ] },
          { heading: "Accessibility", links: [
            { label: "Accessibility Support", to: "/_404.html" },
            { label: "Support for Students with Disabilities", to: "/_404.html" },
            { label: "Equity, Civil Rights, and Fair Access", to: "/_404.html" },
          ] },
        ]}
      />
      <Voices
        label="Telling Our Stories"
        image={img.lifeVoice}
        caption="A student refines a digital illustration in the Visual Arts Studio at the Corravale Student Center."
      />
    </>
  );
}

/* ---------------- Athletics ---------------- */
export function AthleticsPage() {
  return (
    <>
      <SidebarPage
        title="Athletics"
        intro="Rise Ravens! Corravale's proud athletics heritage began in 1889 and thrives to this day, with our teams earning more than 40 national championships across 15 varsity sports. Students, faculty and staff also take part in dozens of intramural, club sport and fitness programs every year."
        sidebarImage={img.athleticsSidebar}
        sidebarCaption="Corravale Athletics is honored to deliver transformative experiences to over 900 student-athletes competing in 29 sports."
        groups={[
          { heading: "Varsity Sports", links: [
            { label: "GoRavens.com", to: "/_404.html" },
            { label: "Tickets", to: "/_404.html" },
            { label: "Competition Schedule", to: "/_404.html" },
          ] },
          { heading: "Facilities", links: [
            { label: "Athletics", to: "/_404.html" },
            { label: "Recreational Sports", to: "/_404.html" },
          ] },
          { heading: "Club & Intramural Sports", links: [
            { label: "Club Sports", to: "/_404.html" },
            { label: "Intramural Sports", to: "/_404.html" },
          ] },
          { heading: "Seasonal Youth Athletics", links: [
            { label: "Skills Clinics", to: "/_404.html" },
            { label: "PlayPals", to: "/_404.html" },
          ] },
          { heading: "Campus Recreation & Wellness Offerings", links: [
            { label: "Intramural Athletics", to: "/_404.html" },
            { label: "Wellness Classes", to: "/_404.html" },
          ] },
        ]}
      />
      <Voices
        label="Telling Our Stories"
        image={img.athleticsVoice}
        caption="Students enjoy an evening tennis match on the Rivergate courts just beyond the Halden-Brooks Residence Hall."
      />
    </>
  );
}

/* ---------------- Research ---------------- */
const trending = [
  { score: "221", title: "Recurrent Non-Cardiac Chest Pain", meta: ["Article in Halcyon: Journal of the National Medical Society", "June 2026", "142 mentions in the past week"] },
  { score: "357", title: "Global, regional, and national age-sex-specific incidence and survival trends, 1960-2020: a comprehensive analysis for the Worldwide Disease Impact Survey 2020", meta: ["Article in The Vantage", "October 2019", "51 mentions in the past week"] },
  { score: "3467", title: "Prolonged screen time in bed and the risk of poor sleep", meta: ["Article in Nexus One", "November 2025", "44 mentions in the past week"] },
  { score: "2125", title: "Association of Renal Injury With Mortality in Hospitalized Patients With Severe Viral Pneumonia in Delna", meta: ["Article in Halcyon Cardiology", "June 2020", "39 mentions in the past week"] },
  { score: "200", title: "Visceral Fat and Associations With Metabolic Risk Factors in the Brightwater Heart Cohort", meta: ["Article in Atherosclerosis, Thrombosis, and Vascular Science (Crestline)", "August 2013", "29 mentions in the past week"] },
  { score: "2764", title: "Persistent illness linked to respiratory virus reinfection among children and adolescents in the recent era (RENEW-EHR): a retrospective cohort study", meta: ["Article in Vantage Infectious Diseases", "November 2025", "28 mentions in the past week"] },
  { score: "93", title: "RIGOR+AI: an updated quality, risk of bias, and applicability appraisal tool for prediction models built with regression or machine learning approaches", meta: ["Article in Continental Medical Review", "April 2025", "24 mentions in the past week"] },
  { score: "6579", title: "Accumulation of microplastics in postmortem human tissue", meta: ["Article in Frontier Medicine", "January 2025", "22 mentions in the past week"] },
  { score: "25", title: "Delayed Detection of Anastomotic Leak and Failure to Rescue After Bowel Surgery", meta: ["Article in Vantage Surgery", "March 2026", "21 mentions in the past week"] },
  { score: "13", title: "Biomarkers in Septic Shock: From Bench to Bedside", meta: ["Article in Journal of Cardiothoracic and Vascular Care", "November 2025", "24 mentions in the past week"] },
  { score: "735", title: "Projected Burden of COVID-19 Cases, Outpatient Encounters, Hospital Admissions, and Fatalities in the US From October 2022 to September 2024", meta: ["Article in Annals of Internal Care", "March 2026", "23 mentions in the past week"] },
  { score: "352", title: "Favorable and adverse psychosocial effects of receiving a cancer diagnosis during adolescence or young adulthood", meta: ["Article in Oncology (0008543X)", "March 2012", "23 mentions in the past week"] },
  { score: "243", title: "Beliefs about the health risks of cigarette smoking: A new scale reveals widespread misperception", meta: ["Article in Open Bio", "August 2017", "23 mentions in the past week"] },
  { score: "403", title: "The Cortisol Awakening Response: Mechanisms and Physiological Relevance", meta: ["Article in Hormone Reviews", "August 2024", "22 mentions in the past week"] },
  { score: "412", title: "Widespread evidence of directional selection fulfills the potential of ancient DNA to illuminate human adaptation", meta: ["September 2024", "21 mentions in the past week"] },
  { score: "14", title: "A Discipline in Flux: Catheter-Based Treatment in the 2026 AHA/ACC Acute Pulmonary Embolism Guideline", meta: ["Article in Heart", "April 2026", "21 mentions in the past week"] },
  { score: "1348", title: "Adverse social relationships as emerging risk factors for accelerated aging, inflammation, and multimorbidity", meta: ["Article in Proceedings of the National Institute of Natural Sciences of the United Provinces", "February 2026", "19 mentions in the past week"] },
  { score: "81", title: "Tucatinib–trastuzumab–capecitabine as therapy for leptomeningeal metastasis among women with HER2+ breast cancer: TBCRC049 phase 2 trial findings", meta: ["Article in Cancer Today", "March 2026", "19 mentions in the past week"] },
  { score: "162", title: "Frequency and correlates of prenatal cannabis use in a US state: A statewide population‐based pregnancy cohort", meta: ["Article in Dependence", "September 2025", "18 mentions in the past week"] },
  { score: "79", title: "A leader-repeat hairpin suppresses spurious CRISPR RNA biogenesis across diverse CRISPR-Cas13 systems", meta: ["Article in Gene Journal", "April 2026", "18 mentions in the past week"] },
  { score: "1107", title: "Impact of a high-dose 24-h infusion of tranexamic acid on mortality and thromboembolic outcomes in patients with acute gastrointestinal bleeding (HALT-IT): an international randomised, double-blind, placebo-controlled trial", meta: ["Article in The Scalpel", "June 2020", "17 mentions in the past week"] },
  { score: "246", title: "National public health leaders must actively dispel common myths about e‐cigarette safety", meta: ["Article in Dependency", "December 2023", "17 mentions in the past week"] },
  { score: "20", title: "Evaluating Alternative Approaches for Guiding the Choice of Initial Empiric Antibiotic Treatment in Pneumonia Caused by Gram-Negative Bacteria Among Critical Care Patients", meta: ["Article in Frontiers of Infectious Medicine", "November 2024", "17 mentions in the past week"] },
  { score: "1256", title: "The Meridian Genome Atlas: 300 genomes drawn from 142 distinct human populations", meta: ["Article in Lumen", "September 2015", "16 mentions in the past week"] },
  { score: "566", title: "From Cigarettes to Engineered Snacks: How Corporate Design Fuels the Rising Wave of Avoidable Chronic Illness", meta: ["Article in Meridian Quarterly", "January 2026", "16 mentions in the past week"] },
];

export function ResearchPage() {
  return (
    <>
      <SidebarPage
        title="Research"
        intro="With expenditures topping $1 billion, research sits at the core of Corravale's mission and extends across all 19 schools and colleges. Corravale is a strong champion of collaboration and interdisciplinary research initiatives that engage faculty and students from every corner of campus."
        sidebarImage={img.researchSidebar}
        sidebarCaption="Corravale researchers have shown that lightweight organic solar cells can reach 8 percent efficiency."
        groups={[
          { heading: "Research Across Campus", links: [
            { label: "Overview", to: "/_404.html" },
            { label: "The Corravale Research Scene", to: "/_404.html" },
            { label: "Schools, Colleges and Campuses", to: "/_404.html" },
            { label: "Initiatives", to: "/_404.html" },
            { label: "Research at Corravale", to: "/_404.html" },
          ] },
          { heading: "Student Research", links: [
            { label: "Research Opportunities", to: "/_404.html" },
            { label: "Schools & Colleges", to: "/_404.html" },
          ] },
          { heading: "Research Administration", links: [
            { label: "Office of the Vice President for Research", to: "/_404.html" },
            { label: "Office of Research and Sponsored Projects", to: "/_404.html" },
            { label: "Finance — Sponsored Programs", to: "/_404.html" },
            { label: "eResearch", to: "/_404.html" },
          ] },
          { heading: "Resources for Researchers", links: [
            { label: "Research Resources Portal", to: "/_404.html" },
            { label: "Funding and Research Development", to: "/_404.html" },
            { label: "Research Administration", to: "/_404.html" },
            { label: "Manage Research", to: "/_404.html" },
            { label: "Compliance and Integrity", to: "/_404.html" },
            { label: "Collaborate and Partner", to: "/_404.html" },
            { label: "Communicate and Disseminate", to: "/_404.html" },
          ] },
          { heading: "Research News", links: [
            { label: "Corravale Research", to: "/_404.html" },
            { label: "Federal Research Reports", to: "/_404.html" },
            { label: "Corravale News", to: "/_404.html" },
            { label: "Research Annual Reports", to: "/_404.html" },
            { label: "CRC Annual Reports", to: "/_404.html" },
            { label: "Corravale Medicine News", to: "/_404.html" },
            { label: "Faculty Honors", to: "/_404.html" },
          ] },
          { heading: "Economic Impact", links: [
            { label: "Innovation Partnerships", to: "/_404.html" },
            { label: "Center for Economic Impact", to: "/_404.html" },
            { label: "Statewide Innovation Alliance", to: "/_404.html" },
            { label: "Ignite Forward", to: "/_404.html" },
            { label: "Accelerated Clinical Discovery", to: "/_404.html" },
          ] },
        ]}
      />
      <section className="bg-[#f4f4f4] py-10">
        <div className="mx-auto max-w-[1180px] px-5">
          <h2 className="mb-4 text-center font-cond text-[26px] tracking-[0.2em] text-[#444] uppercase">
            Trending Research
          </h2>
          <p className="mx-auto mb-8 max-w-[900px] text-center text-[14px] leading-relaxed text-[#555]">
            Listed here are 25 recent studies that have drawn notice across news outlets, social platforms
            and other online channels over the past week, spanning coverage from broad general-interest
            media to scholarly citations. These highlights from Corravale scholars reflect only a small
            slice of the more than 271,000 research outputs generated each year by our academic community.
          </p>
          <ul className="grid gap-x-8 gap-y-6 md:grid-cols-2 lg:grid-cols-3">
            {trending.map((item) => (
              <li key={item.title} className="flex gap-3">
                <Link to="/_404.html" aria-label={`Impact score ${item.score}`} className="shrink-0">
                  <span className="grid h-[52px] w-[52px] place-items-center rounded-md border-[3px] border-[#2f7fd0] font-cond text-[14px] font-bold text-[#2f7fd0]">
                    {item.score}
                  </span>
                </Link>
                <div>
                  <h4 className="mb-1">
                    <Link to="/_404.html" className="text-[14px] leading-snug font-bold text-[#00274c] hover:underline">
                      {item.title}
                    </Link>
                  </h4>
                  <ul className="space-y-[2px] text-[12px] text-[#666]">
                    {item.meta.map((m) => (
                      <li key={m}>{m}</li>
                    ))}
                  </ul>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>
      <Voices
        label="Voices of Our Campus"
        image={img.healthVoice}
        caption="The Kinesiology 437 seminar outfits a volunteer with a motion detection sensor suit to study how knee injuries restrict natural movement."
      />
    </>
  );
}

/* ---------------- Health & Medicine ---------------- */
export function HealthPage() {
  return (
    <>
      <SidebarPage
        title="Health & Medicine"
        intro="Our award-winning Corravale Health System cares for millions of patients, leads hundreds of research studies and prepares thousands of tomorrow's medical professionals every year. For our students, faculty and staff, a broad range of health and wellness services and programs are offered across campus."
        sidebarImage={img.healthSidebar}
        sidebarCaption="The Advanced Simulation Lab lets aspiring physicians practice on lifelike patient models at the Corravale Medical College"
        groups={[
          { heading: "Health System", links: [
            { label: "MyCorraHealth.org Patient Portal", to: "/_404.html" },
            { label: "Corravale Health", to: "/_404.html" },
          ] },
          { heading: "Health Services for Students, Faculty & Staff", links: [
            { label: "University Health & Counseling", to: "/_404.html" },
            { label: "Mental Health Resources", to: "/_404.html" },
            { label: "Employee Benefits", to: "/_404.html" },
            { label: "CorraWell Health and Well-being Programs", to: "/_404.html" },
            { label: "Corravale Health Line", to: "/_404.html" },
            { label: "Well-Being Collective", to: "/_404.html" },
          ] },
          { heading: "Health & Medicine Programs", links: [
            { label: "College of Optometry", to: "/_404.html" },
            { label: "Medical College", to: "/_404.html" },
            { label: "College of Dentistry", to: "/_404.html" },
            { label: "School of Physiology", to: "/_404.html" },
            { label: "College of Nursing", to: "/_404.html" },
            { label: "School of Global Health", to: "/_404.html" },
          ] },
        ]}
      />
      <Voices
        label="Telling Our Stories"
        image={img.healthVoice}
        caption="Dana Okafor, pharmacist at Fairmont Grocers, gives a vaccine. Elias Warren, junior at Corravale, receives his shot."
      />
    </>
  );
}

/* ---------------- Initiatives ---------------- */
export function InitiativesPage() {
  return (
    <>
      <SidebarPage
        title="Initiatives"
        intro="Corravale leads a broad range of signature initiatives and outreach programs centered on priority areas that empower us to advance academic excellence, drive meaningful change, and confront the complex global challenges shaping our shared future."
        sidebarImage={img.initiativesSidebar}
        sidebarCaption="Student volunteers help tend the Campus Farm at the Corravale Botanical Gardens"
        groups={[
          { heading: "Sustainability", links: [
            { label: "Corra Green", to: "/_404.html" },
            { label: "Follow our journey toward full carbon neutrality", to: "/_404.html" },
            { label: "100+ green organizations across campus", to: "/_404.html" },
            { label: "800+ green-focused courses", to: "/_404.html" },
            { label: "Learn “where it goes”", to: "/_404.html" },
            { label: "School of Environmental and Earth Studies", to: "/_404.html" },
          ] },
          { heading: "Leadership Initiatives & Focus Areas", links: [
            { label: "Arts Initiative", to: "/_404.html" },
            { label: "Campus Climate: Sexual Misconduct", to: "/_404.html" },
            { label: "Master Plan 2050", to: "/_404.html" },
            { label: "Climate, Sustainability, and a Carbon-Free Future", to: "/_404.html" },
            { label: "Health and Wellness", to: "/_404.html" },
            { label: "Shared Heritage Project", to: "/_404.html" },
            { label: "Look to Corravale", to: "/_404.html" },
            { label: "Bold Ideas in Teaching and Research", to: "/_404.html" },
          ] },
          { heading: "Outreach & Partnership", links: [
            { label: "Government Affairs", to: "/_404.html" },
            { label: "Industry Engagement Center", to: "/_404.html" },
            { label: "Technology Partnerships", to: "/_404.html" },
            { label: "CV + Rivbend", to: "/_404.html" },
            { label: "Statewide Research Corridor", to: "/_404.html" },
          ] },
          { heading: "Impact", links: [
            { label: "CV + Fairhaven", to: "/_404.html" },
            { label: "CV + Rivbend", to: "/_404.html" },
            { label: "Cost Savings & Budget", to: "/_404.html" },
          ] },
        ]}
      />
      <Voices
        label="Telling Our Stories"
        image={img.initiativesVoice}
        caption="CV researchers have received a $2 million federal grant to identify and cultivate green algae that can power a high-yield, environmentally sustainable and cost-effective system for producing clean biofuels."
      />
    </>
  );
}

/* ---------------- Giving ---------------- */
export function GivingPage() {
  return (
    <>
      <SidebarPage
        title="Giving"
        intro="Corravale is dedicated to putting its academic strength and resources to work for the good of the wider world. A deeply rooted culture of philanthropy is what makes that ambition attainable. The generous commitment of our Corravale donors changes lives each day."
        sidebarImage={img.givingSidebar}
        sidebarCaption="Corravale students write thank-you notes expressing their gratitude to alumni and donors"
        groups={[
          { heading: "Corravale Giving", links: [
            { label: "Make a Gift to CU", to: "/_404.html" },
            { label: "Stories and News", to: "/_404.html" },
          ] },
          { heading: "Ways to Give", links: [
            { label: "Give Today", to: "/_404.html" },
            { label: "Crowdfunding at CU", to: "/_404.html" },
            { label: "Cryptocurrency", to: "/_404.html" },
            { label: "Donor Advised Funds", to: "/_404.html" },
            { label: "Employer Matching", to: "/_404.html" },
            { label: "Giving from Abroad", to: "/_404.html" },
            { label: "Gifts-in-Kind", to: "/_404.html" },
            { label: "Estate and Legacy Giving", to: "/_404.html" },
            { label: "Multiyear Pledges", to: "/_404.html" },
            { label: "Securities and Bonds", to: "/_404.html" },
            { label: "Memorial and Honor Gifts", to: "/_404.html" },
            { label: "Wire and ACH Bank Transfers", to: "/_404.html" },
          ] },
          { heading: "Talk with Our Teams", links: [
            { label: "Message Us", to: "/_404.html" },
            { label: "Corporate Partners", to: "/_404.html" },
            { label: "Foundation Partners", to: "/_404.html" },
            { label: "Global Engagement Center", to: "/_404.html" },
            { label: "Regional Major Gifts", to: "/_404.html" },
            { label: "Family & Parent Giving", to: "/_404.html" },
            { label: "Legacy Giving", to: "/_404.html" },
            { label: "Campus Life", to: "/_404.html" },
          ] },
        ]}
      />
      <Voices
        label="Telling Our Stories"
        image={img.givingVoice}
        caption="An ecology and evolutionary biology student catalogs a collection of aquatic life at the Halvorsen Building."
      />
    </>
  );
}

/* ---------------- Prospective Students ---------------- */
export function ProspectivePage() {
  return (
    <>
      <SidebarPage
        title="Prospective Students"
        intro="Corravale's commitment to interdisciplinary study empowers students to shape their academic journey around their own career ambitions and personal goals. As one of the nation's largest public research universities, Corravale hosts thousands of active projects that foster meaningful collaboration between students and faculty."
        sidebarImage={img.prospectiveSidebar}
        sidebarCaption="Graduate mentors and first-year students run experiments side by side in the Aldridge Discovery Lab"
        groups={[
          { heading: "Undergraduate Students", links: [
            { label: "Admissions", to: "/_404.html" },
            { label: "Apply Now", to: "/_404.html" },
            { label: "Majors", to: "/_404.html" },
            { label: "Costs & Financial Aid", to: "/_404.html" },
            { label: "Costs for In-State Residents", to: "/_404.html" },
            { label: "Visiting Information", to: "/_404.html" },
            { label: "Housing & Dining", to: "/_404.html" },
            { label: "Corravale Access", to: "/_404.html" },
          ] },
          { heading: "International Students", links: [
            { label: "International Center", to: "/_404.html" },
            { label: "Undergraduate Programs", to: "/_404.html" },
            { label: "Graduate Programs", to: "/_404.html" },
            { label: "Schools & Colleges", to: "/_404.html" },
            { label: "Costs & Financial Aid", to: "/_404.html" },
          ] },
          { heading: "Graduate Students", links: [
            { label: "Programs of Study", to: "/_404.html" },
            { label: "Schools & Colleges", to: "/_404.html" },
            { label: "Costs & Financial Aid", to: "/_404.html" },
            { label: "Visiting Information", to: "/_404.html" },
            { label: "Corravale Access", to: "/_404.html" },
          ] },
          { heading: "Student Resources", links: [
            { label: "Academic Calendar", to: "/_404.html" },
            { label: "Costs & Financial Aid", to: "/_404.html" },
            { label: "First-Generation Students", to: "/_404.html" },
            { label: "Housing & Dining", to: "/_404.html" },
            { label: "Library", to: "/_404.html" },
            { label: "Schools & Colleges", to: "/_404.html" },
            { label: "Social Media Directory", to: "/_404.html" },
            { label: "Vax Portal", to: "/_404.html" },
            { label: "Visiting Information", to: "/_404.html" },
            { label: "About Corravale", to: "/_404.html" },
          ] },
        ]}
      />
      <Voices
        label="Voices of Corravale"
        image={img.prospectiveVoice}
        caption="A student sketches quietly in a sunlit studio inside the Design and Media Center on the West Quad"
      />
    </>
  );
}

/* ---------------- Current Students ---------------- */
export function CurrentStudentsPage() {
  return (
    <>
      <SidebarPage
        title="Current Students"
        intro="With more than 1,100 student organizations and classmates from all fifty states and 108 countries, life at Corravale rarely stands still. Hundreds of campus tools, guides, events, and resources are here to help every student stay linked to the full campus experience."
        sidebarImage={img.currentSidebar}
        sidebarCaption="The 3-D Visualization Lab at the Merriston Center on North Quadrant"
        groups={[
          { heading: "Tools", links: [
            { label: "Corravale Access", to: "/_404.html" },
            { label: "Nimbus", to: "/_404.html" },
            { label: "Email", to: "/_404.html" },
            { label: "Email — CVHS", to: "/_404.html" },
            { label: "IT AI Services", to: "/_404.html" },
            { label: "Library Catalog", to: "/_404.html" },
            { label: "Vax Viewer", to: "/_404.html" },
          ] },
          { heading: "Tuition & Financial Aid", links: [
            { label: "Tuition & Fees", to: "/_404.html" },
            { label: "Financial Aid", to: "/_404.html" },
          ] },
          { heading: "Campus Essentials", links: [
            { label: "Public Art on Campus", to: "/_404.html" },
            { label: "Campus Help & Info Desks", to: "/_404.html" },
            { label: "Safety Alert Enrollment", to: "/_404.html" },
            { label: "Top Topics", to: "/_404.html" },
            { label: "Getting Here, Transit & Parking", to: "/_404.html" },
            { label: "Maps & Wayfinding", to: "/_404.html" },
            { label: "Loop Line", to: "/_404.html" },
            { label: "Social Channels Guide", to: "/_404.html" },
            { label: "Campus Health Alerts", to: "/_404.html" },
          ] },
          { heading: "Campus Living", links: [
            { label: "Campus Living", to: "/_404.html" },
            { label: "Student Clubs & Groups", to: "/_404.html" },
            { label: "Event Listings", to: "/_404.html" },
            { label: "Corravale Daily", to: "/_404.html", note: "Campus News Outlet" },
            { label: "About Our Town", to: "/_404.html" },
          ] },
          { heading: "Learning Resources", links: [
            { label: "Semester Schedule", to: "/_404.html" },
            { label: "Course Catalog", to: "/_404.html" },
            { label: "Campus Libraries", to: "/_404.html" },
            { label: "Learning Support Services", to: "/_404.html" },
            { label: "Tech Accessibility", to: "/_404.html" },
            { label: "Discovery", to: "/_404.html" },
          ] },
          { heading: "Support Services", links: [
            { label: "Career Studio", to: "/_404.html" },
            { label: "Technology on Campus", to: "/_404.html" },
            { label: "Office of the Dean", to: "/_404.html" },
            { label: "First-Generation Scholars", to: "/_404.html" },
            { label: "Housing and Meals", to: "/_404.html" },
            { label: "Office of the Student Advocate", to: "/_404.html" },
            { label: "Support for Students with Disabilities", to: "/_404.html" },
            { label: "Student Jobs & Employment", to: "/_404.html" },
            { label: "Student Health & Counseling", to: "/_404.html" },
            { label: "Well-Being Alliance", to: "/_404.html" },
          ] },
          { heading: "Campus Employment", links: [
            { label: "Student Jobs & Employment", to: "/_404.html" },
            { label: "Campus Life Employment", to: "/_404.html" },
            { label: "Graduate Assistant Positions", to: "/_404.html" },
          ] },
          { heading: "Academic, Research & Cultural Programs", links: [
            { label: "Arts", to: "/_404.html" },
            { label: "Innovation & Entrepreneurship", to: "/_404.html" },
            { label: "Global Corravale", to: "/_404.html" },
            { label: "Our Roots", to: "/_404.html" },
            { label: "Green Campus", to: "/_404.html" },
          ] },
        ]}
      />
      <HomeGallery title="Onward Now" />
    </>
  );
}

/* ---------------- Faculty & Staff ---------------- */
export function FacultyStaffPage() {
  return (
    <>
      <SidebarPage
        title="Faculty and Staff"
        intro="Corravale is regarded as one of the best places to work in higher education, according to a national review of universities. We place a high priority on building an environment that helps faculty and staff do their finest work, and we value the contributions of every employee in keeping Corravale a leading public institution."
        sidebarImage={img.facultySidebar}
        sidebarCaption="Bring your best self to work. Learn how ThriveWell's health and wellness programs boost everyday well-being."
        groups={[
          { heading: "Tools", links: [
            { label: "Corravale Access", to: "/_404.html" },
            { label: "Email", to: "/_404.html" },
            { label: "Email — CHS", to: "/_404.html" },
            { label: "Portal", to: "/_404.html" },
            { label: "Community Directory", to: "/_404.html" },
            { label: "Campus AI Tools", to: "/_404.html" },
            { label: "Library Catalog", to: "/_404.html" },
            { label: "Compliance Hotline", to: "/_404.html" },
            { label: "Children on Campus Registration", to: "/_404.html" },
          ] },
          { heading: "Jobs & Career Paths", links: [
            { label: "Job Openings", to: "/_404.html" },
            { label: "Career Explorer", to: "/_404.html" },
          ] },
          { heading: "Faculty & Staff Support", links: [
            { label: "Coverage", to: "/_404.html" },
            { label: "Campus Alert Enrollment", to: "/_404.html" },
            { label: "People & Culture", to: "/_404.html" },
            { label: "Tech Accessibility", to: "/_404.html" },
            { label: "Delivery, Transportation & Parking", to: "/_404.html" },
            { label: "Occupational Wellness Center", to: "/_404.html" },
            { label: "Office of the Faculty Liaison", to: "/_404.html" },
            { label: "Office of the Staff Advocate", to: "/_404.html" },
            { label: "Pay Hub", to: "/_404.html" },
            { label: "Purchasing Services", to: "/_404.html" },
            { label: "Social Media Toolkit", to: "/_404.html" },
            { label: "Campus Health Brief", to: "/_404.html" },
            { label: "University Ledger", to: "/_404.html", note: "Faculty & Staff Notes" },
            { label: "Vax Status", to: "/_404.html" },
            { label: "Well-Being Coalition", to: "/_404.html" },
          ] },
          { heading: "Teaching & Scholarship Resources", links: [
            { label: "Center for Learning Innovation", to: "/_404.html" },
            { label: "Center for the Study of Learning & Teaching", to: "/_404.html" },
            { label: "Learning with Technology Collaborative", to: "/_404.html" },
            { label: "Educator Handbook", to: "/_404.html" },
            { label: "Corravale Publishing", to: "/_404.html" },
          ] },
          { heading: "Schedules", links: [
            { label: "Academic Schedule", to: "/_404.html" },
            { label: "Events Schedule", to: "/_404.html" },
            { label: "Holiday Calendar", to: "/_404.html" },
          ] },
          { heading: "Central Offices", links: [
            { label: "Board of Trustees", to: "/_404.html" },
            { label: "Office of the Chancellor", to: "/_404.html" },
            { label: "Academic Affairs Office", to: "/_404.html" },
            { label: "Leadership Offices", to: "/_404.html" },
            { label: "Key Topics", to: "/_404.html" },
          ] },
        ]}
      />
      <Voices
        label="Sharing Our Stories"
        image={img.facultyVoice}
        caption="A pharmacist fills a prescription at the Corravale Health System pharmacy."
      />
    </>
  );
}

/* ---------------- Parents ---------------- */
export function ParentsPage() {
  return (
    <>
      <SidebarPage
        title="Parents"
        intro="Welcome to the Corravale family. Sending a student to college is a milestone for every household. Corravale is dedicated to helping parents and students make the most of this chapter by sharing up-to-date information about campus life, key dates, and upcoming events."
        sidebarImage={img.parentsSidebar}
        sidebarCaption="A Corravale parent lends a hand to a first-year student on move-in day at Halden Hall"
        groups={[
          { heading: "For Parents & Families", links: [
            { label: "C-Parent", to: "/_404.html" },
            { label: "Undergraduate Admissions", to: "/_404.html" },
            { label: "Portal en Espanol", to: "/_404.html" },
          ] },
          { heading: "Health & Safety", links: [
            { label: "University Health & Counseling", to: "/_404.html" },
            { label: "Counseling & Psychological Services", to: "/_404.html" },
            { label: "Public Safety and Security", to: "/_404.html" },
          ] },
          { heading: "Tools & Resources", links: [
            { label: "Academic Schedule", to: "/_404.html" },
            { label: "Social Media Listings", to: "/_404.html" },
            { label: "Campus Visit Details", to: "/_404.html" },
            { label: "Parent & Family Support", to: "/_404.html" },
          ] },
          { heading: "News & Updates", links: [
            { label: "Corravale Daily", to: "/_404.html", note: "Campus Newspaper" },
            { label: "Corravale News", to: "/_404.html" },
            { label: "Campus Calendar", to: "/_404.html" },
            { label: "Top Topics", to: "/_404.html" },
          ] },
          { heading: "Tuition & Aid Details", links: [
            { label: "Costs for In-State Students", to: "/_404.html" },
            { label: "Fees & Tuition", to: "/_404.html" },
            { label: "Aid & Grants", to: "/_404.html" },
          ] },
          { heading: "Campus Services", links: [
            { label: "Campus Life", to: "/_404.html" },
            { label: "Learning Support", to: "/_404.html" },
            { label: "Career Office", to: "/_404.html" },
            { label: "Global Programs Hub", to: "/_404.html" },
            { label: "Support for Students with Disabilities", to: "/_404.html" },
          ] },
        ]}
      />
      <HomeGallery title="Seize the Day" />
    </>
  );
}

/* ---------------- Alumni ---------------- */
export function AlumniPage() {
  return (
    <>
      <SidebarPage
        title="Alumni"
        intro="Corravale's graduates have gone on to reach the far edges of space, to spark movements that reshape culture and to guide nations. No matter how far they travel, they always seem to find their way home. We're proud to count one of the largest and most devoted communities of living alumni anywhere. Go Vale!"
        sidebarImage={img.alumniSidebar}
        sidebarCaption={'Fans pack the stands for a football game "under the lights" at Weldon Stadium'}
        groups={[
          { heading: "Stay in Touch", links: [
            { label: "Alumni Association", to: "/_404.html" },
            { label: "Social Media Directory", to: "/_404.html" },
            { label: "Corravale Giving", to: "/_404.html" },
            { label: "Make a Gift Online", to: "/_404.html" },
            { label: "Corravale Alumnus", to: "/_404.html", note: "Alumni Magazine" },
            { label: "Corravale Today", to: "/_404.html", note: "Alumni Magazine" },
            { label: "Career Alumni Networking Association (CANA)", to: "/_404.html" },
            { label: "Update Your Graduate Profile", to: "/_404.html" },
          ] },
          { heading: "Corravale Athletics", links: [
            { label: "GoRavens.com", to: "/_404.html" },
            { label: "Tickets", to: "/_404.html" },
            { label: "Football Schedule", to: "/_404.html" },
          ] },
          { heading: "Records & Transcripts", links: [
            { label: "Request Transcript", to: "/_404.html" },
            { label: "Request Copy of Your Diploma", to: "/_404.html" },
            { label: "Update Your Graduate Profile", to: "/_404.html" },
          ] },
          { heading: "Visiting", links: [
            { label: "Art in Public Spaces", to: "/_404.html" },
            { label: "Maps, Directions & Transportation", to: "/_404.html" },
            { label: "New Weldon Convention & Visitors Bureau", to: "/_404.html" },
          ] },
          { heading: "Career Services", links: [
            { label: "Career Center", to: "/_404.html" },
            { label: "Career Development — Alumni Association", to: "/_404.html" },
            { label: "Jobs at CU", to: "/_404.html" },
          ] },
          { heading: "Impact", links: [
            { label: "CU + New Weldon", to: "/_404.html" },
            { label: "CU + Halbrook", to: "/_404.html" },
          ] },
        ]}
      />
      <Voices
        label="Sharing Our Journey"
        image={img.alumniVoice}
        caption="The ensemble performs on stage during the Fall 2024 New Student Convocation. The student conductor turns toward the audience and raises a fist in triumph."
      />
    </>
  );
}

/* ---------------- Schools & Colleges ---------------- */
export function SchoolsCollegesPage() {
  const schools = [
    "Architecture & Urban Planning", "Art & Design", "Business", "Dentistry", "Education",
    "Engineering", "Environment and Sustainability", "Information", "Kinesiology", "Law",
    "Sciences, Letters, and Fine Arts", "Medicine", "Music, Theatre & Dance", "Nursing",
    "Pharmacy", "Public Health", "Public Affairs", "Corravale School of Advanced Study", "Social Work",
  ];
  return (
    <>
      <PageTitle>Schools &amp; Colleges</PageTitle>
      <section className="bg-[#333] py-8">
        <div className="mx-auto max-w-[900px] px-5">
          <p className="mb-8 text-center text-[15px] leading-relaxed text-white/85">
            Students discover their passions and chart their futures across our 19 nationally recognized
            schools and colleges — the heart and soul of the Corravale experience at our flagship campus.
            Meanwhile, our Corravale Westgate and Corravale Alden campuses offer inspiration and direction
            to more than 15,000 students.
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            <LinkPanelList heading="Schools" items={schools} />
            <LinkPanelList heading="Campuses" items={["CV Westgate", "CV Alden"]} />
          </div>
        </div>
      </section>
    </>
  );
}

function LinkPanelList({ heading, items }: { heading: string; items: string[] }) {
  return (
    <nav className="bg-navy-panel">
      <h4 className="bg-[#123a66] px-4 py-2 font-cond text-[13px] tracking-[0.1em] text-maize uppercase">
        {heading}
      </h4>
      <ul className="py-1">
        {items.map((label) => (
          <li key={label}>
            <Link
              to="/_404.html"
              className="group flex items-center justify-between gap-2 px-4 py-[7px] text-[13.5px] text-white/90 hover:text-maize"
            >
              {label}
              <CircleArrowRight size={13} className="text-maize opacity-70 group-hover:opacity-100" />
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

/* ---------------- Facts & Figures ---------------- */
const rankings = [
  { sup: "#", num: "1", bold: "U.S. PUBLIC", rest: "UNIVERSITY", src: "World's Top Universities", tail: " Global Review (2026)" },
  { sup: "#", num: "3", bold: "NATIONAL UNDERGRADUATE", rest: "PUBLIC UNIVERSITIES", src: "ACADEMIC STANDARD REVIEW (2025)" },
  { sup: "#", num: "1", bold: "BEST SMALL COLLEGE", rest: "TOWNS IN AMERICA", src: "CAMPUSGRADE (2025)" },
  { sup: "#", num: "2", bold: "U.S. PUBLIC", rest: "UNIVERSITY", src: "GLOBAL CAMPUS INDEX RANKINGS (2025)" },
  { sup: "#", num: "23", bold: "WORLD REPUTATION", rest: "RANKINGS", src: "MERIDIAN REVIEW (2025)" },
];

const factCols = [
  { heading: "Research", to: "/_404.html", items: ["#2 in research activity among public research universities", "$1.25B in annual federally funded research awards (2024)", "$2.16B in research expenditures (2025)"] },
  { heading: "Innovation Partnerships", to: "/_404.html", items: ["615 new inventions disclosed (2024)", "28 new venture startups founded"] },
  { heading: "2023 Incoming Class", to: "/_404.html", items: ["3.9-4.0 average high school GPA", "31–34 average ACT score", "1350-1530 average SAT range"] },
  { heading: "Athletics", to: "/_404.html", items: ["419 all-time league athletic championships", "900+ student-athletes", "27 Division I varsity teams"] },
  { heading: "Academics", to: "/academics/", items: ["110 grad programs in the top 10 — National Education Digest (2022)", "97% first-year student retention rate", "93% of students graduate within six years", "19 schools and colleges", "280+ degree programs", "15:1 student to faculty ratio"] },
  { heading: "Affordability", to: "/_404.html", items: ["2 of 3 first-year students receive financial aid", "More than $754.6M in scholarships and fellowships awarded to students (2020-21)", "Value Quarterly ranks Corravale No. 1 for value (2022)"] },
];

export function FactsFiguresPage() {
  return (
    <>
      <PageTitle>Facts &amp; Figures</PageTitle>
      <section className="bg-[#333] py-8">
        <div className="mx-auto max-w-[1100px] px-5">
          <p className="mx-auto mb-8 max-w-[900px] text-center text-[15px] leading-relaxed text-white/85">
            More than any institution before us, Corravale holds the potential to become far greater than the
            sum of its many remarkable parts. It is precisely this potential to shape the communities we serve
            that stands as our most enduring value as a university. Below are a few facts and figures that
            begin to convey the scope and ambition of Corravale.
          </p>
          <h3 className="mb-6 text-center font-cond text-[22px] tracking-[0.16em] text-maize uppercase">
            Fairhaven Campus
          </h3>
          <ul className="mb-8 grid gap-6 md:grid-cols-3">
            {rankings.map((r) => (
              <li key={r.num + r.bold}>
                <Link to="/_404.html" className="flex items-start gap-1">
                  <span className="font-cond text-[40px] leading-none font-bold text-maize">
                    <sup className="text-[20px]">{r.sup}</sup>
                    {r.num}
                  </span>
                  <span className="ml-2 mt-1 text-[13px] leading-tight text-white">
                    <span className="font-bold">{r.bold}</span> {r.rest}
                    <em className="block text-[12px] text-white/70 not-italic">{r.src}{r.tail}</em>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
          <div className="grid gap-4 md:grid-cols-3">
            {factCols.map((c) => (
              <div key={c.heading} className="bg-navy-panel">
                <h4 className="bg-[#123a66] px-4 py-2 font-cond text-[13px] font-normal tracking-[0.08em] text-maize uppercase">
                  <Link to={c.to}>{c.heading}</Link>
                </h4>
                <ul className="space-y-2 p-4 text-[13px] text-white/85">
                  {c.items.map((i) => (
                    <li key={i}>
                      <Link to="/_404.html" className="hover:text-maize">
                        {i}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <h3 className="mt-10 mb-4 text-center font-cond text-[22px] tracking-[0.16em] text-maize uppercase">
            Corravale Promise
          </h3>
          <div className="mx-auto max-w-[640px]">
            <img src={img.factsBanner} alt="Corravale Promise" className="mb-4 w-full" />
            <ul className="mb-4 grid gap-3 sm:grid-cols-2">
              <li>
                <Link to="/_404.html" className="block text-center">
                  <span className="block font-cond text-[20px] text-maize">FREE TUITION</span>
                  <span className="block text-[12px] text-white">FOR FAMILIES WITH</span>
                  <span className="block text-[12px] text-white">INCOMES $125,000 &amp; UNDER</span>
                  <span className="mt-1 block text-[11px] text-white/70">ASSETS BELOW $125,000 (effective fall 2025)</span>
                </Link>
              </li>
              <li>
                <Link to="/_404.html" className="block text-center">
                  <span className="block font-cond text-[20px] text-maize">TUITION SUPPORT</span>
                  <span className="block text-[12px] text-white">FOR SOME FAMILIES</span>
                  <span className="mt-1 block text-[11px] text-white/70">EARNING MORE</span>
                </Link>
              </li>
            </ul>
            <p className="mb-4 text-center text-[12px] text-white/70">
              FOUR YEARS FREE FOR QUALIFYING STATE STUDENTS{" "}
              <Link to="/_404.html" className="text-maize underline">FAIRHAVEN</Link>,{" "}
              <Link to="/_404.html" className="text-maize underline">WESTGATE</Link> &amp;{" "}
              <Link to="/_404.html" className="text-maize underline">ALDEN</Link> CAMPUSES
            </p>
            <Link to="/_404.html" className="mx-auto block max-w-[420px] bg-navy-panel p-4 text-center">
              <span className="block font-cond text-[26px] font-bold text-maize">1 out of 4</span>
              <span className="block text-[12px] text-white">IN-STATE UNDERGRADUATES</span>
              <span className="mt-1 block text-[11px] text-white/70">PAY NO TUITION THANKS TO FINANCIAL AID</span>
            </Link>
          </div>

          <h3 className="mt-10 mb-6 text-center font-cond text-[20px] tracking-[0.12em] text-maize uppercase">
            Corravale University (Fairhaven, Westgate, Alden campuses)
          </h3>
          <h5 className="mb-3 text-center font-cond text-[14px] tracking-[0.12em] text-white uppercase">
            In 2022, Marrenia students came from
          </h5>
          <ul className="mb-8 grid grid-cols-3 gap-4 text-center">
            {[["83", "ALL MARRENIA COUNTIES"], ["50", "STATES"], ["99", "COUNTRIES"]].map(([n, l]) => (
              <li key={l}>
                <Link to="/_404.html">
                  <span className="block font-cond text-[38px] font-bold text-maize">{n}</span>
                  <span className="block text-[12px] text-white">{l}</span>
                </Link>
              </li>
            ))}
          </ul>
          <h5 className="mb-3 text-center font-cond text-[14px] tracking-[0.12em] text-white uppercase">
            Corravale Medicine
          </h5>
          <ul className="mb-8 grid grid-cols-2 gap-4 text-center">
            {[["#1", "TOP HOSPITAL", "IN MARRENIA", "(2023)"], ["#1", "CHILDREN'S HOSPITAL", "IN MARRENIA", "(2023)"]].map((r) => (
              <li key={r[1]}>
                <Link to="/_404.html">
                  <span className="block font-cond text-[38px] font-bold text-maize">{r[0]}</span>
                  <span className="block text-[13px] text-white">{r[1]}</span>
                  <span className="block text-[13px] text-maize">{r[2]}</span>
                  <span className="block text-[11px] text-white/60">{r[3]}</span>
                </Link>
              </li>
            ))}
          </ul>
          <h5 className="mb-3 text-center font-cond text-[14px] tracking-[0.12em] text-white uppercase">Impact</h5>
          <ul className="mb-8 grid gap-4 sm:grid-cols-3">
            {[["MORE THAN", "$10.4B", "TOTAL REVENUE FROM OPERATING ACTIVITIES (2023)"], ["ONE OF THE STATE'S", "TOP 5", "EMPLOYERS"], ["MORE THAN", "668,000", "LIVING ALUMNI WORLDWIDE"]].map((r) => (
              <li key={r[1]} className="bg-navy-panel p-4 text-center">
                <Link to="/_404.html">
                  <span className="block text-[11px] text-white/70">{r[0]}</span>
                  <span className="block font-cond text-[30px] font-bold text-maize">{r[1]}</span>
                  <span className="block text-[11px] text-white">{r[2]}</span>
                </Link>
              </li>
            ))}
          </ul>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[13px] text-white">
              <thead>
                <tr className="bg-[#123a66] text-maize">
                  <th className="p-2 text-left">FALL 2025</th>
                  <th className="p-2 text-left"><Link to="/_404.html">Fairhaven</Link></th>
                  <th className="p-2 text-left"><Link to="/_404.html">Westgate</Link></th>
                  <th className="p-2 text-left"><Link to="/_404.html">Alden</Link></th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["Undergraduate Enrollment", "35,358", "6,199", "5,534"],
                  ["In-state", "18,800", "5,673", "5,057"],
                  ["Out-of-state", "16,558", "526", "477"],
                  ["Graduate Enrollment", "18,130", "1,806", "1,585"],
                  ["Student organizations", "1,600+", "180+", "100+"],
                ].map((row, i) => (
                  <tr key={row[0]} className={i % 2 ? "bg-white/5" : ""}>
                    <th className="p-2 text-left font-normal">{row[0]}</th>
                    <td className="p-2">{row[1]}</td>
                    <td className="p-2">{row[2]}</td>
                    <td className="p-2">{row[3]}</td>
                  </tr>
                ))}
              </tbody>
              <thead>
                <tr className="bg-[#123a66] text-maize">
                  <th className="p-2 text-left"><em className="not-italic">2025-2026</em></th>
                  <th className="p-2 text-left"><Link to="/_404.html">Fairhaven</Link></th>
                  <th className="p-2 text-left"><Link to="/_404.html">Westgate</Link></th>
                  <th className="p-2 text-left"><Link to="/_404.html">Alden</Link></th>
                </tr>
              </thead>
              <tbody>
                <tr className="bg-[#123a66]/60">
                  <th className="p-2 text-left">Tuition + Fees ‡</th>
                  <td className="p-2" /><td className="p-2" /><td className="p-2" />
                </tr>
                {[
                  ["In-state", "$18,346 **", "$15,840", "$14,106"],
                  ["Out-of-state", "$63,962 **", "$33,768", "$26,928"],
                  ["Room + Board", "$16,246 **", "N/A", "$13,420 (average)"],
                ].map((row) => (
                  <tr key={row[0]}>
                    <th className="p-2 text-left font-normal">{row[0]}</th>
                    <td className="p-2">{row[1]}</td>
                    <td className="p-2">{row[2]}</td>
                    <td className="p-2">{row[3]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <ul className="mt-4 space-y-1 text-[12px] text-white/60">
            <li>* Corravale University Health (does not include Medical School)</li>
            <li>** 2025-2026 costs for a CAS undergraduate</li>
            <li>‡ Based on a 15-credit semester course load</li>
          </ul>
          <p className="mt-4 text-center text-[12px] text-white/70">Updated January 2026</p>
        </div>
      </section>
    </>
  );
}
