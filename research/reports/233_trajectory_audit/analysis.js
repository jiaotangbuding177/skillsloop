const SVG_NS = 'http://www.w3.org/2000/svg';
const chartKeys = ['cost_performance', 'features', 'source_growth', 'boundaries', 'resources', 'actions', 'source_size', 'implementation', 'failure_categories'];

const svgNode = (tag, attributes = {}, text = '') => {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attributes)) {
    if (value !== null && value !== undefined) node.setAttribute(key, value);
  }
  if (text) node.textContent = text;
  return node;
};

const htmlNode = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};

const linear = (value, domainMin, domainMax, rangeMin, rangeMax) =>
  rangeMin + (value - domainMin) / (domainMax - domainMin) * (rangeMax - rangeMin);

const logScale = (value, domainMin, domainMax, rangeMin, rangeMax) =>
  linear(Math.log10(value), Math.log10(domainMin), Math.log10(domainMax), rangeMin, rangeMax);

const niceMaximum = (value) => {
  if (!value) return 1;
  const power = 10 ** Math.floor(Math.log10(value));
  const scaled = value / power;
  const nice = scaled <= 1 ? 1 : scaled <= 2 ? 2 : scaled <= 5 ? 5 : 10;
  return nice * power;
};

const concise = (value) => {
  if (Number.isInteger(value)) return value.toFixed(0);
  if (Math.abs(value) >= 100) return value.toFixed(0);
  if (Math.abs(value) >= 10) return value.toFixed(1);
  return value.toFixed(2);
};

function setQuery(key, value, defaultValue = '') {
  const url = new URL(location.href);
  if (!value || value === defaultValue) url.searchParams.delete(key);
  else url.searchParams.set(key, value);
  history.replaceState(null, '', url);
}

function addTitle(svg, title, description) {
  const titleNode = svgNode('title', {}, title);
  const descriptionNode = svgNode('desc', {}, description);
  svg.replaceChildren(titleNode, descriptionNode);
  svg.setAttribute('aria-label', title);
}

function drawNumericAxes(svg, settings) {
  const { left, right, top, bottom, width, height, xTicks, yTicks, x, y,
    xFormat = String, yFormat = String, xTitle = '', yTitle = '' } = settings;
  const plotBottom = height - bottom;
  const plotRight = width - right;
  for (const tick of yTicks) {
    const py = y(tick);
    svg.append(svgNode('line', { x1: left, y1: py, x2: plotRight, y2: py, class: 'analysis-grid' }));
    svg.append(svgNode('text', { x: left - 12, y: py + 4, class: 'analysis-axis-label', 'text-anchor': 'end' }, yFormat(tick)));
  }
  for (const tick of xTicks) {
    const px = x(tick);
    svg.append(svgNode('line', { x1: px, y1: plotBottom, x2: px, y2: plotBottom + 5, class: 'analysis-axis' }));
    svg.append(svgNode('text', { x: px, y: plotBottom + 23, class: 'analysis-axis-label', 'text-anchor': 'middle' }, xFormat(tick)));
  }
  svg.append(svgNode('line', { x1: left, y1: top, x2: left, y2: plotBottom, class: 'analysis-axis' }));
  svg.append(svgNode('line', { x1: left, y1: plotBottom, x2: plotRight, y2: plotBottom, class: 'analysis-axis' }));
  if (xTitle) svg.append(svgNode('text', { x: (left + plotRight) / 2, y: height - 9, class: 'analysis-axis-title', 'text-anchor': 'middle' }, xTitle));
  if (yTitle) svg.append(svgNode('text', { x: 16, y: (top + plotBottom) / 2, class: 'analysis-axis-title', 'text-anchor': 'middle', transform: `rotate(-90 16 ${(top + plotBottom) / 2})` }, yTitle));
}

function addTooltipBehavior(container, tooltip) {
  const place = (mark, event) => {
    tooltip.hidden = false;
    tooltip.textContent = mark.dataset.tip;
    const wrap = container.getBoundingClientRect();
    const markBox = mark.getBoundingClientRect();
    const clientX = event?.clientX ?? markBox.left + markBox.width / 2;
    const clientY = event?.clientY ?? markBox.top;
    const left = Math.max(8, Math.min(container.clientWidth - tooltip.offsetWidth - 8, clientX - wrap.left + 12));
    const top = Math.max(8, clientY - wrap.top - tooltip.offsetHeight - 12);
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
  };
  const hide = () => { tooltip.hidden = true; };
  for (const mark of container.querySelectorAll('[data-tip]')) {
    mark.addEventListener('pointerenter', (event) => place(mark, event));
    mark.addEventListener('pointermove', (event) => place(mark, event));
    mark.addEventListener('pointerleave', hide);
    mark.addEventListener('focus', () => place(mark));
    mark.addEventListener('blur', hide);
  }
}

