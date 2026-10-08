import { Link } from "@/lib/router";

/**
 * Stand-in for the reference's self-contained offline notice. It is shown for
 * destinations that cannot be rendered in the static export — external sites,
 * authenticated services, and backend-only tools.
 */
export function OfflinePage() {
  return (
    <section className="flex min-h-[calc(100vh-260px)] items-center justify-center bg-[#f7f7f7] px-6 py-16">
      <div className="w-full max-w-[420px] text-center text-[#333]">
        <p className="font-cond text-[64px] leading-none text-[#c9ccd0]">404</p>
        <h1 className="mt-3 text-[24px] font-bold text-[#222]">Page Not Available</h1>
        <p className="mt-3 text-[13.5px] leading-relaxed text-[#555]">
          This page could not be downloaded for offline viewing. It may be an external link, a
          backend-dependent feature, or a page that requires authentication.
        </p>
        <div className="mt-5 rounded-[4px] bg-white px-5 py-4 text-left text-[12.5px] leading-relaxed text-[#555] shadow-[0_1px_4px_rgba(0,0,0,0.14)]">
          <strong className="block font-bold text-[#333]">Why am I seeing this?</strong>
          <span className="mt-1 block">
            This site is served as a self-contained offline preview. Some pages cannot be fully
            replicated in offline mode.
          </span>
        </div>
        <div className="mt-6 flex items-center justify-center gap-5 text-[13px]">
          <button
            type="button"
            onClick={() => window.history.back()}
            className="rounded-[4px] bg-navy px-4 py-[7px] text-white hover:bg-navy-panel"
          >
            Go Back
          </button>
          <Link to="/" className="text-[#1a5fa8] hover:underline">
            Home
          </Link>
        </div>
      </div>
    </section>
  );
}
