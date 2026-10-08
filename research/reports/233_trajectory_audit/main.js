const $ = (selector) => document.querySelector(selector);
const parameters = new URLSearchParams(location.search);
const labels = { linux: 'Ubuntu', macos: 'macOS', windows: 'Windows', android: 'Android', web: 'Web' };
// Round decimal percentage ties consistently with the score snapshot.
const percentage = (value) => (Math.round((value + Number.EPSILON) * 10000) / 100).toFixed(2);
const element = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};
function remember(key, value, defaultValue = '') {
  const url = new URL(location.href);
  if (value === defaultValue || value === '') url.searchParams.delete(key);
  else url.searchParams.set(key, value);
  history.replaceState(null, '', url);
}
async function getData(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Unable to load ${url}: ${response.status}`);
  return response.json();
}

function initComparison() {
  const view = $('#compare-view');
  let coverage = 50, pointer = null;
  const setCoverage = (value) => {
    coverage = Math.round(Math.max(0, Math.min(100, value)));
    view.style.setProperty('--compare-position', `${coverage}%`);
    view.setAttribute('aria-valuenow', String(coverage));
    view.setAttribute('aria-valuetext', `${coverage}% reference, ${100 - coverage}% recreation`);
    view.querySelector('.image-label.left').style.opacity = coverage < 10 ? '0' : '1';
    view.querySelector('.image-label.right').style.opacity = coverage > 90 ? '0' : '1';
  };
  const move = (event) => {
    const bounds = view.getBoundingClientRect();
    setCoverage((event.clientX - bounds.left - view.clientLeft) / view.clientWidth * 100);
  };
  view.addEventListener('pointerdown', (event) => {
    if (!event.isPrimary || event.button !== 0) return;
    pointer = event.pointerId;
    view.setPointerCapture(pointer);
    view.focus({ preventScroll: true });
    view.classList.add('is-dragging');
    move(event);
  });
  view.addEventListener('pointermove', (event) => { if (event.pointerId === pointer) move(event); });
  const stop = (event) => {
    if (event.pointerId !== pointer) return;
    pointer = null;
    view.classList.remove('is-dragging');
    if (view.hasPointerCapture(event.pointerId)) view.releasePointerCapture(event.pointerId);
  };
  view.addEventListener('pointerup', (event) => { if (event.pointerId === pointer) move(event); stop(event); });
  view.addEventListener('pointercancel', stop);
  view.addEventListener('lostpointercapture', stop);
  view.addEventListener('keydown', (event) => {
    const values = { ArrowLeft: coverage - 1, ArrowDown: coverage - 1, ArrowRight: coverage + 1, ArrowUp: coverage + 1, PageDown: coverage - 10, PageUp: coverage + 10, Home: 0, End: 100 };
    if (!Object.hasOwn(values, event.key)) return;
    event.preventDefault();
    setCoverage(values[event.key]);
  });
  // Same-test reference and AP evaluation screenshots; full frames, lossless WebP.
  // Source PNG hashes and task provenance are in data/comparison-sources.json.
  const cases = {
    foodtruck: { name: 'Food Truck', model: 'GPT-6 Astra', platform: 'macOS', width: 1920, height: 1080 },
    qdirstat: { name: 'QDirStat', model: 'Claude Opus 5', platform: 'Ubuntu', width: 1157, height: 650 },
    timeplanner: { name: 'TimePlanner', model: 'Claude Opus 5', platform: 'Android', width: 1080, height: 2400 },
    bboxeditor: { name: 'Bounding Box Editor', model: 'Claude Opus 5', platform: 'Windows', width: 1456, height: 813 },
    detox: { name: 'Detox', model: 'GPT-6 Astra', platform: 'Web', width: 1920, referenceHeight: 3640, recreationHeight: 3645 },
  };
  for (const button of document.querySelectorAll('[data-comparison]')) {
    button.addEventListener('click', () => {
      const key = button.dataset.comparison, example = cases[key];
      for (const kind of ['reference', 'recreation']) {
        const image = $(`#compare-${kind}`);
        image.src = `assets/comparisons/${key}_${kind}.webp`;
        $('#compare-full-' + kind).href = image.src;
        image.width = example.width;
        image.height = example[`${kind}Height`] || example.height;
        image.alt = kind === 'reference' ? `Original ${example.name} on ${example.platform}` : `${example.model} recreation of ${example.name}`;
      }
      $('#compare-platform').textContent = example.platform;
      $('#compare-caption').replaceChildren(element('strong', example.name), document.createTextNode(` · ${example.model}`));
      for (const choice of document.querySelectorAll('[data-comparison]')) choice.setAttribute('aria-pressed', String(choice === button));
      setCoverage(50);
    });
  }
}
initComparison();

