import Link from '@/components/Link';

const SOCIAL = ['Streamly', 'Z', 'Skylark', 'Vidcast', 'Photogram', 'Loopit', 'Careerly'];

export default function Footer() {
  return (
    <footer className="bg-cb-blue text-white">
      <div className="mx-auto max-w-[1200px] px-4 py-10">
        <div className="flex flex-wrap gap-12">
          <div className="min-w-[280px] flex-1">
            <p className="m-0 text-2xl font-bold text-cb-maize">
              <Link to="/">Corravale University</Link>
            </p>
            <nav aria-label="Our Campuses" className="mt-4">
              <ul className="flex gap-5 text-sm">
                <li><Link to="/" className="hover:underline">Fairhaven</Link></li>
                <li><Link to="/about/" className="hover:underline">Westgate</Link></li>
                <li><Link to="/about/" className="hover:underline">Alden</Link></li>
              </ul>
            </nav>
            <ul className="mt-5 space-y-2 text-sm text-white/85">
              <li>
                © 2026{' '}
                <Link to="/about/" className="underline-offset-2 hover:underline">
                  The Board of Regents of Corravale University
                </Link>{' '}
                1240 Larkspur Ave., Fairhaven, MI 48211-1044
              </li>
              <li>
                <Link to="/about/privacy/" className="underline-offset-2 hover:underline">
                  Privacy Notice
                </Link>
              </li>
              <li>
                <span className="text-white/60">Phone</span>{' '}
                <a href="tel:+1-734-764-1817" className="underline-offset-2 hover:underline">
                  +1 (734) 764-1817
                </a>
              </li>
              <li>
                <Link to="/contact/" className="underline-offset-2 hover:underline">
                  Contact us
                </Link>
              </li>
            </ul>
          </div>
          <div className="min-w-[220px]">
            <nav aria-label="Careers">
              <ul className="text-sm">
                <li><Link to="/faculty-staff/" className="hover:underline">Careers</Link></li>
              </ul>
            </nav>
            <nav aria-label="Social Feeds" className="mt-6">
              <ul className="flex flex-wrap gap-4 text-sm">
                {SOCIAL.map((s) => (
                  <li key={s}>
                    <Link to="/alumni/" className="hover:underline">{s}</Link>
                  </li>
                ))}
              </ul>
            </nav>
            <nav aria-label="Regulatory Compliance Requirements" className="mt-8">
              <ul className="flex gap-5">
                <li>
                  <Link
                    to="/about/facts-figures/"
                    className="block border border-white/60 px-4 py-2 text-center leading-tight hover:border-cb-maize"
                  >
                    <span className="block text-[11px] font-bold tracking-[0.2em]">TRANSPARENCY</span>
                    <span className="mt-1 block text-[9px] tracking-[0.15em]">BUDGET &amp; SALARY</span>
                  </Link>
                </li>
                <li>
                  <Link
                    to="/about/facts-figures/"
                    className="block border border-white/60 px-4 py-2 text-center leading-tight hover:border-cb-maize"
                  >
                    <span className="block text-[11px] font-bold tracking-[0.2em]">CAMPUS SAFETY</span>
                  </Link>
                </li>
              </ul>
            </nav>
          </div>
        </div>
      </div>
    </footer>
  );
}
