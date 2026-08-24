const MCP = (new URLSearchParams(location.search).get('mcp')) || 'http://localhost:8770';
const GRAFANA = (new URLSearchParams(location.search).get('grafana')) || 'http://localhost:3000';
const $ = (s) => document.querySelector(s);
const TYPE_COLORS = {
  core: '#3b82f6', moc: '#7c3aed', project: '#059669', daily: '#d97706',
  system: '#64748b', note: '#38bdf8', area: '#0ea5e9', resource: '#e11d48',
  archive: '#78716c', doc: '#14b8a6', alert: '#ef4444'
};

let GRAPH = null;        // dados do /graph
let NODE_POS = {};       // id -> [x,y]
let NODE_DEG = {};       // id -> grau

// ---------- Tema claro/escuro (persiste em localStorage) ----------
function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  try { localStorage.setItem('mb_theme', t); } catch (e) {}
}
(function initTheme() {
  let t = 'dark';
  try { t = localStorage.getItem('mb_theme') || 'dark'; } catch (e) {}
  applyTheme(t);
})();
$('#themeBtn').addEventListener('click', () => {
  const cur = document.documentElement.getAttribute('data-theme') || 'dark';
  applyTheme(cur === 'dark' ? 'light' : 'dark');
});

// ---------- Grafo ----------
async function loadGraph() {
  const r = await fetch(`${MCP}/graph?k=3`);
  const g = await r.json();
  GRAPH = g;
  $('#stat-nodes').textContent = g.nodes.length;
  $('#stat-edges').textContent = g.edges.length;
  computeDegrees(g);
  drawGraph(g);
  buildOrphans(g); buildDonut(g); buildBfsSelects(g); buildLegend();
}

function computeDegrees(g) {
  NODE_DEG = {};
  g.edges.forEach(e => {
    NODE_DEG[e.source] = (NODE_DEG[e.source] || 0) + 1;
    NODE_DEG[e.target] = (NODE_DEG[e.target] || 0) + 1;
  });
}

function drawGraph(g) {
  const svg = $('#graph');
  svg.innerHTML = '';
  const W = svg.clientWidth, H = svg.clientHeight;
  const cx = W/2, cy = H/2, R = Math.min(W, H) * 0.42;
  NODE_POS = {};
  g.nodes.forEach((n, i) => {
    const a = (2*Math.PI*i) / g.nodes.length;
    NODE_POS[n.id] = [cx + R*Math.cos(a), cy + R*Math.sin(a)];
  });
  const ns = 'http://www.w3.org/2000/svg';
  g.edges.forEach(e => {
    const [x1,y1] = NODE_POS[e.source] || [cx,cy];
    const [x2,y2] = NODE_POS[e.target] || [cx,cy];
    const line = document.createElementNS(ns, 'line');
    line.setAttribute('x1', x1); line.setAttribute('y1', y1);
    line.setAttribute('x2', x2); line.setAttribute('y2', y2);
    line.setAttribute('class', 'edge');
    line.setAttribute('stroke-width', Math.max(0.5, e.weight * 2));
    line.dataset.s = e.source; line.dataset.t = e.target;
    svg.appendChild(line);
  });
  g.nodes.forEach(n => {
    const [x,y] = NODE_POS[n.id] || [cx,cy];
    const c = document.createElementNS(ns, 'circle');
    c.setAttribute('cx', x); c.setAttribute('cy', y); c.setAttribute('r', 6);
    c.setAttribute('class', 'node ' + (n.type || 'note'));
    c.dataset.id = n.id;
    const t = document.createElementNS(ns, 'text');
    t.setAttribute('x', x+9); t.setAttribute('y', y+4);
    t.setAttribute('fill', 'var(--node-text)'); t.setAttribute('font-size', '10');
    t.textContent = (n.label || n.id).slice(0, 22);
    svg.appendChild(c); svg.appendChild(t);
    c.addEventListener('mouseenter', (ev) => showTip(ev, n, x, y));
    c.addEventListener('mousemove', moveTip);
    c.addEventListener('mouseleave', hideTip);
    c.addEventListener('click', () => focusNode(n.id));
  });
}

