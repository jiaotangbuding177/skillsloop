import { useState } from 'react';
import { cn } from '@/utils/cn';
import Link from '@/components/Link';

const AUDIENCES = [
  { label: 'Prospective Students', to: '/prospective-students/' },
  { label: 'Current Students', to: '/current-students/' },
  { label: 'Faculty & Staff', to: '/faculty-staff/' },
  { label: 'Parents', to: '/parents/' },
  { label: 'Alumni', to: '/alumni/' },
];

const QUICK_LINKS = [
  { label: 'Academic Calendar', to: '/about/facts-figures/' },
  { label: 'Courses', to: '/academics/' },
  { label: 'Directory', to: '/contact/' },
  { label: 'Email', to: '/current-students/' },
  { label: 'Health Email', to: '/health-medicine/' },
  { label: 'Library Catalog', to: '/academics/' },
  { label: 'Maps & Directions', to: '/contact/' },
  { label: 'Schools & Colleges', to: '/schools-colleges/' },
  { label: 'Corravale Access', to: '/current-students/' },
];

const MENU = [
  { label: 'Home', to: '/' },
  { label: 'About', to: '/about/' },
  { label: 'Academics', to: '/academics/' },
  { label: 'Life at Corravale', to: '/life-at-michigan/' },
  { label: 'Athletics', to: '/athletics/' },
  { label: 'Research', to: '/research/' },
  { label: 'Health & Medicine', to: '/health-medicine/' },
  { label: 'Initiatives', to: '/initiatives/' },
  { label: 'Giving', to: '/giving/' },
];

export default function Header({ current }: { current: string }) {
  const [quickOpen, setQuickOpen] = useState(false);

  return (
    <header>
      <div className="bg-cb-blue text-white">
        <a
          href="#content"
          className="absolute left-2 top-2 -translate-y-20 bg-cb-maize px-3 py-1 text-sm font-bold text-cb-blue focus:translate-y-0"
        >
          Skip to main content
        </a>
        <div className="mx-auto flex max-w-[1200px] flex-wrap items-start gap-x-10 gap-y-4 px-4 py-4">
          <h1 className="m-0">
            <Link
              to="/"
              className="font-[system-ui] text-3xl font-bold tracking-tight text-cb-maize"
            >
              Corravale University
            </Link>
          </h1>
          <div className="min-w-[300px] flex-1">
            <div className="flex flex-wrap items-center justify-end gap-4 text-[13px]">
              <Link
                to="/about/"
                className="max-w-[280px] text-right leading-tight text-white/90 underline-offset-2 hover:underline"
              >
                Report Sexual Misconduct, Discrimination, and Bias Concerns
              </Link>
              <form
                className="flex items-center"
                role="search"
                onSubmit={(e) => e.preventDefault()}
              >
                <label htmlFor="site-search" className="sr-only">
                  Search for:
                </label>
                <input
                  id="site-search"
                  type="search"
                  placeholder="Search for:"
                  className="h-8 w-44 border border-white/40 bg-white px-2 text-sm text-cb-blue placeholder:text-neutral-500"
                />
                <button
                  type="submit"
                  className="h-8 bg-cb-maize px-3 text-sm font-bold text-cb-blue"
                >
                  Search
                </button>
              </form>
            </div>
            <div className="mt-3 flex flex-wrap items-start justify-end gap-8">
              <div className="relative">
                <button
                  type="button"
                  aria-expanded={quickOpen}
                  onClick={() => setQuickOpen((v) => !v)}
                  className={cn(
                    'flex items-center gap-2 text-sm font-semibold text-white/90 hover:text-cb-maize',
                    quickOpen && 'text-cb-maize',
                  )}
                >
                  Quick Links
                  <span className="text-[10px]">{quickOpen ? '▲' : '▼'}</span>
                </button>
                {quickOpen && (
                  <ul className="absolute right-0 top-8 z-30 w-56 border border-neutral-200 bg-white py-2 text-sm text-cb-blue shadow-lg">
                    {QUICK_LINKS.map((q) => (
                      <li key={q.label}>
                        <Link
                          to={q.to}
                          className="block px-4 py-1.5 hover:bg-cb-gray hover:underline"
                        >
                          {q.label}
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <nav aria-label="Audiences">
                <ul className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
                  <li className="font-semibold text-white/70">For:</li>
                  {AUDIENCES.map((a) => (
                    <li key={a.label}>
                      <Link
                        to={a.to}
                        className="text-white/90 underline-offset-2 hover:text-cb-maize hover:underline"
                      >
                        {a.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </nav>
            </div>
          </div>
        </div>
      </div>
      <nav
        aria-label="Main Menu"
        className="border-b border-neutral-200 bg-white shadow-sm"
      >
        <ul className="mx-auto flex max-w-[1200px] flex-wrap px-2">
          {MENU.map((m) => {
            const active =
              m.to === '/' ? current === '/' : current.startsWith(m.to);
            return (
              <li key={m.label}>
                <Link
                  to={m.to}
                  className={cn(
                    'block px-4 py-3 text-[15px] font-semibold uppercase tracking-wide',
                    active
                      ? 'border-b-4 border-cb-maize text-cb-blue'
                      : 'text-neutral-700 hover:text-cb-blue',
                  )}
                >
                  {m.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </header>
  );
}
