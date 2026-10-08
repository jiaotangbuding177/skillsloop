<h1 align="center">
  <br>
  📋 TaskFlow
  <br>
</h1>

<h4 align="center">A full-featured Kanban board with native drag-and-drop, full CRUD, and localStorage persistence — React 18 + TypeScript.</h4>

<p align="center">
  <img src="https://img.shields.io/badge/React-18-61dafb?style=flat-square&logo=react&logoColor=white" />
  <img src="https://img.shields.io/badge/TypeScript-5.6-3178c6?style=flat-square&logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/Vite-5.4-646cff?style=flat-square&logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" />
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#project-structure">Structure</a>
</p>

---

## Features

- **Drag and Drop** — Move tasks between columns (To Do → In Progress → Done) using native HTML5 DnD API. No react-dnd, no external DnD library.
- **Full CRUD** — Add, edit, and delete tasks via an animated slide-in modal with form validation.
- **Priority System** — Three levels: 🔴 High, 🟡 Medium, 🟢 Low — color-coded on every card.
- **Tag System** — Tag tasks by category (Frontend, Backend, DevOps, Design, etc.) for quick scanning.
- **Search / Filter** — Real-time search across task titles and tags.
- **localStorage Persistence** — Board state survives page refreshes and browser restarts. Uses a reusable `useLocalStorage` custom hook.
- **Progress Bar** — Visual indicator at the top showing percentage of tasks completed.
- **Dark / Light Mode** — Full theme toggle with CSS custom properties.
- **Accessible Modal** — Uses `aria-modal`, `aria-labelledby`, click-outside-to-close, and keyboard support.

## Tech Stack

| Layer | Technology |
|---|---|
| UI | React 18 (functional components + hooks) |
| Language | TypeScript 5.6 (strict mode) |
| Build | Vite 5.4 |
| Styling | CSS custom properties |
| Drag & Drop | HTML5 native DnD API |
| Persistence | `localStorage` via custom `useLocalStorage` hook |
| State | `useState`, lifted state in App |
| Fonts | Inter (Google Fonts) |

## Getting Started

```bash
# Clone the repo
git clone https://github.com/parthlashkari/taskflow.git
cd taskflow

# Install dependencies
npm install

# Start development server
npm run dev
# → http://localhost:5174

# Type-check without building
npm run type-check

# Production build
npm run build
npm run preview
```

**Requirements:** Node.js 18+ and npm 9+

## Project Structure

```
src/
├── components/
│   ├── KanbanColumn.tsx  # Column with drag-over target and add button
│   ├── TaskCard.tsx      # Draggable card with priority, tag, edit/delete
│   └── TaskModal.tsx     # Add/edit modal with form validation
├── hooks/
│   └── useLocalStorage.ts  # Generic typed hook for localStorage sync
├── types.ts              # Task, Column, Priority, ColumnId types
├── App.tsx               # Board state, drag logic, CRUD handlers
└── App.css               # All styles with dark/light CSS variables
```

## How Drag and Drop Works

Tasks implement the HTML5 `draggable` attribute. On `dragStart`, the task and its source column are stored in state. On `drop`, the task is removed from the source column and appended to the target column — all via immutable state updates with `setColumns`. No external library needed.

```tsx
// Simplified drag logic
function onDragStart(task: Task, fromCol: ColumnId) {
  setDragTask({ task, fromCol });
}

function onDrop(toColId: ColumnId) {
  setColumns(cols => {
    const removed = cols.map(c =>
      c.id === dragTask.fromCol
        ? { ...c, tasks: c.tasks.filter(t => t.id !== dragTask.task.id) }
        : c
    );
    return removed.map(c =>
      c.id === toColId ? { ...c, tasks: [...c.tasks, dragTask.task] } : c
    );
  });
}
```

## License

MIT © [Parth Lashkari](https://github.com/parthlashkari)