function createPlot(container, title, { width = 440, height = 300, wide = false } = {}) {
  const panel = htmlNode('section', undefined, `analysis-plot${wide ? ' analysis-plot-wide' : ''}`);
  if (title) panel.append(htmlNode('h4', title));
  const svg = svgNode('svg', {
    viewBox: `0 0 ${width} ${height}`,
    role: 'img',
    preserveAspectRatio: 'xMidYMid meet',
  });
  addTitle(svg, title || 'Interactive paper analysis', 'Focus or hover chart marks to inspect exact aggregate values.');
  panel.append(svg);
  container.append(panel);
  return svg;
}

function yTicks(maximum) {
  return Array.from({ length: 5 }, (_, index) => maximum * index / 4);
}

function renderBars(svg, records, categories, models, metric, unit, divisor = 1, dimensions = {}) {
  const { width = 920, height = 450 } = dimensions;
  const compact = width < 600;
  const margin = { left: compact ? 58 : 76, right: 18, top: 22, bottom: compact ? 54 : 72 };
  const bottom = height - margin.bottom;
  const visible = models.filter((model) => records.some((row) => row.model === model.id));
  const values = records.filter((row) => visible.some((model) => model.id === row.model));
  const maximum = niceMaximum(Math.max(...values.flatMap((row) => [row.mean ?? row.value, ...(row.ci95 || [])])) / divisor * 1.08);
  const y = (value) => linear(value, 0, maximum, bottom, margin.top);
  const step = (width - margin.left - margin.right) / categories.length;
  const groupWidth = Math.min(step * 0.75, 112);
  const barWidth = groupWidth / Math.max(visible.length, 1);
  drawNumericAxes(svg, {
    ...margin, width, height, xTicks: [], yTicks: yTicks(maximum), x: () => 0, y,
    yFormat: concise, yTitle: unit,
  });
  categories.forEach((category, categoryIndex) => {
    const center = margin.left + step * (categoryIndex + 0.5);
    svg.append(svgNode('text', { x: center, y: bottom + 25, class: 'analysis-axis-label', 'text-anchor': 'middle' }, category.label));
    visible.forEach((model, modelIndex) => {
      const row = records.find((item) => item.model === model.id && category.matches(item));
      if (!row) return;
      const rawValue = row.mean ?? row.value;
      const value = rawValue / divisor;
      const x = center - groupWidth / 2 + modelIndex * barWidth + 1;
      const h = Math.max(1, bottom - y(value));
      const interval = row.ci95?.map((number) => number / divisor);
      const detail = interval
        ? `${model.label} · ${category.label}: ${concise(value)} ${unit}; 95% CI ${concise(interval[0])}–${concise(interval[1])}`
        : `${model.label} · ${category.label}: ${concise(value)} ${unit}`;
      const bar = svgNode('rect', {
        x, y: y(value), width: Math.max(2, barWidth - 2), height: h,
        rx: 2, fill: model.color, class: 'analysis-mark analysis-bar', tabindex: 0,
        'data-tip': detail, 'aria-label': detail,
      });
      svg.append(bar);
      if (interval) {
        const cx = x + (barWidth - 2) / 2;
        svg.append(svgNode('line', { x1: cx, y1: y(interval[0]), x2: cx, y2: y(interval[1]), class: 'analysis-error' }));
        svg.append(svgNode('line', { x1: cx - 4, y1: y(interval[0]), x2: cx + 4, y2: y(interval[0]), class: 'analysis-error' }));
        svg.append(svgNode('line', { x1: cx - 4, y1: y(interval[1]), x2: cx + 4, y2: y(interval[1]), class: 'analysis-error' }));
      }
    });
  });
}

function renderFeatures(svg, records, models, metric, dimensions = {}) {
  const { width = 920, height = 450 } = dimensions;
  const compact = width < 600;
  const margin = { left: compact ? 58 : 76, right: 18, top: 22, bottom: compact ? 42 : 72 };
  const bottom = height - margin.bottom;
  const visible = models.filter((model) => records.some((row) => row.model === model.id));
  const values = records.filter((row) => visible.some((model) => model.id === row.model));
  const maximum = niceMaximum(Math.max(...values.flatMap((row) => [row.value, ...row.ci95])) * 1.08);
  const y = (value) => linear(value, 0, maximum, bottom, margin.top);
  const step = (width - margin.left - margin.right) / visible.length;
  drawNumericAxes(svg, {
    ...margin, width, height, xTicks: [], yTicks: yTicks(maximum), x: () => 0, y,
    yFormat: concise, yTitle: metric.unit,
  });
  visible.forEach((model, index) => {
    const row = records.find((item) => item.model === model.id);
    const center = margin.left + step * (index + 0.5);
    const barWidth = Math.min(78, step * 0.48);
    const detail = `${model.label} · ${metric.label}: ${concise(row.value)} ${metric.unit}; 95% CI ${concise(row.ci95[0])}–${concise(row.ci95[1])}`;
    svg.append(svgNode('rect', {
      x: center - barWidth / 2, y: y(row.value), width: barWidth,
      height: Math.max(1, bottom - y(row.value)), rx: 3, fill: model.color,
      class: 'analysis-mark analysis-bar', tabindex: 0, 'data-tip': detail,
      'aria-label': detail,
    }));
    svg.append(svgNode('line', { x1: center, y1: y(row.ci95[0]), x2: center, y2: y(row.ci95[1]), class: 'analysis-error' }));
    svg.append(svgNode('line', { x1: center - 5, y1: y(row.ci95[0]), x2: center + 5, y2: y(row.ci95[0]), class: 'analysis-error' }));
    svg.append(svgNode('line', { x1: center - 5, y1: y(row.ci95[1]), x2: center + 5, y2: y(row.ci95[1]), class: 'analysis-error' }));
    if (!compact) {
      svg.append(svgNode('text', { x: center, y: bottom + 25, class: 'analysis-axis-label', 'text-anchor': 'middle' }, model.label));
    }
  });
}

