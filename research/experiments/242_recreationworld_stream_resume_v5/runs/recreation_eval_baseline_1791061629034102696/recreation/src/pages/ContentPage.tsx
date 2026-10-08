import AudiencePage, {
  type AudiencePageData,
} from "@/components/AudiencePage";
import pages from "@/data/pages.json";

const PAGES = pages as unknown as Record<string, AudiencePageData>;

export default function ContentPage({ slug }: { slug: string }) {
  const data = PAGES[slug];
  if (!data) return null;
  return <AudiencePage data={data} />;
}
