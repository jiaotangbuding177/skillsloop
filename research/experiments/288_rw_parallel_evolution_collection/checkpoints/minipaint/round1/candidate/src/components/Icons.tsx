import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & { size?: number };

const base = (p: IconProps) => {
  const { size = 17, ...rest } = p;
  return {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.7,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    ...rest,
  };
};

/** Cursor / select object */
export const IconSelect = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M6 3l12 8-5 1.2L10.6 18z" />
  </svg>
);

/** Marquee selection */
export const IconSelection = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M4 8V5.5A1.5 1.5 0 0 1 5.5 4H8M16 4h2.5A1.5 1.5 0 0 1 20 5.5V8M20 16v2.5a1.5 1.5 0 0 1-1.5 1.5H16M8 20H5.5A1.5 1.5 0 0 1 4 18.5V16M11 4h2M11 20h2M4 11v2M20 11v2" />
  </svg>
);

export const IconBrush = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M14 4l6 6-7 7H8l-3 3v-3.5L14 4z" />
    <path d="M11 7l6 6" />
  </svg>
);

export const IconPencil = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M4 20l1-4L16.5 4.5a2.1 2.1 0 0 1 3 3L8 19z" />
    <path d="M15 6l3 3" />
  </svg>
);

export const IconPicker = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M19 3l2 2-3 3-2-2z" />
    <path d="M16 6l2 2-9 9H6v-3z" />
    <path d="M5 20h4" />
  </svg>
);

export const IconErase = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M8 19l-3-3a1.6 1.6 0 0 1 0-2.3L12 6.5a1.6 1.6 0 0 1 2.3 0l4.2 4.2a1.6 1.6 0 0 1 0 2.3L13 19z" />
    <path d="M7 19h13" />
  </svg>
);

export const IconMagicErase = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M13 6l5 5L7 22H4v-3z" />
    <path d="M17 2v3M21 4l-2 2M20 9h3M15 2l-1 2" />
  </svg>
);

export const IconFill = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M6 11l6-6 6 6-6 6z" />
    <path d="M9 8L6 5" />
    <path d="M20 15c1 1.5 1.5 2.3 1.5 3.2A1.5 1.5 0 0 1 18 18.2c0-.9.5-1.7 2-3.2z" />
  </svg>
);

/** shape group default icon */
export const IconShape = (p: IconProps) => (
  <svg {...base(p)}>
    <rect x="3" y="10" width="10" height="10" />
    <circle cx="16" cy="8" r="5" />
  </svg>
);

export const IconMedia = (p: IconProps) => (
  <svg {...base(p)}>
    <rect x="3" y="5" width="18" height="14" rx="1" />
    <circle cx="9" cy="10" r="1.6" />
    <path d="M4 17l5-5 4 4 3-3 4 4" />
  </svg>
);

export const IconText = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M5 5h14M12 5v14M9 19h6" />
  </svg>
);

export const IconGradient = (p: IconProps) => (
  <svg {...base(p)}>
    <rect x="4" y="5" width="16" height="14" rx="1" />
    <path d="M4 16l16-8M4 19l16-8" opacity="0.8" />
  </svg>
);

export const IconClone = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M6 9V6h12v3" />
    <rect x="9" y="3" width="6" height="3" />
    <path d="M7 9h10l1 11H6z" />
  </svg>
);

export const IconCrop = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M6 2v16h16M2 6h16v16" />
  </svg>
);

export const IconBlur = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 3c4 5 6 8 6 11a6 6 0 0 1-12 0c0-3 2-6 6-11z" />
    <path d="M12 9c-1.7 2-2.6 3.4-2.6 4.8a2.6 2.6 0 0 0 5.2 0c0-1.4-.9-2.8-2.6-4.8z" opacity="0.7" />
  </svg>
);

export const IconSharpen = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 3l7 15H5z" />
    <path d="M12 8v6" />
  </svg>
);

export const IconDesaturate = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 3c4 5 6 8 6 11a6 6 0 0 1-12 0c0-3 2-6 6-11z" />
    <path d="M12 3v17a6 6 0 0 0 0-17z" fill="currentColor" stroke="none" />
  </svg>
);

export const IconBulge = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 3v3M12 18v3M3 12h3M18 12h3" />
    <path d="M6 6l2 2M18 6l-2 2M6 18l2-2M18 18l-2-2" />
  </svg>
);

export const IconAnimation = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M10 8.5l6 3.5-6 3.5z" fill="currentColor" />
  </svg>
);