function renderSourceGrowth(svg, chart, platform, models, platformLabel, dimensions = {}) {
  const { width = 920, height = 450 } = dimensions;
  const margin = { left: width < 600 ? 58 : 72, right: 18, top: 30, bottom: 52 };
  const x = (value) => linear(value, 0, 100, margin.left, width - margin.right);
  const y = (value) => linear(value, 0, 100, height - margin.bottom, margin.top);
  drawNumericAxes(svg, {
    ...margin, width, height, xTicks: [0, 20, 40, 60, 80, 100], yTicks: [0, 25, 50, 75, 100], x, y,
    xFormat: (value) => `${value}%`, yFormat: (value) => `${value}%`,
    xTitle: 'Assistant-turn progress', yTitle: 'Final replayed source',
  });
  for (const model of models) {
    const cell = chart.cells.find((row) => row.platform === platform && row.model === model.id);
    if (!cell) continue;
    const points = chart.progress.map((progress, index) => [x(progress), y(cell.values[index])]);
    const path = points.map(([px, py], index) => `${index ? 'L' : 'M'} ${px.toFixed(2)} ${py.toFixed(2)}`).join(' ');
    svg.append(svgNode('path', { d: path, fill: 'none', stroke: model.color, 'stroke-width': 3, class: 'analysis-series' }));
    points.forEach(([px, py], index) => {
      const detail = `${model.label} · ${platformLabel} · ${chart.progress[index].toFixed(0)}% progress: ${cell.values[index].toFixed(1)}% of final source`;
      svg.append(svgNode('circle', { cx: px, cy: py, r: 8, fill: 'transparent', class: 'analysis-mark analysis-hit', tabindex: 0, 'data-tip': detail, 'aria-label': detail }));
    });
    const markerX = x(cell.first_code);
    const pointsString = `${markerX - 6},${margin.top - 12} ${markerX + 6},${margin.top - 12} ${markerX},${margin.top - 3}`;
    const detail = `${model.label} · median first code at ${cell.first_code.toFixed(1)}% progress`;
    svg.append(svgNode('polygon', { points: pointsString, fill: model.color, class: 'analysis-mark', tabindex: 0, 'data-tip': detail, 'aria-label': detail }));
  }
}

function renderActions(svg, chart, model, modelLabel, dimensions = {}) {
  const { width = 920, height = 450 } = dimensions;
  const margin = { left: width < 600 ? 58 : 72, right: 18, top: 22, bottom: 52 };
  const bottom = height - margin.bottom;
  const row = chart.models.find((item) => item.model === model);
  const centers = row.shares[chart.categories[0].id].map((_, index) => (chart.bins[index] + chart.bins[index + 1]) / 2);
  const x = (value) => linear(value, 0, 100, margin.left, width - margin.right);
  const y = (value) => linear(value, 0, 100, bottom, margin.top);
  drawNumericAxes(svg, {
    ...margin, width, height, xTicks: [0, 20, 40, 60, 80, 100], yTicks: [0, 25, 50, 75, 100], x, y,
    xFormat: (value) => `${value}%`, yFormat: (value) => `${value}%`,
    xTitle: 'Assistant-turn progress', yTitle: 'Share of actions',
  });
  let lower = centers.map(() => 0);
  for (const category of chart.categories) {
    const upper = lower.map((value, index) => value + row.shares[category.id][index]);
    const topPath = centers.map((progress, index) => `${index ? 'L' : 'M'} ${x(progress).toFixed(2)} ${y(upper[index]).toFixed(2)}`).join(' ');
    const bottomPath = centers.slice().reverse().map((progress, reverseIndex) => {
      const index = centers.length - 1 - reverseIndex;
      return `L ${x(progress).toFixed(2)} ${y(lower[index]).toFixed(2)}`;
    }).join(' ');
    svg.append(svgNode('path', { d: `${topPath} ${bottomPath} Z`, fill: category.color, class: 'analysis-area' }));
    lower = upper;
  }
  centers.forEach((progress, index) => {
    const leftEdge = index ? (centers[index - 1] + progress) / 2 : 0;
    const rightEdge = index + 1 < centers.length ? (progress + centers[index + 1]) / 2 : 100;
    const values = chart.categories.map((category) => `${category.label} ${row.shares[category.id][index].toFixed(1)}%`).join(' · ');
    const detail = `${modelLabel} · ${chart.bins[index]}–${chart.bins[index + 1]}% progress · ${values}`;
    svg.append(svgNode('rect', {
      x: x(leftEdge), y: margin.top, width: x(rightEdge) - x(leftEdge), height: bottom - margin.top,
      fill: 'transparent', class: 'analysis-mark analysis-bin-hit', tabindex: 0,
      'data-tip': detail, 'aria-label': detail,
    }));
  });
}

