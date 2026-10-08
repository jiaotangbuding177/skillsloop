import { useCallback, useEffect, useRef, useState } from "react";
import { AddImageIcon } from "@/components/icons";
import { BandWave, EdgeWave } from "@/components/Waves";
import { DEMOS, demoToImage, fileToImage, type LoadedImage } from "@/app/demos";
import githubMark from "@/assets/img/github-mark.svg";
import illoCompress from "@/assets/img/illo-compress.svg";
import illoGrid from "@/assets/img/illo-grid.svg";
import illoPrivacy from "@/assets/img/illo-privacy.svg";
import logoLockup from "@/assets/img/logo-lockup.svg";

type Props = {
  onImage: (image: LoadedImage) => void;
  onNotice: (message: string) => void;
};

type Feature = {
  title: string;
  body: string;
  image: string;
  alt: string;
};

const FEATURES: Feature[] = [
  {
    title: "Small",
    body: "Smaller images mean faster load times. Squoosh can reduce file size and maintain high quality.",
    image: illoCompress,
    alt: "silhouette of a large 1.4 megabyte image shrunk into a smaller 80 kilobyte image",
  },
  {
    title: "Simple",
    body: "Open your image, inspect the differences, then save instantly. Feeling adventurous? Adjust the settings for even smaller files.",
    image: illoGrid,
    alt: "grid of multiple shrunk images displaying various options",
  },
  {
    title: "Secure",
    body: "Worried about privacy? Images never leave your device since Squoosh does all the work locally.",
    image: illoPrivacy,
    alt: "silhouette of a cloud with a 'no' symbol on top",
  },
];

/** Distinct blob outlines that stack up to form the pink drop target. */
const DROP_BLOBS = [
  "M1.0655 -0.0933C1.0617 0.1569 0.9255 0.5855 0.719 0.7455C0.5126 0.9054 0.0854 0.9011 -0.1732 0.8663C-0.4318 0.8315 -0.7244 0.7467 -0.8327 0.5367C-0.9409 0.3267 -0.9541 -0.1346 -0.8228 -0.3939C-0.6914 -0.6533 -0.3055 -0.9591 -0.0447 -1.0194C0.216 -1.0798 0.5567 -0.9104 0.7418 -0.7561C0.9268 -0.6017 1.0693 -0.3436 1.0655 -0.0933Z",
  "M0.8186 -0.0808C0.8215 0.1786 0.6207 0.5735 0.4087 0.7317C0.1967 0.8898 -0.2237 0.9244 -0.4533 0.868C-0.683 0.8116 -0.8785 0.6417 -0.9693 0.3931C-1.06 0.1446 -1.1121 -0.3929 -0.9977 -0.6234C-0.8834 -0.854 -0.515 -0.9567 -0.2835 -0.9903C-0.0519 -1.0238 0.2078 -0.9765 0.3915 -0.8249C0.5752 -0.6734 0.8157 -0.3403 0.8186 -0.0808Z",
  "M0.8088 -0.0138C0.7959 0.2104 0.6439 0.5133 0.4788 0.6536C0.3137 0.794 0.0169 0.859 -0.1818 0.8281C-0.3805 0.7973 -0.6132 0.6495 -0.7134 0.4684C-0.8136 0.2873 -0.8611 -0.059 -0.7829 -0.2585C-0.7048 -0.458 -0.4678 -0.6566 -0.2445 -0.7288C-0.0212 -0.801 0.3811 -0.8107 0.5566 -0.6915C0.7322 -0.5723 0.8218 -0.238 0.8088 -0.0138Z",
  "M1.0186 0.0214C1.0312 0.2713 0.9534 0.6268 0.7745 0.7923C0.5956 0.9579 0.2098 1.089 -0.0547 1.0149C-0.3193 0.9409 -0.6795 0.5872 -0.8127 0.348C-0.9459 0.1089 -0.9446 -0.2142 -0.8539 -0.4199C-0.7632 -0.6255 -0.5272 -0.838 -0.2684 -0.8859C-0.0096 -0.9337 0.4845 -0.8581 0.699 -0.7069C0.9135 -0.5557 1.0061 -0.2285 1.0186 0.0214Z",
];

