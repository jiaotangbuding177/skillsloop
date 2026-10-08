/**
 * Shared navigational and identity data for the Corravale University site.
 * The mega-menu structure mirrors the information architecture exposed by
 * the reference: nine primary sections, each with a panel of nav blocks.
 */

export const MISCONDUCT_LABEL =
  "Report Sexual Misconduct, Discrimination, and Bias Concerns";

export const AUDEINCE_LINKS = [
  { label: "Prospective Students", href: "/prospective-students/" },
  { label: "Current Students", href: "/current-students/" },
  { label: "Faculty & Staff", href: "/faculty-staff/" },
  { label: "Parents", href: "/parents/" },
  { label: "Alumni", href: "/alumni/" },
];

export const QUICK_LINKS = [
  { label: "Academic Calendar", href: "/_404.html" },
  { label: "Courses", href: "/_404.html" },
  { label: "Directory", href: "/_404.html" },
  { label: "Email", href: "/_404.html" },
  { label: "Health Email", href: "/_404.html" },
  { label: "Library Catalog", href: "/_404.html" },
  { label: "Maps & Directions", href: "/_404.html" },
  { label: "Schools & Colleges", href: "/schools-colleges/" },
  { label: "Corravale Access", href: "/_404.html" },
];

export type NavBlock = {
  title: string;
  groups?: { label: string; children: string[] }[];
  links?: { label: string; href: string; note?: string }[];
  paragraphs?: string[];
};

export type MegaSection = {
  label: string;
  href: string;
  blocks: NavBlock[];
  feature?: { img: string; caption: string; ctaLabel: string; ctaHref: string };
};