function renderFailure(svg, chart, platform, models, platformLabel, dimensions = {}) {
  const { width = 920, height = 450 } = dimensions;
  const margin = { left: width < 600 ? 126 : 150, right: 18, top: 22, bottom: 52 };
  const categories = chart.categories[platform];
  const x = (value) => linear(value, 0, 100, margin.left, width - margin.right);
  const step = (height - margin.top - margin.bottom) / categories.length;
  const offsets = models.map((_, index) => (index - (models.length - 1) / 2) * 8);
  const y = (index) => margin.top + step * (index + 0.5);
  drawNumericAxes(svg, {
    ...margin, width, height, xTicks: [0, 25, 50, 75, 100], yTicks: [], x,
    y: () => 0, xFormat: (value) => `${value}%`, xTitle: 'Programmatic pass rate',
  });
  categories.forEach((category, index) => {
    const py = y(index);
    svg.append(svgNode('line', { x1: margin.left, y1: py, x2: width - margin.right, y2: py, class: 'analysis-grid' }));
    svg.append(svgNode('text', { x: margin.left - 14, y: py + 4, class: 'analysis-axis-label', 'text-anchor': 'end' }, category.label));
    models.forEach((model) => {
      const row = chart.records.find((record) => record.platform === platform && record.model === model.id && record.category === category.id);
      if (!row) return;
      const modelIndex = models.findIndex((item) => item.id === model.id);
      const value = row.pass_rate * 100;
      const detail = `${model.label} · ${platformLabel} · ${category.label}: ${value.toFixed(1)}%; ${row.tasks} tasks`;
      svg.append(svgNode('circle', {
        cx: x(value), cy: py + offsets[modelIndex], r: 6.5, fill: model.color,
        stroke: '#fff', 'stroke-width': 1.2, class: 'analysis-mark', tabindex: 0,
        'data-tip': detail, 'aria-label': detail,
      }));
    });
  });
}

function renderCostPerformance(svg, chart) {
  const width = 920, height = 450;
  const margin = { left: 78, right: 26, top: 30, bottom: 62 };
  const available = chart.models.filter((model) => model.cost !== null);
  const costStep = 25;
  const maxCost = Math.ceil(Math.max(...available.map((model) => model.cost)) * 1.05 / costStep) * costStep;
  const maxScore = Math.ceil(Math.max(...available.map((model) => model.score)) / 10) * 10;
  const x = (value) => linear(value, 0, maxCost, margin.left, width - margin.right);
  const y = (value) => linear(value, 0, maxScore, height - margin.bottom, margin.top);
  drawNumericAxes(svg, {
    ...margin, width, height,
    xTicks: Array.from({ length: 6 }, (_, index) => maxCost * index / 5),
    yTicks: Array.from({ length: maxScore / 10 + 1 }, (_, index) => index * 10),
    x, y, xFormat: concise, yFormat: (value) => `${value}%`,
    xTitle: 'Mean standardized API cost per trajectory (USD)',
    yTitle: 'Average benchmark score',
  });
  const frontier = available.filter((model) => model.pareto).sort((a, b) => a.cost - b.cost);
  if (frontier.length > 1) {
    const path = frontier.map((model, index) => `${index ? 'L' : 'M'} ${x(model.cost).toFixed(2)} ${y(model.score).toFixed(2)}`).join(' ');
    svg.append(svgNode('path', { d: path, fill: 'none', stroke: '#26364a', 'stroke-width': 2, 'stroke-dasharray': '6 5' }));
  }
  for (const model of available) {
    const detail = `${model.label}: $${model.cost.toFixed(2)} per trajectory · ${model.score.toFixed(2)}% average${model.pareto ? ' · Pareto frontier' : ''}`;
    if (model.pareto) {
      svg.append(svgNode('circle', { cx: x(model.cost), cy: y(model.score), r: 12, fill: 'none', stroke: '#26364a', 'stroke-width': 1.5 }));
    }
    svg.append(svgNode('circle', {
      cx: x(model.cost), cy: y(model.score), r: 7, fill: model.color,
      stroke: '#fff', 'stroke-width': 1.2, class: 'analysis-mark', tabindex: 0,
      'data-tip': detail, 'aria-label': detail,
    }));
  }
}