function initCitation() {
  const button = $('#copy-citation'), code = $('#citation-code'), status = $('#citation-status');
  button.hidden = false;
  let reset;
  button.addEventListener('click', async () => {
    clearTimeout(reset);
    try {
      await navigator.clipboard.writeText(code.textContent + '\n');
      button.textContent = 'Copied';
      status.textContent = 'BibTeX citation copied to clipboard.';
      reset = setTimeout(() => { button.textContent = 'Copy'; }, 2000);
    } catch {
      const selection = window.getSelection(), range = document.createRange();
      code.parentElement.focus({ preventScroll: true });
      range.selectNodeContents(code);
      selection.removeAllRanges(); selection.addRange(range);
      button.textContent = 'Copy';
      status.textContent = 'Copy is unavailable. The citation is selected; use your device’s copy command.';
    }
  });
}
initCitation();

function scoresFor(model, platforms) {
  const channel = (key) => {
    const values = platforms.map((p) => model.scores[p][key]);
    return values.length && values.every((v) => typeof v === 'number' && Number.isFinite(v))
      ? values.reduce((sum, v) => sum + v, 0) / values.length : null;
  };
  const prog = channel('prog'), vlm = channel('vlm');
  return {
    prog, vlm, average: prog === null || vlm === null ? null : (prog + vlm) / 2,
    prog_ge90: channel('prog_ge90'), prog_eq100: channel('prog_eq100'),
  };
}

