const state = { run: null, timer: null, selectedArtifact: null };

const $ = (id) => document.getElementById(id);

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}

function pretty(value) {
  if (value === null || value === undefined || value === '') return '—';
  return escapeHtml(value).replace(/\n/g, '<br>');
}

function statusClass(status) {
  if (['shipped', 'approved', 'passed'].includes(status)) return 'success';
  if (['failed', 'blocked', 'veto'].includes(status)) return 'danger';
  if (['awaiting_human', 'pending', 'warning'].includes(status)) return 'warning';
  if (['planning', 'implementing', 'reviewing', 'revising'].includes(status)) return 'active';
  return '';
}

function focusEvidence() {
  document.getElementById('room-trace')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function render() {
  const run = state.run;
  if (!run || run.status === 'idle') {
    $('run-status').textContent = 'IDLE';
    $('run-status').className = 'status-pill idle';
    $('metric-state').textContent = 'IDLE';
    return;
  }
  const metrics = run.metrics || {};
  const status = run.status || 'queued';
  const label = status.replaceAll('_', ' ').toUpperCase();
  $('run-status').textContent = label;
  $('run-status').className = `status-pill ${statusClass(status)}`;
  $('connection-badge').textContent = 'LOCAL REHEARSAL';
  $('connection-badge').className = 'badge muted';
  $('metric-state').textContent = label;
  $('metric-run-id').textContent = run.id;
  $('metric-attempts').textContent = metrics.patch_attempts ?? 0;
  $('metric-blocked').textContent = metrics.blocked_checks ?? 0;
  $('metric-gate').textContent = (run.human_gate || '—').replaceAll('_', ' ').toUpperCase();
  $('metric-elapsed').textContent = `${metrics.elapsed_ms || 0} ms in the factory trace`;
  $('hero-public').textContent = metrics.public_tests || '—';
  $('hero-sealed').textContent = metrics.sealed_tests || '—';
  const progress = status === 'shipped' ? 100 : status === 'awaiting_human' ? 92 : status === 'failed' ? 100 : Math.min(90, (run.events || []).length * 8);
  $('hero-progress').style.width = `${progress}%`;
  renderAgents(run.agents || []);
  renderEvents(run.events || []);
  renderArtifacts(run.artifacts || {});
  renderGate(run);
}

function renderAgents(agents) {
  $('agent-grid').innerHTML = agents.map((agent) => `<article class="agent-card ${escapeHtml(agent.status)}"><span class="agent-role">${pretty(agent.role)}</span><h3>${pretty(agent.name)}</h3><div class="agent-capability">${pretty(agent.capability)}</div><div class="agent-status">${pretty(agent.status)}</div></article>`).join('');
}

function renderEvents(events) {
  $('event-count').textContent = `${events.length} event${events.length === 1 ? '' : 's'}`;
  if (!events.length) {
    $('event-stream').innerHTML = '<div class="empty-state">Run the demo to open the factory room.</div>';
    return;
  }
  $('event-stream').innerHTML = events.map((event) => `<div class="event ${escapeHtml(event.level)}"><div class="event-meta">${pretty(event.actor)}<br>${pretty(event.kind)}</div><div class="event-message"><strong>${pretty(event.actor)}</strong> ${pretty(event.message)}${event.recipient ? ` <span class="recipient">→ ${pretty(event.recipient)}</span>` : ''}${event.execution ? '<span class="execution">tool/event</span>' : ''}</div></div>`).join('');
  const stream = $('event-stream');
  stream.scrollTop = stream.scrollHeight;
}

function renderArtifacts(artifacts) {
  const entries = Object.values(artifacts);
  $('artifact-count').textContent = `${entries.length} artifact${entries.length === 1 ? '' : 's'}`;
  if (!entries.length) {
    $('artifact-list').innerHTML = '<div class="empty-state">Plans, diffs, and verifier reports appear here.</div>';
    $('artifact-detail').textContent = 'Select an artifact to inspect its evidence.';
    return;
  }
  $('artifact-list').innerHTML = entries.map((artifact) => `<div class="artifact${state.selectedArtifact === artifact.name ? ' selected' : ''}" data-artifact="${escapeHtml(artifact.name)}"><div><strong>${pretty(artifact.name)}</strong><small>${pretty(artifact.description)}</small></div><span class="artifact-kind">${pretty(artifact.kind)}</span></div>`).join('');
  document.querySelectorAll('.artifact').forEach((element) => element.addEventListener('click', () => {
    state.selectedArtifact = element.dataset.artifact;
    renderArtifacts(artifacts);
  }));
  const selected = artifacts[state.selectedArtifact] || entries[0];
  $('artifact-detail').textContent = selected.content || 'No content recorded.';
}

function renderGate(run) {
  const ready = run.status === 'awaiting_human' || run.status === 'shipped';
  $('gate-card').className = `gate-card${ready ? ' ready' : ''}`;
  $('gate-title').textContent = run.status === 'shipped' ? 'Promotion approved' : ready ? 'Verified case is waiting for approval' : 'Waiting for a verified case';
  $('gate-copy').textContent = run.status === 'shipped' ? 'The Human Owner approved the evidence packet.' : 'The Release Critic can recommend promotion. Only the Human Owner can approve it.';
  $('approve').disabled = run.status !== 'awaiting_human';
}

async function request(path, options = {}) {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || 'Request failed');
  return payload;
}

async function startRun() {
  $('run-demo').disabled = true;
  $('run-demo-secondary').disabled = true;
  try {
    state.selectedArtifact = null;
    state.run = await request('/api/run', { method: 'POST', body: JSON.stringify({ mode: 'offline' }) });
    render();
    focusEvidence();
    if (state.timer) window.clearInterval(state.timer);
    state.timer = window.setInterval(async () => {
      if (!state.run || ['shipped', 'failed', 'awaiting_human'].includes(state.run.status)) {
        if (state.run?.status === 'awaiting_human') window.clearInterval(state.timer);
        return;
      }
      try { state.run = await request('/api/run'); render(); } catch (_) { }
    }, 450);
  } finally {
    $('run-demo').disabled = false;
    $('run-demo-secondary').disabled = false;
  }
}

async function approveRun() {
  if (!state.run) return;
  state.run = await request('/api/approve', { method: 'POST', body: JSON.stringify({ run_id: state.run.id }) });
  render();
}

async function exportReport() {
  if (!state.run) return;
  const payload = await request('/api/report');
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${state.run.id}-report.json`;
  link.click();
  URL.revokeObjectURL(url);
}

$('run-demo').addEventListener('click', startRun);
$('run-demo-secondary').addEventListener('click', startRun);
$('approve').addEventListener('click', approveRun);
$('export-report').addEventListener('click', exportReport);

(async function boot() {
  try { state.run = await request('/api/run'); } catch (_) { }
  render();
})();