// ---------- Card de hover (metadados do no) ----------
const tip = $('#nodeTip');
function showTip(ev, n, x, y) {
  const deg = NODE_DEG[n.id] || 0;
  tip.innerHTML = `<h5>${n.label || n.id}</h5>` +
    `<div class="meta">Tipo: <b>${n.type || 'note'}</b></div>` +
    `<div class="meta">Caminho: ${n.id}</div>` +
    `<div class="meta">Conexões (grau): ${deg}</div>`;
  tip.style.display = 'block';
  moveTip(ev);
}
function moveTip(ev) {
  const pad = 14;
  let x = ev.clientX + pad, y = ev.clientY + pad;
  const r = tip.getBoundingClientRect();
  if (x + r.width > window.innerWidth) x = ev.clientX - r.width - pad;
  if (y + r.height > window.innerHeight) y = ev.clientY - r.height - pad;
  tip.style.left = x + 'px'; tip.style.top = y + 'px';
}
function hideTip() { tip.style.display = 'none'; }

// ---------- Busca + highlight ----------
async function search() {
  const q = $('#q').value.trim();
  if (!q) return;
  const r = await fetch(`${MCP}/search?q=${encodeURIComponent(q)}&k=5`);
  const data = await r.json();
  const items = (data.hits || []).map(x =>
    `<div class="item"><div class="content"><div class="header">${x.path}</div>` +
    `<div class="description">${x.snippet || ''}</div></div></div>`).join('');
  $('#results').innerHTML = items || '<div class="item">sem resultados</div>';
  highlightNode(q);
}
function highlightNode(q) {
  if (!GRAPH) return;
  const hit = GRAPH.nodes.find(n => (n.label || n.id).toLowerCase().includes(q.toLowerCase()));
  document.querySelectorAll('.node.hl').forEach(e => e.classList.remove('hl'));
  if (hit) {
    const c = document.querySelector(`.node[data-id="${CSS.escape(hit.id)}"]`);
    if (c) c.classList.add('hl');
  }
}
$('#searchBtn').addEventListener('click', search);

// ---------- Health + metrics ----------
async function loadMetrics() {
  try {
    const r = await fetch(`${MCP}/metrics`);
    $('#metrics').textContent = await r.text();
    const m = ($('#metrics').textContent.match(/mcp_requests_total (\d+)/) || [])[1];
    if (m) $('#stat-req').textContent = m;
  } catch (e) { $('#metrics').textContent = 'metrics indisponível'; }
}
async function health() {
  try {
    const r = await fetch(`${MCP}/health`);
    const ok = (await r.json()).ok;
    $('#card-health').classList.toggle('is-ok', ok);
    $('#card-health').classList.toggle('is-nok', !ok);
    $('#stat-health').textContent = ok ? 'OK' : 'NOK';
    $('#status').textContent = ok ? `Conectado a ${MCP}` : `Sem resposta de ${MCP}`;
  } catch (e) {
    $('#card-health').classList.add('is-nok');
    $('#stat-health').textContent = 'NOK';
    $('#status').textContent = `Erro: ${e}`;
  }
}

// ---------- Teste de conexao (ping) ----------
async function testConnection(samples = 10) {
  const btn = $('#testConnBtn');
  btn.classList.add('loading', 'disabled');
  $('#c-state').textContent = 'testando…'; $('#c-samples').textContent = '0'; $('#connLog').textContent = '';
  const lat = []; let ok = 0;
  for (let i = 0; i < samples; i++) {
    const t0 = performance.now();
    try {
      const r = await fetch(`${MCP}/health?_=${Date.now()}`, { cache: 'no-store' });
      const dt = performance.now() - t0;
      if (r.ok) { lat.push(dt); ok++; $('#c-samples').textContent = ok; }
      $('#connLog').textContent = `amostra ${i+1}: ${dt.toFixed(1)} ms (${r.ok ? 'ok' : 'falha'})`;
    } catch (e) { $('#connLog').textContent = `amostra ${i+1}: ERRO ${e}`; }
  }
  btn.classList.remove('loading', 'disabled');
  if (!lat.length) { $('#c-state').textContent = 'FALHA'; return; }
  const min = Math.min(...lat), max = Math.max(...lat);
  const avg = lat.reduce((a,b)=>a+b,0) / lat.length;
  const jitter = lat.reduce((a,b)=>a+Math.abs(b-avg),0) / lat.length;
  $('#c-state').textContent = `OK (${ok}/${samples})`;
  $('#c-min').textContent = `${min.toFixed(1)} ms`;
  $('#c-avg').textContent = `${avg.toFixed(1)} ms`;
  $('#c-max').textContent = `${max.toFixed(1)} ms`;
  $('#c-jitter').textContent = `${jitter.toFixed(1)} ms`;
}
$('#testConnBtn').addEventListener('click', () => testConnection(10));

