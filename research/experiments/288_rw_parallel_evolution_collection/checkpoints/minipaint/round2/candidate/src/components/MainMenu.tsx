import { useEffect, useRef, useState } from "react";
import { MENU } from "@/editor/data";
import type { MenuEntry, MenuLeaf } from "@/editor/data";
import { cn } from "@/utils/cn";

interface Props {
  dispatch: (action: string) => void;
}

function isLeaf(e: MenuEntry): e is MenuLeaf {
  return e !== "separator";
}

export function MainMenu({ dispatch }: Props) {
  const [openId, setOpenId] = useState<string | null>(null);
  const [openSub, setOpenSub] = useState<string | null>(null);
  const ref = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const onDocDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpenId(null);
        setOpenSub(null);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpenId(null);
        setOpenSub(null);
      }
    };
    document.addEventListener("mousedown", onDocDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocDown);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  const runItem = (leaf: MenuLeaf) => {
    if (leaf.sub) return;
    setOpenId(null);
    setOpenSub(null);
    if (leaf.action) dispatch(leaf.action);
  };

  return (
    <nav className="mp-menubar" aria-label="Main Menu" ref={ref}>
      <ul role="menubar">
        {MENU.map((menu) => {
          const open = openId === menu.id;
          return (
            <li key={menu.id} role="none">
              <button
                type="button"
                role="menuitem"
                aria-haspopup="true"
                aria-expanded={open}
                data-open={open}
                className={cn("mp-menu-title", open && "is-open")}
                onClick={() => {
                  setOpenId(open ? null : menu.id);
                  setOpenSub(null);
                }}
                onMouseEnter={() => {
                  if (openId && openId !== menu.id) {
                    setOpenId(menu.id);
                    setOpenSub(null);
                  }
                }}
              >
                {menu.label}
              </button>
              {open && (
                <ul className="mp-dropdown" role="menu" aria-label={menu.label}>
                  {menu.items.map((entry, i) => {
                    if (!isLeaf(entry)) return <li key={`s${i}`} className="mp-menu-sep" role="separator" />;
                    const id = `${menu.id}-${i}`;
                    const hasSub = !!entry.sub;
                    return (
                      <li key={id} role="none" style={{ position: "relative" }}>
                        <button
                          type="button"
                          role="menuitem"
                          aria-haspopup={hasSub || undefined}
                          aria-expanded={hasSub ? openSub === id : undefined}
                          className="mp-menu-item"
                          onClick={() => runItem(entry)}
                          onMouseEnter={() => setOpenSub(hasSub ? id : null)}
                        >
                          <span>{hasSub ? `${entry.label} ` : entry.label}</span>
                          {hasSub ? (
                            <span className="mp-sub-arrow">&gt;</span>
                          ) : entry.shortcut ? (
                            <span className="mp-key">
                              <span className="mp-sr-only">Shortcut Key:</span>
                              {entry.shortcut}
                            </span>
                          ) : null}
                        </button>
                        {hasSub && openSub === id && (
                          <ul className="mp-dropdown mp-dropdown--nested" role="menu" aria-label={`${entry.label} >`}>
                            {entry.sub!.map((sub, j) =>
                              sub === "separator" ? (
                                <li key={`ss${j}`} className="mp-menu-sep" role="separator" />
                              ) : (
                                <li key={`${id}-${j}`} role="none">
                                  <button
                                    type="button"
                                    role="menuitem"
                                    className="mp-menu-item"
                                    onClick={() => runItem(sub as MenuLeaf)}
                                  >
                                    <span>{(sub as MenuLeaf).label}</span>
                                    {(sub as MenuLeaf).shortcut && (
                                      <span className="mp-key">
                                        <span className="mp-sr-only">Shortcut Key:</span>
                                        {(sub as MenuLeaf).shortcut}
                                      </span>
                                    )}
                                  </button>
                                </li>
                              )
                            )}
                          </ul>
                        )}
                      </li>
                    );
                  })}
                </ul>
              )}
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