export function IntroPage({ onImage, onNotice }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [loadingDemo, setLoadingDemo] = useState<string | null>(null);
  const [canInstall, setCanInstall] = useState(true);
  const [dragValid, setDragValid] = useState(false);
  const dragDepth = useRef(0);

  const openFile = useCallback(
    async (file: File | undefined | null) => {
      if (!file) return;
      if (!file.type.startsWith("image/")) {
        onNotice("That doesn't look like an image");
        return;
      }
      const image = await fileToImage(file);
      onImage(image);
    },
    [onImage, onNotice],
  );

  const pickDemo = useCallback(
    async (id: string) => {
      const demo = DEMOS.find((d) => d.id === id);
      if (!demo) return;
      setLoadingDemo(demo.size);
      // Give the badge a beat to render before the editor mounts.
      await new Promise((r) => window.setTimeout(r, 260));
      setLoadingDemo(null);
      onImage(demoToImage(demo));
    },
    [onImage],
  );

  // Clipboard paste support (the "OR Paste" affordance).
  useEffect(() => {
    const onPaste = (event: ClipboardEvent) => {
      const items = event.clipboardData?.items;
      if (!items) return;
      for (const item of items) {
        if (item.type.startsWith("image/")) {
          void openFile(item.getAsFile());
          break;
        }
      }
    };
    document.addEventListener("paste", onPaste);
    return () => document.removeEventListener("paste", onPaste);
  }, [openFile]);

  // Keep the install affordance visible; capture the deferred PWA prompt when
  // the browser offers one so it can be triggered for real.
  const installPrompt = useRef<{ prompt: () => void } | null>(null);
  useEffect(() => {
    const onPrompt = (event: Event) => {
      event.preventDefault();
      installPrompt.current = event as unknown as { prompt: () => void };
      setCanInstall(true);
    };
    window.addEventListener("beforeinstallprompt", onPrompt);
    return () => window.removeEventListener("beforeinstallprompt", onPrompt);
  }, []);

  return (
    <div className="abs-fill intro-view">
      <div
        className={`intro-hero${dragValid ? " drag-valid" : ""}`}
        onDragEnter={(e) => {
          e.preventDefault();
          dragDepth.current += 1;
          setDragValid(true);
        }}
        onDragOver={(e) => e.preventDefault()}
        onDragLeave={() => {
          dragDepth.current -= 1;
          if (dragDepth.current <= 0) setDragValid(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          dragDepth.current = 0;
          setDragValid(false);
          void openFile(e.dataTransfer?.files?.[0]);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="visually-hidden"
          onChange={(e) => {
            void openFile(e.target.files?.[0]);
            e.target.value = "";
          }}
        />

        <h1 className="logo-row">
          <img
            className="logo-mark"
            src={logoLockup}
            alt="Squoosh"
            width={539}
            height={162}
          />
        </h1>

        <div className="drop-zone">
          <svg
            className="drop-blob abs-fill"
            viewBox="-1.25 -1.25 2.5 2.5"
            preserveAspectRatio="xMidYMid slice"
            aria-hidden="true"
          >
            {DROP_BLOBS.map((d, i) => (
              <path key={i} d={d} />
            ))}
          </svg>
          <div className="drop-inner">
            <button
              className="drop-icon-btn plain-btn"
              type="button"
              aria-label="Choose an image"
              onClick={() => inputRef.current?.click()}
            >
              <AddImageIcon />
            </button>
            <div className="drop-hint">
              <span className="drop-word">Drop </span>OR{" "}
              <button
                className="paste-link plain-btn"
                type="button"
                onClick={() => inputRef.current?.click()}
              >
                Paste
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="demos-band">
        <BandWave />
        <div className="demos-pad">
          <p className="demos-heading">
            Or <strong>try one</strong> of these:
          </p>
          <ul className="demo-list">
            {DEMOS.map((demo) => (
              <li key={demo.id}>
                <button
                  className="plain-btn"
                  type="button"
                  aria-label={`${demo.label} ${demo.size}`}
                  onClick={() => void pickDemo(demo.id)}
                >
                  <div className="demo-card">
                    <div className="demo-avatar" style={{ position: "relative" }}>
                      <img src={demo.avatar} alt={demo.label} />
                      {loadingDemo === demo.size && (
                        <div
                          className="abs-fill"
                          style={{
                            background: "rgba(0,0,0,.5)",
                            display: "grid",
                            placeItems: "center",
                          }}
                        >
                          <span
                            className="spinner"
                            style={{ ["--size" as string]: "34px", ["--color" as string]: "#fff" }}
                          />
                        </div>
                      )}
                    </div>
                    <div className="demo-badge">{demo.size}</div>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="band-tail">
        <EdgeWave color="info" amplitude={24} baseline={40} phase={0.7} />
      </div>

      {FEATURES.map((feature) => (
        <section className="info-block" key={feature.title}>
          <div className="info-inner">
            <div className="info-grid">
              <div className="info-copy">
                <h2 className="info-heading">{feature.title}</h2>
                <p className="info-body">{feature.body}</p>
              </div>
              <figure className="info-figure">
                <img src={feature.image} alt={feature.alt} />
              </figure>
            </div>
          </div>
        </section>
      ))}

      <footer className="site-footer">
        <div className="footer-band">
          <EdgeWave color="footer" amplitude={22} baseline={42} phase={1.2} />
          <div className="footer-pad">
            <footer className="footer-links">
              <a
                className="footer-link"
                href="https://github.com/GoogleChromeLabs/squoosh/blob/dev/README.md#privacy"
              >
                Privacy
              </a>
              <a
                className="footer-link with-mark"
                href="https://github.com/GoogleChromeLabs/squoosh"
              >
                <img src={githubMark} alt="" width={10} height={10} />
                Source on Github
              </a>
            </footer>
          </div>
        </div>
      </footer>

      {canInstall && (
        <button
          className="install-btn"
          type="button"
          onClick={() => {
            if (installPrompt.current) {
              installPrompt.current.prompt();
            } else {
              onNotice("Install this page from your browser menu");
            }
          }}
        >
          Install
        </button>
      )}
    </div>
  );
}