// ---------- Notas Orfas (grau 0 no /graph) ----------
function buildOrphans(g) {
  const orphans = g.nodes.filter(n => (NODE_DEG[n.id] || 0) === 0);
  const box = $('#orphans');
  box.innerHTML = orphans.map(n =>
    `<span class="chip orphan" data-id="${n.id}">${(n.label || n.id).slice(0,28)}</span>`).join('') ||
    '<span class="meta">nenhuma nota orfã</span>';
  $('#orphanCount').textContent = `${orphans.length} de ${g.nodes.length} nós são órfãos (sem links de entrada/saída)`;
  box.querySelectorAll('.chip').forEach(c => c.addEventListener('click', () => focusNode(c.dataset.id)));
}

// ---------- Donut de Tipos ----------
function buildDonut(g) {
  const counts = {};
  g.nodes.forEach(n => { const t = n.type || 'note'; counts[t] = (counts[t] || 0) + 1; });
  const entries = Object.entries(counts).sort((a,b) => b[1]-a[1]);
  const total = g.nodes.length;
  const cv = $('#donut'); const ctx = cv.getContext('2d');
  ctx.clearRect(0,0,cv.width,cv.height);
  let ang = -Math.PI/2;
  const cxv = cv.width/2, cyv = cv.height/2, rad = Math.min(cxv,cyv)-12;
  entries.forEach(([t,c]) => {
    const slice = (c/total) * 2*Math.PI;
    ctx.beginPath(); ctx.moveTo(cxv,cyv);
    ctx.arc(cxv,cyv,rad,ang,ang+slice);
    ctx.closePath(); ctx.fillStyle = TYPE_COLORS[t] || '#888'; ctx.fill();
    ang += slice;
  });
  ctx.beginPath(); ctx.arc(cxv,cyv,rad*0.55,0,2*Math.PI); ctx.fillStyle = 'var(--panel)'; ctx.fill();
  ctx.fillStyle = 'var(--txt)'; ctx.font = 'bold 16px sans-serif'; ctx.textAlign = 'center';
  ctx.fillText(total, cxv, cyv+5);
  const total2 = total;
  $('#donutLegend').innerHTML = entries.map(([t,c]) =>
    `<span class="item"><span class="sw" style="background:${TYPE_COLORS[t]||'#888'}"></span>${t}: ${c} (${Math.round(c/total2*100)}%)</span>`).join('');
}

// ---------- Legenda de Cores ----------
function buildLegend() {
  $('#legend').innerHTML = Object.entries(TYPE_COLORS).map(([t,c]) =>
    `<span class="item"><span class="sw" style="background:${c}"></span>${t}</span>`).join('');
}

// ---------- Modo Foco (ego-grafo: vizinhança de 1o grau) ----------
function focusNode(id) {
  if (!GRAPH) return;
  const neigh = new Set([id]);
  GRAPH.edges.forEach(e => {
    if (e.source === id) neigh.add(e.target);
    if (e.target === id) neigh.add(e.source);
  });
  document.querySelectorAll('.node').forEach(c => {
    c.classList.toggle('dim', !neigh.has(c.dataset.id));
  });
  document.querySelectorAll('.edge').forEach(l => {
    const s = l.dataset.s, t = l.dataset.t;
    l.classList.toggle('dim', !(s === id || t === id));
  });
  $('#status').textContent = `Modo Foco: ${id} (${neigh.size-1} vizinhos)`;
}
$('#focusReset').addEventListener('click', () => {
  document.querySelectorAll('.node.dim, .edge.dim').forEach(e => e.classList.remove('dim'));
  $('#status').textContent = `Conectado a ${MCP}`;
});