export const MAIN_MENU: MegaSection[] = [
  {
    label: "About",
    href: "/about/",
    blocks: [
      {
        title: "Facts & History",
        links: [
          { label: "Accreditation", href: "/_404.html" },
          { label: "Annual Report", href: "/_404.html" },
          { label: "Faculty Honors", href: "/_404.html" },
          { label: "Facts & Figures", href: "/facts-figures/" },
          { label: "Famous Alumni", href: "/_404.html" },
          { label: "Health System", href: "/_404.html" },
          { label: "Corravale Almanac", href: "/_404.html" },
          { label: "Mission", href: "/_404.html" },
          { label: "CU Heritage Project", href: "/_404.html" },
        ],
      },
      {
        title: "Academic Units & Campuses",
        groups: [
          {
            label: "All Colleges & Schools",
            children: [
              "Architecture & Urban Planning",
              "Art & Design",
              "Business",
              "Dentistry",
              "Education",
              "Engineering",
              "Environment and Sustainability",
              "Information",
              "Kinesiology",
              "Law",
              "Literature, Science, and the Arts",
              "Medicine",
              "Music, Theatre & Dance",
              "Nursing",
              "Pharmacy",
              "Public Health",
              "Public Policy",
              "Verstead School of Graduate Studies",
              "Social Work",
            ],
          },
        ],
        links: [
          { label: "Health System", href: "/_404.html" },
          { label: "Westhaven Campus", href: "/_404.html" },
          { label: "Rowan Campus", href: "/_404.html" },
        ],
      },
      {
        title: "Leadership & Administration",
        groups: [
          {
            label: "Executive Offices",
            children: [
              "Business and Finance",
              "Communications",
              "Development",
              "General Counsel",
              "Government Relations",
              "Information Technology",
              "Medical Affairs",
              "Provost",
              "Research",
              "Secretary of the University",
              "Student Life",
            ],
          },
        ],
        links: [
          { label: "Board of Regents", href: "/_404.html" },
          { label: "Office of the President", href: "/_404.html" },
          { label: "Office of the Provost", href: "/_404.html" },
        ],
      },
      {
        title: "State & Community",
        links: [
          { label: "Government Relations", href: "/_404.html" },
          { label: "Corporate Relations", href: "/_404.html" },
          { label: "Statewide Research Corridor", href: "/_404.html" },
        ],
      },
      {
        title: "Jobs",
        links: [
          { label: "Job Postings", href: "/_404.html" },
          { label: "Human Resources", href: "/_404.html" },
          { label: "Benefits", href: "/_404.html" },
          { label: "Student Employment", href: "/_404.html" },
          { label: "Career Center", href: "/_404.html" },
        ],
      },
      {
        title: "News & Events",
        links: [
          { label: "Corravale News", href: "/_404.html" },
          { label: "Events Calendar", href: "/_404.html" },
          { label: "Corravale Today", href: "/_404.html", note: "Alumni Magazine" },
          { label: "Corravale Daily", href: "/_404.html", note: "Student Newspaper" },
          {
            label: "The University Record",
            href: "/_404.html",
            note: "News for Faculty & Staff",
          },
          { label: "Key Issues", href: "/_404.html" },
        ],
      },
      {
        title: "Academic, Research & Cultural Initiatives",
        links: [
          { label: "Arts & Culture", href: "/_404.html" },
          { label: "Entrepreneurship & Innovation", href: "/_404.html" },
          { label: "Global Corravale", href: "/_404.html" },
          { label: "Heritage", href: "/_404.html" },
          { label: "Presidential Initiatives & Focus Areas", href: "/_404.html" },
          { label: "Sustainability", href: "/_404.html" },
        ],
      },
      {
        title: "Campus Information",
        links: [
          { label: "Campus Health Update", href: "/_404.html" },
          { label: "Clock Tower Lighting", href: "/_404.html" },
          { label: "Logistics, Transportation & Parking", href: "/_404.html" },
          { label: "Maps & Directions", href: "/_404.html" },
          { label: "Blue Line", href: "/_404.html" },
          { label: "Social Media Directory", href: "/_404.html" },
          { label: "Campus Information Centers", href: "/_404.html" },
          { label: "Art in Public Spaces", href: "/_404.html" },
        ],
      },
      {
        title: "Visit",
        links: [
          { label: "Maps, Directions & Transportation", href: "/_404.html" },
          { label: "Admissions Tours", href: "/_404.html" },
          { label: "Westhaven Convention & Visitors Bureau", href: "/_404.html" },
        ],
        paragraphs: [
          "Few institutions are positioned as we are to grow into something far greater than the sum of our many distinguished schools and centers.",
        ],
      },
    ],
    feature: {
      img: "/media/CampusArch16-about.jpg",
      caption:
        "Few institutions are positioned as we are to grow into something far greater than the sum of our many distinguished schools and centers. It is precisely this capacity to strengthen the communities we serve that defines our truest worth as a university.",
      ctaLabel: "View Our Facts & Figures",
      ctaHref: "/facts-figures/",
    },
  },
  {
    label: "Academics",
    href: "/academics/",
    blocks: [
      {
        title: "Schools, Colleges & Campuses",
        links: [
          { label: "Flagship Schools & Colleges", href: "/_404.html" },
          { label: "Accreditation", href: "/_404.html" },
        ],
      },
      {
        title: "Undergraduate Programs",
        groups: [
          {
            label: "Majors",
            children: [
              "Architecture & City Planning",
              "Art & Design",
              "Commerce",
              "Education",
              "Engineering",
              "Environment & Sustainability",
              "Informatics",
              "Sport Science",
              "Arts, Sciences, and Humanities",
              "Medicine",
              "Music, Dance & Theatre",
              "Nursing",
              "Pharmacy",
              "Public Affairs",
            ],
          },
        ],
        links: [
          { label: "Admissions", href: "/_404.html" },
          { label: "Undergraduate Colleges & Schools", href: "/_404.html" },
          { label: "Innovation & Entrepreneurship", href: "/_404.html" },
          { label: "Learning Networks", href: "/_404.html" },
          { label: "International & Away Programs", href: "/_404.html" },
          { label: "Involvement Opportunities", href: "/_404.html" },
          { label: "Global Corravale Metro Center", href: "/_404.html" },
        ],
      },
      {
        title: "Graduate Programs",
        groups: [
          {
            label: "Innovation & Entrepreneurship",
            children: [
              "Halloran School of Graduate Studies",
              "Architecture & Urban Planning",
              "Art & Design",
              "Business",
              "Dentistry",
              "Education",
              "Engineering",
            ],
          },
        ],
        links: [
          { label: "Fields of Study", href: "/_404.html" },
          { label: "Graduate Schools & Colleges", href: "/_404.html" },
        ],
      },
      {
        title: "Digital & Lifelong Learning",
        links: [
          { label: "Academic Innovation", href: "/_404.html" },
          { label: "Distance Education", href: "/_404.html" },
          { label: "Disclosures", href: "/_404.html" },
          { label: "Executive Education", href: "/_404.html" },
          { label: "Lifelong Learning", href: "/_404.html" },
          { label: "Corravale Online Courses", href: "/_404.html" },
        ],
      },
      {
        title: "Services & Resources",
        links: [
          { label: "Academic Support Services", href: "/_404.html" },
          { label: "Academic Calendar", href: "/_404.html" },
          { label: "First Generation Students", href: "/_404.html" },
          { label: "Computing on Campus", href: "/_404.html" },
          { label: "Arts Course Guide", href: "/_404.html" },
          { label: "Faculty Honors", href: "/_404.html" },
          { label: "Summer Programs", href: "/_404.html" },
          { label: "Summer Programs Directory", href: "/_404.html" },
        ],
      },
      {
        title: "Libraries",
        links: [
          { label: "Corravale Library Catalog", href: "/_404.html" },
          { label: "Search All Branches", href: "/_404.html" },
        ],
      },
    ],
    feature: {
      img: "/media/academics-law.jpg",
      caption:
        "Students attend a lecture on the central quad, where interdisciplinary teaching brings together scholars from across the university's many schools and colleges.",
      ctaLabel: "Explore Academics",
      ctaHref: "/academics/",
    },
  },
  {
    label: "Life at Corravale",
    href: "/life-at-michigan/",
    blocks: [
      {
        title: "Housing & Dining",
        links: [
          { label: "Residence Halls", href: "/_404.html" },
          { label: "Dining Services", href: "/_404.html" },
          { label: "Learning Communities", href: "/_404.html" },
          { label: "Off-Campus Housing", href: "/_404.html" },
        ],
      },
      {
        title: "Get Involved",
        links: [
          { label: "Student Organizations", href: "/_404.html" },
          { label: "Fraternity & Sorority Life", href: "/_404.html" },
          { label: "Leadership Programs", href: "/_404.html" },
          { label: "Volunteer & Service", href: "/_404.html" },
        ],
      },
      {
        title: "Arts & Culture",
        links: [
          { label: "Museums & Galleries", href: "/_404.html" },
          { label: "Theaters & Performance", href: "/_404.html" },
          { label: "Music & Concerts", href: "/_404.html" },
          { label: "Public Art on Campus", href: "/_404.html" },
        ],
      },
      {
        title: "Recreation & Wellness",
        links: [
          { label: "Recreational Sports", href: "/_404.html" },
          { label: "Fitness Centers", href: "/_404.html" },
          { label: "Counseling & Psychological Services", href: "/_404.html" },
          { label: "Health Services", href: "/_404.html" },
        ],
      },
      {
        title: "Getting Around",
        links: [
          { label: "Campus Maps", href: "/_404.html" },
          { label: "Buses & Shuttles", href: "/_404.html" },
          { label: "Parking", href: "/_404.html" },
          { label: "Bike Programs", href: "/_404.html" },
        ],
      },
      {
        title: "Safety & Support",
        links: [
          { label: "Campus Safety", href: "/_404.html" },
          { label: "Dean of Students", href: "/_404.html" },
          { label: "Accessibility Resources", href: "/_404.html" },
          { label: "Multicultural Services", href: "/_404.html" },
        ],
      },
    ],
    feature: {
      img: "/media/lifeatumich-cube.jpg",
      caption:
        "Cyclists coast past the cube sculpture at Founders Plaza, one of the many landmarks that make campus a vibrant place to live and learn.",
      ctaLabel: "Explore Campus Life",
      ctaHref: "/life-at-michigan/",
    },
  },
  {
    label: "Athletics",
    href: "/athletics/",
    blocks: [
      {
        title: "Ravens Athletics",
        links: [
          { label: "Varsity Sports", href: "/_404.html" },
          { label: "Schedules & Results", href: "/_404.html" },
          { label: "Tickets", href: "/_404.html" },
          { label: "Facilities", href: "/_404.html" },
        ],
      },
      {
        title: "Teams",
        links: [
          { label: "Men's Sports", href: "/_404.html" },
          { label: "Women's Sports", href: "/_404.html" },
          { label: "Club Sports", href: "/_404.html" },
        ],
      },
      {
        title: "Rec Sports",
        links: [
          { label: "Intramurals", href: "/_404.html" },
          { label: "Fitness & Wellness", href: "/_404.html" },
          { label: "Sport Clubs", href: "/_404.html" },
        ],
      },
      {
        title: "Support the Ravens",
        links: [
          { label: "Booster Clubs", href: "/_404.html" },
          { label: "Athletic Giving", href: "/_404.html" },
          { label: "Alumni Athletes", href: "/_404.html" },
        ],
      },
      {
        title: "Resources",
        links: [
          { label: "Sports Medicine", href: "/_404.html" },
          { label: "Compliance", href: "/_404.html" },
          { label: "Athletics Staff Directory", href: "/_404.html" },
        ],
      },
    ],
    feature: {
      img: "/media/athletics-vollyball.jpg",
      caption:
        "Corravale Athletics is honored to deliver transformative experiences for student-athletes on and off the field of play.",
      ctaLabel: "Visit Athletics",
      ctaHref: "/athletics/",
    },
  },
  {
    label: "Research",
    href: "/research/",
    blocks: [
      {
        title: "Research Across Campus",
        links: [
          { label: "Overview", href: "/_404.html" },
          { label: "The Corravale Research Scene", href: "/_404.html" },
          { label: "Schools, Colleges and Campuses", href: "/_404.html" },
          { label: "Initiatives", href: "/_404.html" },
          { label: "Research at Corravale", href: "/_404.html" },
          { label: "Student Research", href: "/_404.html" },
          { label: "Research Opportunities", href: "/_404.html" },
        ],
      },
      {
        title: "Research Administration",
        links: [
          { label: "Office of the Vice President for Research", href: "/_404.html" },
          { label: "Office of Research and Sponsored Projects", href: "/_404.html" },
          { label: "Finance — Sponsored Programs", href: "/_404.html" },
          { label: "eResearch", href: "/_404.html" },
        ],
      },
      {
        title: "Resources for Researchers",
        links: [
          { label: "Research Resources Portal", href: "/_404.html" },
          { label: "Funding and Research Development", href: "/_404.html" },
          { label: "Research Administration", href: "/_404.html" },
          { label: "Manage Research", href: "/_404.html" },
          { label: "Compliance and Integrity", href: "/_404.html" },
          { label: "Collaborate and Partner", href: "/_404.html" },
          { label: "Communicate and Disseminate Research", href: "/_404.html" },
        ],
      },
      {
        title: "Innovation Partnerships",
        links: [
          { label: "Center for Economic Impact", href: "/_404.html" },
          { label: "Statewide Innovation Alliance", href: "/_404.html" },
          { label: "Ignite Forward", href: "/_404.html" },
          { label: "Accelerated Clinical Discovery", href: "/_404.html" },
        ],
      },
      {
        title: "Economic Impact",
        links: [
          { label: "Federal Research Reports", href: "/_404.html" },
          { label: "Corravale News — Research", href: "/_404.html" },
          { label: "Research Annual Reports", href: "/_404.html" },
          { label: "CRC Annual Reports", href: "/_404.html" },
        ],
      },
      {
        title: "Schools & Colleges",
        links: [
          { label: "Architecture & Urban Studies", href: "/_404.html" },
          { label: "Arts & Design", href: "/_404.html" },
          { label: "Business", href: "/_404.html" },
          { label: "Dentistry", href: "/_404.html" },
          { label: "Engineering", href: "/_404.html" },
          { label: "Medicine", href: "/_404.html" },
          { label: "Public Health", href: "/_404.html" },
          { label: "Social Work", href: "/_404.html" },
        ],
      },
    ],
    feature: {
      img: "/media/research.jpg",
      caption:
        "Corravale researchers have shown that lightweight organic solar cells can reach 8 percent efficiency.",
      ctaLabel: "Discover Research",
      ctaHref: "/research/",
    },
  },
  {
    label: "Health & Medicine",
    href: "/health-medicine/",
    blocks: [
      {
        title: "Corravale Health",
        links: [
          { label: "About the Health System", href: "/_404.html" },
          { label: "Find a Doctor", href: "/_404.html" },
          { label: "Locations", href: "/_404.html" },
          { label: "Patient Services", href: "/_404.html" },
        ],
      },
      {
        title: "Education",
        links: [
          { label: "Medical School", href: "/_404.html" },
          { label: "Nursing", href: "/_404.html" },
          { label: "Dentistry", href: "/_404.html" },
          { label: "Pharmacy", href: "/_404.html" },
          { label: "Public Health", href: "/_404.html" },
        ],
      },
      {
        title: "Research & Innovation",
        links: [
          { label: "Clinical Trials", href: "/_404.html" },
          { label: "Basic Science Research", href: "/_404.html" },
          { label: "Translational Research", href: "/_404.html" },
        ],
      },
    ],
    feature: {
      img: "/media/healthmed-surgery.jpg",
      caption:
        "The Advanced Simulation Lab lets aspiring physicians rehearse complex procedures in a hands-on, high-fidelity environment.",
      ctaLabel: "Explore Health & Medicine",
      ctaHref: "/health-medicine/",
    },
  },
  {
    label: "Initiatives",
    href: "/initiatives/",
    blocks: [
      {
        title: "University Initiatives",
        links: [
          { label: "Arts & Culture", href: "/_404.html" },
          { label: "Entrepreneurship & Innovation", href: "/_404.html" },
          { label: "Global Corravale", href: "/_404.html" },
          { label: "Heritage", href: "/_404.html" },
        ],
      },
      {
        title: "Focus Areas",
        links: [
          { label: "Presidential Initiatives", href: "/_404.html" },
          { label: "Sustainability", href: "/_404.html" },
          { label: "Community Engagement", href: "/_404.html" },
        ],
      },
      {
        title: "Strategic Partnerships",
        links: [
          { label: "Corporate Relations", href: "/_404.html" },
          { label: "Government Relations", href: "/_404.html" },
          { label: "Statewide Research Corridor", href: "/_404.html" },
        ],
      },
      {
        title: "Get Involved",
        links: [
          { label: "Volunteer", href: "/_404.html" },
          { label: "Give to Corravale", href: "/_404.html" },
          { label: "Partner with Us", href: "/_404.html" },
        ],
      },
    ],
    feature: {
      img: "/media/initiatives-garden.jpg",
      caption:
        "Student volunteers help tend the Campus Farm at the Corravale Arboretum as part of a sustainability initiative.",
      ctaLabel: "View Our Initiatives",
      ctaHref: "/initiatives/",
    },
  },
  {
    label: "Giving",
    href: "/giving/",
    blocks: [
      {
        title: "Ways to Give",
        links: [
          { label: "Make a Gift", href: "/_404.html" },
          { label: "Annual Giving", href: "/_404.html" },
          { label: "Planned Giving", href: "/_404.html" },
          { label: "Corporate & Foundation Giving", href: "/_404.html" },
        ],
      },
      {
        title: "Where to Give",
        links: [
          { label: "Schools & Colleges", href: "/_404.html" },
          { label: "Student Support", href: "/_404.html" },
          { label: "Research & Innovation", href: "/_404.html" },
          { label: "Athletics", href: "/_404.html" },
        ],
      },
      {
        title: "Our Donors",
        links: [
          { label: "Donor Stories", href: "/_404.html" },
          { label: "President's Society", href: "/_404.html" },
          { label: "Recognition Societies", href: "/_404.html" },
        ],
      },
    ],
    feature: {
      img: "/media/giving-thanks.jpg",
      caption:
        "Corravale students write thank-you notes expressing gratitude to the donors whose generosity makes their education possible.",
      ctaLabel: "Support Corravale",
      ctaHref: "/giving/",
    },
  },
];

export const FOOTER_CAMPUSES = [
  { label: "Fairhaven", href: "/" },
  { label: "Westgate", href: "/_404.html" },
  { label: "Alden", href: "/_404.html" },
];

export const FOOTER_SOCIAL = [
  { label: "Streamly", href: "/_404.html", glyph: "f" },
  { label: "Z", href: "/_404.html", glyph: "z" },
  { label: "Skylark", href: "/_404.html", glyph: "s" },
  { label: "Vidcast", href: "/_404.html", glyph: "v" },
  { label: "Photogram", href: "/_404.html", glyph: "p" },
  { label: "Loopit", href: "/_404.html", glyph: "l" },
  { label: "Careerly", href: "/_404.html", glyph: "c" },
];