function renderSourceSize(svg, chart, platform, models, platformLabel, dimensions = {}) {
  const { width = 920, height = 450 } = dimensions;
  const margin = { left: width < 600 ? 62 : 78, right: 18, top: 22, bottom: 58 };
  const bottom = height - margin.bottom;
  const visible = models.map((model) => ({ model, row: chart.series.find((item) => item.platform === platform && item.model === model.id) })).filter((item) => item.row);
  if (platform === 'web') {
    const all = visible.flatMap(({ row }) => row.values).filter((value) => value > 0);
    const min = 10 ** Math.floor(Math.log10(Math.min(...all)));
    const max = 10 ** Math.ceil(Math.log10(Math.max(...all)));
    const ticks = Array.from({ length: Math.log10(max) - Math.log10(min) + 1 }, (_, index) => min * 10 ** index);
    const y = (value) => logScale(value, min, max, bottom, margin.top);
    drawNumericAxes(svg, {
      ...margin, width, height, xTicks: [], yTicks: ticks, x: () => 0, y,
      yFormat: (value) => `10^${Math.round(Math.log10(value))}`,
      yTitle: 'Recreation production LOC',
    });
    const step = (width - margin.left - margin.right) / visible.length;
    visible.forEach(({ model, row }, modelIndex) => {
      const center = margin.left + step * (modelIndex + 0.5);
      row.values.forEach((value, index) => {
        const jitter = ((index * 37) % 23 - 11) * Math.min(2.2, step / 70);
        const detail = `${model.label} · ${platformLabel}: ${value.toLocaleString()} production LOC`;
        svg.append(svgNode('circle', {
          cx: center + jitter, cy: y(value), r: 4.2, fill: model.color, opacity: 0.62,
          stroke: '#fff', 'stroke-width': 0.7, class: 'analysis-mark', tabindex: 0,
          'data-tip': detail, 'aria-label': detail,
        }));
      });
      if (width >= 600) {
        svg.append(svgNode('text', { x: center, y: bottom + 25, class: 'analysis-axis-label', 'text-anchor': 'middle' }, model.label));
      }
    });
    return;
  }
  const points = visible.flatMap(({ row }) => row.points).filter(([xValue, yValue]) => xValue > 0 && yValue > 0);
  const allX = points.map((point) => point[0]);
  const allY = points.map((point) => point[1]);
  const xMin = 10 ** Math.floor(Math.log10(Math.min(...allX)));
  const xMax = 10 ** Math.ceil(Math.log10(Math.max(...allX)));
  const yMin = 10 ** Math.floor(Math.log10(Math.min(...allY)));
  const yMax = 10 ** Math.ceil(Math.log10(Math.max(...allY)));
  const x = (value) => logScale(value, xMin, xMax, margin.left, width - margin.right);
  const y = (value) => logScale(value, yMin, yMax, bottom, margin.top);
  const powers = (min, max) => Array.from({ length: Math.log10(max) - Math.log10(min) + 1 }, (_, index) => min * 10 ** index);
  drawNumericAxes(svg, {
    ...margin, width, height, xTicks: powers(xMin, xMax), yTicks: powers(yMin, yMax), x, y,
    xFormat: (value) => `10^${Math.round(Math.log10(value))}`,
    yFormat: (value) => `10^${Math.round(Math.log10(value))}`,
    xTitle: 'Reference production LOC', yTitle: 'Recreation production LOC',
  });
  const identityMin = Math.max(xMin, yMin), identityMax = Math.min(xMax, yMax);
  svg.append(svgNode('line', { x1: x(identityMin), y1: y(identityMin), x2: x(identityMax), y2: y(identityMax), stroke: '#718096', 'stroke-width': 1.5, 'stroke-dasharray': '6 5' }));
  const summary = chart.summaries[platform];
  if (summary?.slope !== undefined) {
    const start = xMin, end = xMax;
    svg.append(svgNode('line', {
      x1: x(start), y1: y(10 ** summary.intercept * start ** summary.slope),
      x2: x(end), y2: y(10 ** summary.intercept * end ** summary.slope),
      stroke: '#26364a', 'stroke-width': 2,
    }));
  }
  for (const { model, row } of visible) {
    for (const [reference, recreation] of row.points) {
      const detail = `${model.label} · ${platformLabel}: ${reference.toLocaleString()} reference LOC · ${recreation.toLocaleString()} recreation LOC`;
      svg.append(svgNode('circle', {
        cx: x(reference), cy: y(recreation), r: 4.2, fill: 'transparent', stroke: model.color,
        'stroke-width': 1.5, class: 'analysis-mark', tabindex: 0,
        'data-tip': detail, 'aria-label': detail,
      }));
    }
  }
}

