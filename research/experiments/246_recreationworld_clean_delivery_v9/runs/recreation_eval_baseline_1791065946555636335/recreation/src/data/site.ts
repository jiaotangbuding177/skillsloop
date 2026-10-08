export interface NavLink {
  label: string;
  to: string;
}

export const mainNav: NavLink[] = [
  { label: "About", to: "/about/" },
  { label: "Academics", to: "/academics/" },
  { label: "Life at Corravale", to: "/life-at-michigan/" },
  { label: "Athletics", to: "/athletics/" },
  { label: "Research", to: "/research/" },
  { label: "Health & Medicine", to: "/health-medicine/" },
  { label: "Initiatives", to: "/initiatives/" },
  { label: "Giving", to: "/giving/" },
];

export const audiences: NavLink[] = [
  { label: "Prospective Students", to: "/prospective-students/" },
  { label: "Current Students", to: "/current-students/" },
  { label: "Faculty & Staff", to: "/faculty-staff/" },
  { label: "Parents", to: "/parents/" },
  { label: "Alumni", to: "/alumni/" },
];

export const quickLinks: NavLink[] = [
  { label: "Academic Calendar", to: "/_404.html" },
  { label: "Courses", to: "/_404.html" },
  { label: "Directory", to: "/_404.html" },
  { label: "Email", to: "/_404.html" },
  { label: "Health Email", to: "/_404.html" },
  { label: "Library Catalog", to: "/_404.html" },
  { label: "Maps & Directions", to: "/_404.html" },
  { label: "Schools & Colleges", to: "/schools-colleges/" },
  { label: "Corravale Access", to: "/_404.html" },
];

export const campuses: NavLink[] = [
  { label: "Fairhaven", to: "/" },
  { label: "Westgate", to: "/_404.html" },
  { label: "Alden", to: "/_404.html" },
];

export const socialFeeds = [
  "Streamly",
  "Z",
  "Skylark",
  "Vidcast",
  "Photogram",
  "Loopit",
  "Careerly",
];

export interface NavBlock {
  title: string;
  items: { label: string; to: string; note?: string }[];
}

/** Homepage "Featured Stories" slides. */
export const featuredStories = [
  {
    title: "Fighting infection and chronic pain with engineered cells",
    body:
      "Engineered cells could enable targeted therapies for infection and chronic pain that don't rely on broad medications, which may trigger new side effects or dangerous immune system reactions in some patients.",
    cta: "Read more about this research",
    to: "/_404.html",
    image: "/_images/6af4de40ef359f0b.jpg",
  },
];

export const infographics = [
  { label: "18 schools and colleges — see the full list", to: "/schools-colleges/" },
  { label: "More than 260 degree programs", to: "/_404.html" },
  { label: "Corravale Research: $1.94 billion in research spending (FY2024)", to: "/_404.html" },
  { label: "95+ Top-Ranked Graduate Programs", to: "/_404.html" },
];

export const homeNews = [
  { label: "Leadership transition update", to: "/_404.html" },
  { label: "Sky survey completes planned 3D map of the cosmos, keeps exploring", to: "/_404.html" },
  { label: "Corravale Minds podcast: Fake flavors and real cravings drive our addiction to processed foods", to: "/_404.html" },
  { label: "Pregnancy-related deaths rose during the pandemic and remain high for many new mothers", to: "/_404.html" },
  { label: "Regional identity is a personal choice, not always tied to family ancestry", to: "/_404.html" },
];

export const homeNewsLinks = [
  { label: "Visit Corravale News", to: "/_404.html" },
  { label: "Explore Key Issues", to: "/_404.html" },
  { label: "Visit the Campus Chronicle", to: "/_404.html" },
];

export const inTheNews = [
  { source: "Northshore Public Radio", label: "As floodwaters rise, aging dams near failure: State needs $1B in repairs", to: "/_404.html" },
  { source: "Gaceta Sur (Spain)", label: "How a breakout artist redefined global fame", to: "/_404.html" },
  { source: "Riverside Post", label: "Commentary: Line-drying clothes and the math of small climate wins", to: "/_404.html" },
  { source: "The Daily", label: "How one cereal maker shaped how the nation ate breakfast", to: "/_404.html" },
];