async function initResults() {
  const data = await getData('data/leaderboard.json');
  const scope = $('#result-scope');
  const search = $('#model-search');
  const common = data.comparison_platforms;
  scope.options[0].textContent = common.length === 5 ? 'Overall' : `Reported mean · ${common.length} of 5 platforms`;
  if ([...scope.options].some((option) => option.value === parameters.get('scope'))) scope.value = parameters.get('scope');
  search.value = parameters.get('model') || '';
  let sortKey = 'average', direction = 'descending';
  function render() {
    const selected = scope.value === 'comparison' ? common : [scope.value];
    const eligible = data.models.filter((model) => model.primary);
    const rows = eligible.map((model) => ({
      model, scores: scoresFor(model, selected),
      cost: Number.isFinite(model.estimated_cost_usd_per_task) && model.estimated_cost_usd_per_task >= 0
        ? model.estimated_cost_usd_per_task : null,
    }));
    // Keep the cost scale stable across search and platform filters. Costs are
    // always the five-platform mean, and Rank remains a benchmark score rank.
    const maxCost = Math.max(0, ...rows.map((row) => row.cost ?? 0));
    const rankingKey = sortKey === 'name' || sortKey === 'cost' ? 'average' : sortKey;
    const ranked = rows.filter((row) => row.scores[rankingKey] !== null).sort((a, b) => b.scores[rankingKey] - a.scores[rankingKey]);
    const ranks = new Map();
    let lastRank = 0, lastValue = null;
    ranked.forEach((row, i) => {
      const value = row.scores[rankingKey];
      if (lastValue === null || Math.abs(value - lastValue) > 1e-12) lastRank = i + 1;
      ranks.set(row.model.id, lastRank); lastValue = value;
    });
    rows.sort((a, b) => {
      if (sortKey === 'name') return a.model.name.localeCompare(b.model.name) * (direction === 'ascending' ? 1 : -1);
      const x = sortKey === 'cost' ? a.cost : a.scores[sortKey];
      const y = sortKey === 'cost' ? b.cost : b.scores[sortKey];
      if (x === null) return y === null ? a.model.name.localeCompare(b.model.name) : 1;
      if (y === null) return -1;
      return (direction === 'ascending' ? x - y : y - x) || a.model.name.localeCompare(b.model.name);
    });
    const query = search.value.trim().toLowerCase();
    const visible = rows.filter(({ model }) => `${model.name} ${model.variant} ${model.effort}`.toLowerCase().includes(query));
    const body = $('#results-body'); body.replaceChildren();
    for (const { model, scores, cost } of visible) {
      const rank = ranks.get(model.id);
      const tr = element('tr', undefined, rank ? '' : 'unranked');
      tr.dataset.modelId = model.id;
      tr.append(element('td', rank || '—', `rank${rank === 1 ? ' leader' : ''}`));
      const nameCell = element('td');
      nameCell.append(element('span', model.name, 'model-name'));
      const description = [model.variant, model.effort && `${model.effort} effort`].filter(Boolean).join(' · ');
      const config = element('span', description, 'model-config');
      config.title = [description, model.context_window && `${model.context_window} context`, model.max_output_tokens && `${model.max_output_tokens} max output`].filter(Boolean).join(' · ');
      nameCell.append(config); tr.append(nameCell);
      for (const key of ['prog', 'vlm', 'average', 'prog_ge90', 'prog_eq100']) {
        const value = scores[key];
        const cell = element('td', undefined, `numeric score${key === 'average' ? ' average-score' : ''}`);
        cell.append(element('span', value === null ? '—' : percentage(value), value === null ? 'score-missing' : ''));
        if (value === null) cell.title = 'Not reported for every selected platform';
        else cell.setAttribute('aria-label', `${percentage(value)} percent`);
        if (key === 'average' && value !== null) {
          const meter = element('span', undefined, 'score-meter'); meter.setAttribute('aria-hidden', 'true');
          const fill = element('span'); fill.style.width = `${value * 100}%`; meter.append(fill); cell.append(meter);
        }
        tr.append(cell);
      }
      const costCell = element('td', undefined, 'numeric cost-cell');
      costCell.append(element('span', cost === null ? '—' : `$${cost.toFixed(2)}`, cost === null ? 'score-missing' : ''));
      costCell.title = cost === null
        ? 'Cost telemetry unavailable'
        : `Five-platform mean standardized API cost per trajectory. Bar scaled linearly to the highest reported cost ($${maxCost.toFixed(2)}).`;
      if (cost !== null) {
        const meter = element('span', undefined, 'cost-meter'); meter.setAttribute('aria-hidden', 'true');
        const fill = element('span'); fill.style.width = `${maxCost > 0 ? cost / maxCost * 100 : 0}%`;
        meter.append(fill); costCell.append(meter);
      }
      tr.append(costCell);
      body.append(tr);
    }
    if (!visible.length) {
      const row = element('tr'), cell = element('td', 'No models match this search.', 'empty-state'); cell.colSpan = 8; row.append(cell); body.append(row);
    }
    for (const button of document.querySelectorAll('[data-sort]')) {
      const active = button.dataset.sort === sortKey;
      button.closest('th').setAttribute('aria-sort', active ? direction : 'none');
      button.querySelector('span').textContent = active ? direction === 'ascending' ? '↑' : '↓' : '↕';
    }
  }
  scope.addEventListener('change', () => { remember('scope', scope.value, 'comparison'); render(); });
  search.addEventListener('input', () => { remember('model', search.value.trim()); render(); });
  for (const button of document.querySelectorAll('[data-sort]')) {
    button.addEventListener('click', () => {
      if (sortKey === button.dataset.sort) direction = direction === 'ascending' ? 'descending' : 'ascending';
      else { sortKey = button.dataset.sort; direction = sortKey === 'name' || sortKey === 'cost' ? 'ascending' : 'descending'; }
      render();
    });
  }
  render();
}

const friendlyNames = {
  'adrienverge-photocollage': 'PhotoCollage', 'aleksey-hoffman-sigma-file-manager': 'Sigma File Manager',
  'bragefuglseth-fretboard': 'Fretboard', 'bragefuglseth-keypunch': 'Keypunch',
  'fabiocolacio-marker': 'Marker', 'clementine-player-clementine': 'Clementine',
  'digimezzo-dopamine': 'Dopamine', 'giuspen-cherrytree': 'CherryTree',
};
function appName(app) {
  const raw = app.label.replace(/^bench50-/, '');
  return friendlyNames[raw] || raw.split(/[-_]/).map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}