/* ---- shape tools ---- */
export const IconLine = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M4 20L20 4" />
  </svg>
);
export const IconArrow = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M4 20L20 4M20 4h-7M20 4v7" />
  </svg>
);
export const IconRectangle = (p: IconProps) => (
  <svg {...base(p)}>
    <rect x="3.5" y="6" width="17" height="12" />
  </svg>
);
export const IconEllipse = (p: IconProps) => (
  <svg {...base(p)}>
    <ellipse cx="12" cy="12" rx="8.5" ry="6" />
  </svg>
);
export const IconTriangle = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 4l8 16H4z" />
  </svg>
);
export const IconRightTriangle = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M4 4v16h16z" />
  </svg>
);
export const IconRomb = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 3l8 9-8 9-8-9z" />
  </svg>
);
export const IconParallelogram = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M7 6h13l-3 12H4z" />
  </svg>
);
export const IconTrapezoid = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M7 6h10l3 12H4z" />
  </svg>
);
export const IconPlus = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 4v16M4 12h16" />
  </svg>
);
export const IconPentagon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 3l9 6.5-3.4 10.5H6.4L3 9.5z" />
  </svg>
);
export const IconHexagon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M8 3h8l4 9-4 9H8l-4-9z" />
  </svg>
);
export const IconStar = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 3l2.6 6.3 6.4.5-4.9 4.2 1.5 6.5L12 17l-5.6 3.5L7.9 14 3 9.8l6.4-.5z" />
  </svg>
);
export const IconHeart = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 20s-7-4.6-7-9.5A4 4 0 0 1 12 7a4 4 0 0 1 7 3.5C19 15.4 12 20 12 20z" />
  </svg>
);
export const IconCylinder = (p: IconProps) => (
  <svg {...base(p)}>
    <ellipse cx="12" cy="6" rx="7" ry="3" />
    <path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6" />
  </svg>
);
export const IconHuman = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="12" cy="5" r="2.5" />
    <path d="M12 8v7M7 11h10M9 20l3-5 3 5" />
  </svg>
);
export const IconTear = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 3c4 4.5 6 7.3 6 5.5v0a6 6 0 0 1-12 0C6 10.3 8 7.5 12 3z" />
    <path d="M12 7v13" />
  </svg>
);
export const IconCog = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="3" />
    <path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" />
  </svg>
);
export const IconBezier = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M4 20C4 10 20 14 20 4" />
    <circle cx="4" cy="20" r="1.6" />
    <circle cx="20" cy="4" r="1.6" />
  </svg>
);
export const IconMoon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5z" />
  </svg>
);
export const IconCallout = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M4 5h16v11H10l-4 4v-4H4z" />
  </svg>
);
export const IconPolygon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 3l7 4.5-2.5 9h-9L5 7.5z" />
  </svg>
);

/* ---- UI icons ---- */
export const IconPlusThin = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 5v14M5 12h14" />
  </svg>
);

export const IconChevronUp = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M5 15l7-7 7 7" />
  </svg>
);

export const IconMenuToggle = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M4 7h16M4 12h16M4 17h16" />
  </svg>
);

export const IconUndo = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M9 7L4 12l5 5" />
    <path d="M4 12h10a6 6 0 0 1 0 12h-2" />
  </svg>
);

export const SHAPE_TOOL_ICONS: Record<string, (p: IconProps) => React.ReactElement> = {
  line: IconLine,
  arrow: IconArrow,
  rectangle: IconRectangle,
  ellipse: IconEllipse,
  triangle: IconTriangle,
  right_triangle: IconRightTriangle,
  romb: IconRomb,
  parallelogram: IconParallelogram,
  trapezoid: IconTrapezoid,
  plus: IconPlus,
  pentagon: IconPentagon,
  hexagon: IconHexagon,
  star: IconStar,
  heart: IconHeart,
  cylinder: IconCylinder,
  human: IconHuman,
  tear: IconTear,
  cog: IconCog,
  bezier_curve: IconBezier,
  moon: IconMoon,
  callout: IconCallout,
  polygon: IconPolygon,
};

export const TOOL_ICONS: Record<string, (p: IconProps) => React.ReactElement> = {
  select: IconSelect,
  selection: IconSelection,
  brush: IconBrush,
  pencil: IconPencil,
  pick_color: IconPicker,
  erase: IconErase,
  magic_erase: IconMagicErase,
  fill: IconFill,
  shape: IconShape,
  media: IconMedia,
  text: IconText,
  gradient: IconGradient,
  clone: IconClone,
  crop: IconCrop,
  blur: IconBlur,
  sharpen: IconSharpen,
  desaturate: IconDesaturate,
  bulge_pinch: IconBulge,
  animation: IconAnimation,
};

export const SHAPE_TOOL_DEFS: { id: string; title: string }[] = [
  { id: "line", title: "Line" },
  { id: "arrow", title: "Arrow" },
  { id: "rectangle", title: "Rectangle" },
  { id: "ellipse", title: "Ellipse" },
  { id: "triangle", title: "Triangle" },
  { id: "right_triangle", title: "Right triangle" },
  { id: "romb", title: "Romb" },
  { id: "parallelogram", title: "Parallelogram" },
  { id: "trapezoid", title: "Trapezoid" },
  { id: "plus", title: "Plus" },
  { id: "pentagon", title: "Pentagon" },
  { id: "hexagon", title: "Hexagon" },
  { id: "star", title: "Star" },
  { id: "heart", title: "Heart" },
  { id: "cylinder", title: "Cylinder" },
  { id: "human", title: "Human" },
  { id: "tear", title: "Tear" },
  { id: "cog", title: "Cog" },
  { id: "bezier_curve", title: "Bezier curve" },
  { id: "moon", title: "Moon" },
  { id: "callout", title: "Callout" },
  { id: "polygon", title: "Polygon" },
];