// ---------- Caminho A->B (BFS no grafo) ----------
function buildBfsSelects(g) {
  const opts = g.nodes.map(n => `<option value="${n.id}">${(n.label||n.id).slice(0,40)}</option>`).join('');
  $('#bfsA').innerHTML = opts; $('#bfsB').innerHTML = opts;
}
function bfsPath(a, b) {
  if (a === b) return [a];
  const adj = {}; GRAPH.edges.forEach(e => {
    (adj[e.source] = adj[e.source] || []).push(e.target);
    (adj[e.target] = adj[e.target] || []).push(e.source);
  });
  const prev = { [a]: null }; const q = [a];
  while (q.length) {
    const cur = q.shift();
    for (const nx of (adj[cur] || [])) {
      if (!(nx in prev)) { prev[nx] = cur; if (nx === b) { q.length = 0; break; } q.push(nx); }
    }
  }
  if (!(b in prev)) return null;
  const path = []; let c = b; while (c !== null) { path.unshift(c); c = prev[c]; }
  return path;
}
$('#bfsBtn').addEventListener('click', () => {
  const a = $('#bfsA').value, b = $('#bfsB').value;
  const p = bfsPath(a, b);
  document.querySelectorAll('.node.path, .edge.path').forEach(e => e.classList.remove('path'));
  if (!p) { $('#bfsOut').textContent = 'Sem caminho entre as notas.'; return; }
  const set = new Set(p);
  document.querySelectorAll('.node').forEach(c => c.classList.toggle('path', set.has(c.dataset.id)));
  document.querySelectorAll('.edge').forEach(l => {
    if (set.has(l.dataset.s) && set.has(l.dataset.t)) l.classList.add('path');
  });
  $('#bfsOut').textContent = `Caminho (${p.length} nós): ` + p.map(id => (GRAPH.nodes.find(n=>n.id===id)||{}).label||id).join(' → ');
});

// ---------- Heatmap de Atividade (via /activity) ----------
async function loadActivity() {
  try {
    const r = await fetch(`${MCP}/activity`);
    const d = await r.json();
    const by = d.by_date || {};
    const dates = Object.keys(by).sort();
    const box = $('#heat'); box.innerHTML = '';
    if (!dates.length) { $('#heatInfo').textContent = 'Sem notas diárias (20_DAILY_NOTES).'; return; }
    const max = Math.max(...dates.map(dt => by[dt]));
    dates.slice(-60).forEach(dt => {
      const v = by[dt];
      const cell = document.createElement('div');
      cell.className = 'cell';
      const intensity = max ? Math.ceil((v / max) * 4) : 0;
      cell.style.background = intensity ? `var(--accent)` : 'var(--border)';
      cell.style.opacity = intensity ? (0.35 + intensity * 0.16) : 1;
      cell.title = `${dt}: ${v} nota(s)`;
      box.appendChild(cell);
    });
    $('#heatInfo').textContent = `${dates.length} dias com atividade | pico: ${max} notas/dia`;
  } catch (e) { $('#heatInfo').textContent = 'heatmap indisponível'; }
}

// ---------- Governanca (/validate) ----------
async function loadGovernance() {
  try {
    const r = await fetch(`${MCP}/validate`);
    const d = await r.json();
    const ok = d.ok;
    const issues = d.issues || [];
    if (ok) {
      $('#gov').textContent = '✅ Vault íntegro (sem problemas detectados).';
      $('#gov').style.color = 'var(--ok)';
    } else {
      const list = issues.map(i => `• [${i.tipo || '?'}] ${i.path || ''} ${i.msg || ''}`).join('\n');
      $('#gov').textContent = `⚠️ ${issues.length} problema(s) detectado(s):\n` + (list || '(validador não detalhou as ocorrências)');
      $('#gov').style.color = 'var(--nok)';
    }
  } catch (e) { $('#gov').textContent = 'validate indisponível'; }
}
$('#govBtn').addEventListener('click', loadGovernance);

// ---------- Exportar Grafo (SVG / PNG) ----------
function serializeSvg() {
  const svg = $('#graph').cloneNode(true);
  svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  return '<?xml version="1.0" standalone="no"?>\n' + svg.outerHTML;
}
$('#expSvg').addEventListener('click', () => {
  const blob = new Blob([serializeSvg()], { type: 'image/svg+xml' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = 'mega-brain-graph.svg'; a.click(); URL.revokeObjectURL(a.href);
});
$('#expPng').addEventListener('click', () => {
  const svgStr = serializeSvg();
  const img = new Image();
  const svg64 = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgStr)));
  img.onload = () => {
    const cv = document.createElement('canvas');
    cv.width = $('#graph').clientWidth; cv.height = $('#graph').clientHeight;
    cv.getContext('2d').drawImage(img, 0, 0);
    const a = document.createElement('a'); a.href = cv.toDataURL('image/png');
    a.download = 'mega-brain-graph.png'; a.click();
  };
  img.src = svg64;
});

// ---------- Init ----------
$('#grafana').src = GRAFANA;
$('#grafanaUrl').value = GRAFANA;
$('#grafanaLoad').addEventListener('click', () => { $('#grafana').src = $('#grafanaUrl').value; });
health(); loadGraph(); loadMetrics(); loadActivity(); testConnection(5);
setInterval(() => { health(); loadMetrics(); }, 15000);