function renderFrameworkMatrix(svg, chart, platform, platformLabel, dimensions = {}) {
  const { width = 920, height = 450 } = dimensions;
  const margin = {
    left: width < 600 ? 120 : 165,
    right: 18,
    top: 22,
    bottom: width < 600 ? 86 : 105,
  };
  const rows = chart.flows[platform] || [];
  const totals = (key) => Object.fromEntries([...new Set(rows.map((row) => row[key]))].map((name) => [name, rows.filter((row) => row[key] === name).reduce((sum, row) => sum + row.count, 0)]));
  const referenceTotals = totals('reference'), recreationTotals = totals('recreation');
  const references = Object.keys(referenceTotals).sort((a, b) => referenceTotals[b] - referenceTotals[a]);
  const recreations = Object.keys(recreationTotals).sort((a, b) => recreationTotals[b] - recreationTotals[a]);
  const cellWidth = (width - margin.left - margin.right) / recreations.length;
  const cellHeight = (height - margin.top - margin.bottom) / references.length;
  const maximum = Math.max(...rows.map((row) => row.count));
  const label = (key) => chart.family_labels[key] || key;
  references.forEach((reference, rowIndex) => {
    const cy = margin.top + cellHeight * (rowIndex + 0.5);
    svg.append(svgNode('text', { x: margin.left - 14, y: cy + 4, class: 'analysis-axis-label', 'text-anchor': 'end' }, label(reference)));
    recreations.forEach((recreation, columnIndex) => {
      const item = rows.find((row) => row.reference === reference && row.recreation === recreation);
      const count = item?.count || 0;
      const x = margin.left + columnIndex * cellWidth, y = margin.top + rowIndex * cellHeight;
      const detail = `${platformLabel}: ${label(reference)} → ${label(recreation)} · ${count} recreations`;
      svg.append(svgNode('rect', {
        x: x + 1, y: y + 1, width: cellWidth - 2, height: cellHeight - 2, rx: 3,
        fill: '#3E7CC3', opacity: count ? 0.12 + 0.78 * count / maximum : 0.025,
        class: 'analysis-mark', tabindex: count ? 0 : -1,
        'data-tip': count ? detail : null, 'aria-label': count ? detail : null,
      }));
      if (count) svg.append(svgNode('text', { x: x + cellWidth / 2, y: y + cellHeight / 2 + 4, class: 'analysis-matrix-value', 'text-anchor': 'middle' }, String(count)));
    });
  });
  recreations.forEach((recreation, index) => {
    const x = margin.left + cellWidth * (index + 0.5), y = height - margin.bottom + 16;
    svg.append(svgNode('text', { x, y, class: 'analysis-axis-label', 'text-anchor': 'end', transform: `rotate(-38 ${x} ${y})` }, label(recreation)));
  });
  svg.append(svgNode('text', { x: 18, y: (margin.top + height - margin.bottom) / 2, class: 'analysis-axis-title', 'text-anchor': 'middle', transform: `rotate(-90 18 ${(margin.top + height - margin.bottom) / 2})` }, 'Reference framework'));
  svg.append(svgNode('text', { x: (margin.left + width - margin.right) / 2, y: height - 10, class: 'analysis-axis-title', 'text-anchor': 'middle' }, 'Recreation framework'));
}

function renderCoverage(svg, chart, models, dimensions = {}) {
  const { width = 920, height = 450 } = dimensions;
  const margin = { left: 76, right: 24, top: 30, bottom: 58 };
  const x = (value) => linear(value, 0, 100, margin.left, width - margin.right);
  const y = (value) => linear(value, 0, 100, height - margin.bottom, margin.top);
  drawNumericAxes(svg, {
    ...margin, width, height, xTicks: [0, 20, 40, 60, 80, 100], yTicks: [0, 25, 50, 75, 100], x, y,
    xFormat: (value) => `${value}%`, yFormat: (value) => `${value}%`,
    xTitle: 'Programmatic score threshold', yTitle: 'Applications meeting threshold',
  });
  for (const model of models) {
    const row = chart.coverage.series.find((item) => item.model === model.id);
    if (!row) continue;
    const points = chart.coverage.thresholds.map((threshold, index) => [x(threshold), y(row.values[index])]);
    const path = points.map(([px, py], index) => `${index ? 'L' : 'M'} ${px.toFixed(2)} ${py.toFixed(2)}`).join(' ');
    svg.append(svgNode('path', { d: path, fill: 'none', stroke: model.color, 'stroke-width': 3, class: 'analysis-series' }));
    chart.coverage.thresholds.forEach((threshold, index) => {
      if (threshold % 5) return;
      const value = row.values[index];
      const detail = `${model.label} · score ≥ ${threshold}%: ${value.toFixed(1)}% of applications`;
      svg.append(svgNode('circle', {
        cx: x(threshold), cy: y(value), r: 7, fill: 'transparent',
        class: 'analysis-mark analysis-hit', tabindex: 0,
        'data-tip': detail, 'aria-label': detail,
      }));
    });
  }
}