export const videos = [
  {
    title: "Meet the Incoming University President",
    image: "/_images/1edd5970e96fbddd.jpg",
    alt: "A welcome message from President-elect Marion Halcombe.",
    to: "/_404.html",
  },
  {
    title: "Harnessing Innovation to Renew the American Dream: The Corravale Task Force",
    image: "/_images/4ae7aa5aaab80c54.jpg",
    alt: "Corravale Task Force panel discussion.",
    to: "/_404.html",
  },
  {
    title: "Relocating the Historic Founders",
    image: "/_images/ebf5ca139005cbae.jpg",
    alt: "Corravale University slowly and carefully relocated a piece of history Nov. 22, 2025.",
    to: "/_404.html",
  },
];

export const homeEvents = [
  {
    month: "March",
    day: "17",
    title: "The Corravale Framework for Siting Renewable Energy: Policy, Practice, and Impact",
    location: "Arts and Architecture Hall",
    image: "/_images/2eb6869096259dcd.jpg",
    alt: "The Corravale Model for Siting Renewable Energy",
    to: "/_404.html",
  },
  { month: "Mar", day: "12", title: "SNL: Saturday Night Laughs, a FREE Improv Comedy Show!", to: "/_404.html" },
  { month: "Mar", day: "14", title: "From Lecture Halls to Language Models: Placing GenAI in Learning", to: "/_404.html" },
  { month: "Apr", day: "17", title: "Corravale Careers: A Workshop Series for Life After Graduation", to: "/_404.html" },
  { month: "Apr", day: "17", title: "Green Market: Spring Seedling", to: "/_404.html" },
];

export const academicCalendar = [
  { dates: "Apr 21", label: "Classes end" },
  { dates: "Apr 22, 25-26", label: "Study days" },
  { dates: "Apr 23-30", label: "Examinations" },
  { dates: "May 1-3", label: "Commencement Activities" },
];

export interface GalleryShot {
  src: string;
  alt: string;
  time: string;
}

export const seizeToday: GalleryShot[] = [
  { src: "/_images/fce6e09caf7dc0ec.jpg", alt: "Rare books are researched and restored at the Aldwin Library.", time: "8:35 am" },
  { src: "/_images/45a75e75b4d19937.jpg", alt: "A rare book collection at the Aldwin Library.", time: "8:42 am" },
  { src: "/_images/a94f8862f8518063.jpg", alt: "The Harlan T. Meade Reserve provides research and education opportunities in the natural sciences.", time: "8:32 am" },
  { src: "/_images/bbb53e02d581e77d.jpg", alt: "A researcher working in the Rowe and Delia Marsh Cardiovascular Center.", time: "8:11 am" },
  { src: "/_images/1fd9c15a12cd459f.jpg", alt: "A snowy view of the Law Quad framed by the stone archway.", time: "8:49 am" },
  { src: "/_images/c32660a5f9b9de25.jpg", alt: "A graduate leans into a microphone during a student a cappella set on the lawn before the main stage at the 2024 Spring Commencement ceremony.", time: "8:57 am" },
  { src: "/_images/32027c7f4e323658.jpg", alt: "A graduate in a cap decorated with a Block C made of sequins and gold and slate gemstones waves to someone across the crowd outside Corravale Stadium.", time: "8:02 am" },
  { src: "/_images/07921e76b7569af8.jpg", alt: "A long exposure shot of students strolling past the Homeward sculpture on an early Fall day with North Campus Hall, Alder Hall, and the Merrow Building rising in the background.", time: "8:44 am" },
  { src: "/_images/e6548a7da1e002fc.jpg", alt: "A group of four students wearing backpacks and each wearing matching tee shirts steps out of the tunnel running through West Hall toward the Green.", time: "8:46 am" },
  { src: "/_images/daba8bbd39dfbe1a.jpg", alt: "A machinist at work in the College Scientific Instrument Shop.", time: "8:31 am" },
  { src: "/_images/a76adadafe4a040e.jpg", alt: "A student in a gray sweatshirt writes in a notebook with a yellow pencil at a long table in the Reference Room of the Ashwood Graduate Library.", time: "9:10 am" },
  { src: "/_images/044d154eb1914a4a.jpg", alt: "ROTC cadets work together to hold and unfold a large American flag outside of the Chemistry building near the Green flag pole during an annual Veterans Day flag raising ceremony.", time: "9:02 am" },
  { src: "/_images/6af4de40ef359f0b.jpg", alt: "Students put on face masks for a flu prevention study.", time: "10:15 am" },
  { src: "/_images/87615bec46077916.jpg", alt: "A local artist uses oil pastels to capture the peonies at peak bloom in the R.H. Calder Garden at Brightwood Arboretum.", time: "10:00 am" },
  { src: "/_images/51f64b7f00b7c5b0.jpg", alt: "A professor of applied optics, electrical engineering and computer science holds a chariot posture in his office on the North Ridge campus.", time: "10:10 am" },
  { src: "/_images/983ddfed9ee4bdd4.jpg", alt: "A commuter shields herself from the light drizzle while waiting for her", time: "10:12 am" },
];

