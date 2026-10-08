import { useCallback, useState } from "react";
import { useSnackbar } from "@/components/Snackbar";
import { EditorPage } from "@/pages/EditorPage";
import { IntroPage } from "@/pages/IntroPage";
import { EDITOR_PATH, useRoute } from "@/app/router";
import type { LoadedImage } from "@/app/demos";

export function App() {
  const { path, navigate } = useRoute();
  const snackbar = useSnackbar();
  const [image, setImage] = useState<LoadedImage | null>(null);

  const openEditor = useCallback(
    (next: LoadedImage) => {
      setImage(next);
      document.title = `${next.filename} - Squoosh`;
      navigate(EDITOR_PATH);
    },
    [navigate],
  );

  const backToIntro = useCallback(() => {
    navigate("/");
    document.title = "Squoosh";
  }, [navigate]);

  const onTitle = useCallback((title: string) => {
    document.title = title;
  }, []);

  const isEditor = path === EDITOR_PATH;

  return (
    <>
      {isEditor && image ? (
        <EditorPage
          key={image.url}
          image={image}
          onBack={backToIntro}
          onNotice={snackbar.show}
          onTitle={onTitle}
          onReplace={openEditor}
        />
      ) : (
        <IntroPage onImage={openEditor} onNotice={snackbar.show} />
      )}
      {snackbar.node}
    </>
  );
}