function renderReels(apps, open) {
  const section = $('#software-reel');
  const buckets = ['linux', 'windows', 'macos', 'android', 'web'].map((platform) => apps.filter((app) => app.platform === platform));
  const picks = [];
  for (let slot = 0; slot < 10; slot++) {
    for (const bucket of buckets) if (bucket.length) picks.push(bucket[Math.floor(slot * bucket.length / 10)]);
  }
  if (!picks.length) return;
  const rows = [picks.filter((_, i) => i % 2 === 0), picks.filter((_, i) => i % 2 === 1)];
  for (const [index, track] of [...section.querySelectorAll('.reel-track')].entries()) {
    track.style.setProperty('--reel-duration', `${Math.max(100, rows[index].length * 6)}s`);
    for (const duplicate of [false, true]) {
      const group = element('div', undefined, 'reel-set');
      if (duplicate) group.setAttribute('aria-hidden', 'true');
      for (const app of rows[index]) {
        const name = appName(app), platform = labels[app.platform] || app.platform;
        const card = element('button', undefined, `reel-card${app.portrait_frame ? ' portrait-frame' : ''}`);
        card.type = 'button';
        card.setAttribute('aria-label', `View ${name} reference screenshot, ${platform}`);
        card.title = `${name} · ${platform}`;
        if (duplicate) card.tabIndex = -1;
        const image = element('img');
        image.src = app.image; image.alt = ''; image.loading = 'lazy'; image.decoding = 'async';
        image.width = app.width; image.height = app.height;
        const caption = element('span', undefined, 'reel-caption');
        caption.append(element('span', name, 'reel-name'), element('span', platform, 'reel-platform'));
        card.append(image, caption);
        card.addEventListener('click', () => open(app));
        group.append(card);
      }
      track.append(group);
    }
  }
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  section.addEventListener('focusin', (event) => {
    const card = event.target.closest('.reel-card');
    if (!card || card.tabIndex < 0 || !card.matches(':focus-visible') || reducedMotion.matches) return;
    const track = card.closest('.reel-track'), viewport = track.parentElement;
    viewport.scrollLeft = 0;
    const bounds = card.getBoundingClientRect(), frame = viewport.getBoundingClientRect();
    if (bounds.left >= frame.left && bounds.right <= frame.right) return;
    // A keyboard user can reach a card that has already scrolled out of view.
    // Move the paused animation to that card, then resume from its new position.
    const animation = track.getAnimations()[0];
    if (!animation) return;
    const progress = Math.max(0, (bounds.left - track.getBoundingClientRect().left - 14) / (track.scrollWidth / 2));
    const duration = animation.effect.getTiming().duration;
    animation.currentTime = Math.min(duration - 1, duration * (track.classList.contains('reverse') ? 1 - progress : progress));
  });
  const updateMotion = () => {
    if (!reducedMotion.matches) {
      for (const viewport of section.querySelectorAll('.reel-window')) viewport.scrollLeft = 0;
    }
  };
  reducedMotion.addEventListener('change', updateMotion);
  updateMotion();
  section.hidden = false;
}
async function initReel() {
  const data = await getData('data/gallery.json');
  const dialog = $('#image-dialog');
  const close = () => dialog.close();
  dialog.addEventListener('close', () => $('#software-reel').classList.remove('is-modal-open'));
  $('#dialog-close').addEventListener('click', close);
  dialog.addEventListener('click', (event) => { if (event.target === dialog) { const rect = dialog.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) close(); } });
  const open = (app) => {
    $('#dialog-title').textContent = appName(app);
    $('#dialog-platform').textContent = `${labels[app.platform] || app.platform} · Reference`;
    $('#dialog-image').src = app.image;
    $('#dialog-image').alt = `Full reference screenshot of ${appName(app)} on ${labels[app.platform] || app.platform}`;
    $('#software-reel').classList.add('is-modal-open');
    dialog.showModal();
  };
  renderReels(data.apps, open);
}

initResults().catch((error) => {
  console.error(error);
  $('#results-body').replaceChildren();
  const row = element('tr'), cell = element('td', 'Results are temporarily unavailable.', 'empty-state'); cell.colSpan = 8; row.append(cell); $('#results-body').append(row);
});
initReel().catch((error) => {
  console.error(error);
});