export async function initAnalysis() {
  const section = document.querySelector('#analysis');
  if (!section) return;
  const response = await fetch('data/analysis.json');
  if (!response.ok) throw new Error(`Unable to load analysis data: ${response.status}`);
  const data = await response.json();
  const tabs = [...document.querySelectorAll('[data-analysis-tab]')];
  const controls = document.querySelector('#analysis-controls');
  const legend = document.querySelector('#analysis-legend');
  const chartWrap = document.querySelector('.analysis-chart-wrap');
  const chart = document.querySelector('#analysis-chart');
  const tooltip = document.querySelector('#analysis-tooltip');
  const heading = document.querySelector('#analysis-chart-title');
  const caption = document.querySelector('#analysis-caption');
  const status = document.querySelector('#analysis-status');
  const params = new URLSearchParams(location.search);
  const state = {
    chart: chartKeys.includes(params.get('analysis')) ? params.get('analysis') : 'cost_performance',
    activeModels: new Set(data.models.map((model) => model.id)),
  };
  const platformLabel = (id) => data.platforms.find((platform) => platform.id === id)?.label || id;
  const modelLabel = (id) => data.models.find((model) => model.id === id)?.label || id;
  const platformCategories = data.platforms.map((platform) => ({
    ...platform,
    matches: (row) => row.platform === platform.id,
  }));

  const renderLegend = (categories = null) => {
    legend.replaceChildren();
    if (categories) {
      for (const category of categories) {
        const item = htmlNode('span', category.label, 'analysis-legend-item');
        item.style.setProperty('--legend-color', category.color);
        legend.append(item);
      }
      return;
    }
    for (const model of data.models) {
      const button = htmlNode('button', model.label, 'analysis-legend-item');
      button.type = 'button';
      button.style.setProperty('--legend-color', model.color);
      button.setAttribute('aria-pressed', String(state.activeModels.has(model.id)));
      button.title = 'Show or hide this model';
      button.addEventListener('click', () => {
        if (state.activeModels.has(model.id) && state.activeModels.size > 1) state.activeModels.delete(model.id);
        else state.activeModels.add(model.id);
        render();
      });
      legend.append(button);
    }
  };

  const render = () => {
    const block = data.charts[state.chart];
    const models = data.models.filter((model) => state.activeModels.has(model.id));
    controls.replaceChildren();
    controls.hidden = true;
    legend.replaceChildren();
    chart.replaceChildren();
    heading.textContent = block.title;
    if (state.chart === 'cost_performance') {
      renderLegend(block.models.filter((model) => model.cost !== null));
      const svg = createPlot(chart, '', { width: 920, height: 450, wide: true });
      renderCostPerformance(svg, block);
      const missing = block.models.filter((model) => model.cost === null).map((model) => model.label).join(', ');
      caption.textContent = `Five-platform score against mean standardized API cost per trajectory. Dashed line marks the Pareto frontier.${missing ? ` Cost unavailable: ${missing}.` : ''}`;
    } else if (state.chart === 'features') {
      renderLegend();
      for (const [index, metric] of block.metrics.entries()) {
        const wide = index === block.metrics.length - 1 && block.metrics.length % 2;
        const width = wide ? 920 : 440;
        const svg = createPlot(chart, metric.label, { width, height: 280, wide });
        renderFeatures(
          svg,
          block.records.filter((row) => row.metric === metric.id),
          models,
          metric,
          { width, height: 280 },
        );
      }
      caption.textContent = 'All five exploration and verification measures. Platform-balanced means with 95% platform-stratified bootstrap intervals.';
    } else if (state.chart === 'source_growth') {
      renderLegend();
      for (const [index, platform] of data.platforms.entries()) {
        const wide = index === data.platforms.length - 1;
        const width = wide ? 920 : 440;
        const svg = createPlot(chart, platform.label, { width, height: 300, wide });
        renderSourceGrowth(
          svg,
          block,
          platform.id,
          models,
          platform.label,
          { width, height: 300 },
        );
      }
      caption.textContent = 'All five platforms. Curves show median replayed source size over normalized assistant-turn progress; triangles mark the median first code-writing turn.';
    } else if (state.chart === 'boundaries') {
      renderLegend();
      for (const metric of block.metrics) {
        const svg = createPlot(chart, metric.label, { height: 280 });
        renderFeatures(
          svg,
          block.records.filter((row) => row.metric === metric.id),
          models,
          metric,
          { width: 440, height: 280 },
        );
      }
      caption.textContent = 'All four evaluation-boundary attempt types. Bars are platform-balanced means per trajectory with 95% platform-stratified bootstrap intervals.';
    } else if (state.chart === 'resources') {
      renderLegend();
      for (const metric of block.metrics) {
        const svg = createPlot(chart, metric.label);
        renderBars(
          svg,
          block.records.filter((row) => row.metric === metric.id),
          platformCategories,
          models,
          metric.id,
          metric.unit,
          metric.divisor,
          { width: 440, height: 300 },
        );
      }
      caption.textContent = 'All four resource measures across all five platforms. Whiskers are 95% bootstrap intervals; cost uses the same 90% cache-hit assumption for every model.';
    } else if (state.chart === 'actions') {
      renderLegend(block.categories);
      for (const row of block.models) {
        const label = modelLabel(row.model);
        const svg = createPlot(chart, label);
        renderActions(svg, block, row.model, label, { width: 440, height: 300 });
      }
      caption.textContent = 'All four analyzed models. Each progress bin sums to 100%; actions are grouped into seven functional categories after trajectory normalization.';
    } else if (state.chart === 'source_size') {
      renderLegend();
      for (const [index, platform] of data.platforms.entries()) {
        const wide = index === data.platforms.length - 1;
        const width = wide ? 920 : 440;
        const svg = createPlot(chart, platform.label, { width, height: 330, wide });
        renderSourceSize(
          svg,
          block,
          platform.id,
          models,
          platform.label,
          { width, height: 330 },
        );
      }
      caption.textContent = 'All five platforms and every available source-size observation. Native panels compare reference and recreation LOC on log scales; Web shows recreation LOC only.';
    } else if (state.chart === 'implementation') {
      const reference = { id: 'reference', label: 'Reference', color: '#9AA4AE' };
      const displayModels = [reference, ...data.models];
      renderLegend(displayModels);
      for (const metric of block.metrics.filter((item) => item.id !== 'frameworks')) {
        const svg = createPlot(chart, metric.label);
        renderBars(
          svg,
          block.records.map((row) => ({ ...row, value: row[metric.id] })),
          platformCategories,
          displayModels,
          metric.id,
          metric.unit,
          1,
          { width: 440, height: 300 },
        );
      }
      const nativePlatforms = data.platforms.filter((item) => ['linux', 'mac', 'windows'].includes(item.id));
      for (const [index, platform] of nativePlatforms.entries()) {
        const wide = index === nativePlatforms.length - 1;
        const width = wide ? 920 : 440;
        const svg = createPlot(chart, `Framework transitions · ${platform.label}`, { width, height: 350, wide });
        renderFrameworkMatrix(svg, block, platform.id, platform.label, { width, height: 350 });
      }
      caption.textContent = 'File structure spans all five platforms; framework-transition matrices show the three native desktop platforms. Web has no local reference-source measurement.';
    } else {
      renderLegend();
      for (const [index, platform] of data.platforms.entries()) {
        const wide = index === data.platforms.length - 1;
        const width = wide ? 920 : 440;
        const svg = createPlot(chart, platform.label, { width, height: 330, wide });
        renderFailure(
          svg,
          block,
          platform.id,
          models,
          platform.label,
          { width, height: 330 },
        );
      }
      const coverageSvg = createPlot(chart, 'Score-threshold coverage', { width: 920, height: 450, wide: true });
      renderCoverage(coverageSvg, block, models);
      caption.textContent = 'All five platform-specific category panels plus the platform-balanced score-threshold coverage curves.';
    }
    document.querySelector('#analysis-panel').setAttribute('aria-labelledby', `analysis-tab-${state.chart}`);
    for (const tab of tabs) {
      const selected = tab.dataset.analysisTab === state.chart;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
    }
    const panelCount = chart.querySelectorAll('.analysis-plot').length;
    status.textContent = `${block.title}: ${panelCount} interactive panels shown.`;
    addTooltipBehavior(chartWrap, tooltip);
  };

  const selectTab = (key, focus = false) => {
    state.chart = key;
    setQuery('analysis', key, 'cost_performance');
    render();
    if (focus) document.querySelector(`[data-analysis-tab="${key}"]`).focus();
  };
  for (const tab of tabs) {
    tab.addEventListener('click', () => selectTab(tab.dataset.analysisTab));
    tab.addEventListener('keydown', (event) => {
      const current = chartKeys.indexOf(state.chart);
      let next = null;
      if (event.key === 'ArrowRight') next = (current + 1) % chartKeys.length;
      if (event.key === 'ArrowLeft') next = (current - 1 + chartKeys.length) % chartKeys.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = chartKeys.length - 1;
      if (next === null) return;
      event.preventDefault();
      selectTab(chartKeys[next], true);
    });
  }
  render();
}

initAnalysis().catch((error) => {
  console.error(error);
  const caption = document.querySelector('#analysis-caption');
  if (caption) caption.textContent = 'Analysis data could not be loaded. Please reload the page.';
});