export const studentGallery: GalleryShot[] = [
  { src: "/_images/7f8e9a40cd8e7319.jpg", alt: "A student tests a prosthetic foot in the Applied Biomechanics and Control Lab.", time: "7:58 am" },
  { src: "/_images/36c8d4bf4d552978.jpg", alt: "A small group of students sit in the grass on the Central Green.", time: "8:04 am" },
  { src: "/_images/7d2e5d9e21f26e36.jpg", alt: "A student gets ready for a morning class in the sunlit atrium of the Merriston Center.", time: "8:12 am" },
  { src: "/_images/a3bf3e87673f2073.jpg", alt: "Members of the women's tennis team run through an early morning workout.", time: "8:20 am" },
  { src: "/_images/a5cf54c08444dbdc.jpg", alt: "A student worker readies the register for a new day at the Corravale U.", time: "8:31 am" },
  { src: "/_images/09d25592b3019959.jpg", alt: "A research technician working in a laboratory at the Whitfield Cardiovascular Center.", time: "9:05 am" },
  { src: "/_images/3fa3f186d919642b.jpg", alt: "Student musicians pound out rhythms on five gallon buckets during the pre-show.", time: "9:14 am" },
  { src: "/_images/65b119af71e6c236.jpg", alt: "Medical students and residents speak with a patient and her mother during rounds.", time: "9:40 am" },
  { src: "/_images/c342b80512e466ef.jpg", alt: "A group of seven students in Corravale gear smile and pose for a photo.", time: "10:02 am" },
  { src: "/_images/26143309ced199d0.jpg", alt: "A research scientist at the Corravale Herbarium sorts seeds from plant specimens.", time: "10:26 am" },
  { src: "/_images/518ab92f8e42d88b.jpg", alt: "A worker enters the campus Nanofabrication Facility on North Ridge.", time: "10:44 am" },
  { src: "/_images/ada5a7bf1f6e2e2d.jpg", alt: "A toddler enjoys the playroom at the Cranmore Children's Hospital.", time: "11:03 am" },
];

export const contactRows = [
  { dept: "Operators", phone: "734-764-1817" },
  { dept: "Undergraduate Admissions", phone: "734-764-7433" },
  { dept: "Graduate Admissions", phone: "734-764-8129", email: "admissions@corravale.edu" },
  { dept: "Central Information Desk", phone: "734-764-INFO (4636)", email: "info@corravale.edu" },
  { dept: "Aid & Funding", phone: "734-763-6600", email: "financial.aid@corravale.edu" },
  { dept: "Housing & Residence", phone: "734-763-3164", email: "housing@corravale.edu" },
  { dept: "Technology Support Desk", phone: "734-764-HELP (4357)", email: "ithelp@corravale.edu", chat: "Chat with a support agent" },
  { dept: "Web Accessibility", website: "Report a Web Accessibility Issue" },
  { dept: "Corravale News", phone: "734-764-7260" },
  { dept: "Social Media Listings" },
  { dept: "Corravale Health", phone: "734-936-6641" },
];

export const contactLinks = [
  "Find a Department or Unit",
  "Find People on Campus",
  "Request Transcripts",
  "Public Records Requests",
];
