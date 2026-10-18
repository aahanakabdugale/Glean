<script>
  import { onMount } from 'svelte';
  import { toolCallTraces, clearToolTraces, activeView } from '../lib/store.js';
  import { calculateTraceStats, explainTrace } from '../lib/traceExplain.js';
  import {
    Activity,
    ShieldCheck,
    Copy,
    Check,
    Download,
    Trash2,
    Search,
    LayoutGrid,
    MessageSquare,
    Terminal
  } from '@lucide/svelte';

  let filter = '';
  let activeTab = 'plain'; // 'plain' | 'json'
  let selectedId = null;
  let userHasSelectedManually = false;
  let copied = false;

  $: filteredTraces = $toolCallTraces.filter(t => {
    if (!filter.trim()) return true;
    const q = filter.trim().toLowerCase();
    return (
      (t.toolName || '').toLowerCase().includes(q) ||
      (t.status || '').toLowerCase().includes(q) ||
      JSON.stringify(t.toolArgs || {}).toLowerCase().includes(q)
    );
  });

  $: stats = calculateTraceStats($toolCallTraces);

  // Auto-select newest trace unless user has manually chosen a selection
  $: {
    if (filteredTraces.length > 0) {
      if (!userHasSelectedManually) {
        selectedId = filteredTraces[0].id;
      } else if (!filteredTraces.some(t => t.id === selectedId)) {
        selectedId = filteredTraces[0].id;
      }
    } else {
      selectedId = null;
    }
  }

  $: selectedTrace = filteredTraces.find(t => t.id === selectedId) || filteredTraces[0] || null;
  $: explanation = selectedTrace ? explainTrace(selectedTrace) : null;

  $: requestJsonStr = selectedTrace
    ? JSON.stringify(
        selectedTrace.requestPayload || {
          jsonrpc: '2.0',
          id: selectedTrace.id,
          method: 'tools/call',
          params: {
            name: selectedTrace.toolName,
            arguments: selectedTrace.toolArgs || {}
          }
        },
        null,
        2
      )
    : '';

  $: responseJsonStr = selectedTrace
    ? JSON.stringify(
        selectedTrace.responsePayload || {
          jsonrpc: '2.0',
          id: selectedTrace.id,
          result: {
            content: [
              {
                type: 'text',
                text: selectedTrace.rawResult || selectedTrace.result || ''
              }
            ]
          }
        },
        null,
        2
      )
    : '';

  function handleSelect(id) {
    selectedId = id;
    userHasSelectedManually = true;
  }

  function handleClear() {
    clearToolTraces();
    selectedId = null;
    userHasSelectedManually = false;
  }

  function handleExport() {
    if ($toolCallTraces.length === 0) return;
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify($toolCallTraces, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `glean-traces-${new Date().toISOString().slice(0, 10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  }

  async function copyTraceJson() {
    if (!selectedTrace) return;
    const fullPacket = {
      request: selectedTrace.requestPayload || {
        jsonrpc: '2.0',
        id: selectedTrace.id,
        method: 'tools/call',
        params: { name: selectedTrace.toolName, arguments: selectedTrace.toolArgs || {} }
      },
      response: selectedTrace.responsePayload || {
        jsonrpc: '2.0',
        id: selectedTrace.id,
        result: { content: [{ type: 'text', text: selectedTrace.rawResult || '' }] }
      }
    };

    try {
      await navigator.clipboard.writeText(JSON.stringify(fullPacket, null, 2));
      copied = true;
      setTimeout(() => { copied = false; }, 1800);
    } catch (e) {
      // Clipboard fallback
    }
  }

  function handleKeydown(e) {
    // Avoid capturing keyboard shortcuts if typing in filter input
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) {
      return;
    }

    if (e.key === 'c' || e.key === 'C') {
      if (selectedTrace) {
        e.preventDefault();
        copyTraceJson();
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (filteredTraces.length === 0) return;
      const idx = filteredTraces.findIndex(t => t.id === selectedId);
      if (idx < filteredTraces.length - 1) {
        selectedId = filteredTraces[idx + 1].id;
        userHasSelectedManually = true;
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (filteredTraces.length === 0) return;
      const idx = filteredTraces.findIndex(t => t.id === selectedId);
      if (idx > 0) {
        selectedId = filteredTraces[idx - 1].id;
        userHasSelectedManually = true;
      }
    }
  }

  function isTraceSuccess(trace) {
    if (!trace) return false;
    if (trace.isLive) return true;
    const s = String(trace.status || '').toLowerCase();
    return s.includes('200') || s.includes('ok') || s === 'success';
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="traces-container" role="region" aria-label="Protocol Traces">
  <!-- 1. HEADER ROW -->
  <header class="traces-header">
    <div class="header-left">
      <h1 class="page-title">Protocol Traces</h1>
      <span class="mcp-live-chip" title="Live Streamable HTTP MCP transport active">
        <span class="live-dot" aria-hidden="true"></span>
        /mcp live
      </span>
    </div>

    <div class="header-actions">
      <button
        type="button"
        class="action-btn secondary"
        on:click={handleClear}
        disabled={$toolCallTraces.length === 0}
        title="Clear all recorded session traces"
      >
        <Trash2 size={14} />
        <span>Clear</span>
      </button>

      <button
        type="button"
        class="action-btn primary"
        on:click={handleExport}
        disabled={$toolCallTraces.length === 0}
        title="Download all traces as a JSON file"
      >
        <Download size={14} />
        <span>Export all</span>
      </button>
    </div>
  </header>

  <!-- 2. STATS ROW (4 TILES) -->
  <section class="stats-grid" aria-label="MCP Protocol Performance Metrics">
    <!-- Calls -->
    <div class="stat-card">
      <span class="stat-label">Calls</span>
      <span class="stat-value">{stats.total}</span>
    </div>

    <!-- Avg Latency -->
    <div class="stat-card">
      <span class="stat-label">Avg latency</span>
      <span class="stat-value">{stats.avgLatency}ms</span>
    </div>

    <!-- Success % -->
    <div class="stat-card">
      <span class="stat-label">Success</span>
      <span class="stat-value success">{stats.successPct}%</span>
    </div>

    <!-- Slowest -->
    <div class="stat-card">
      <span class="stat-label">Slowest</span>
      <span class="stat-value warning">{stats.slowestMs}ms</span>
    </div>
  </section>

  <!-- 3. MAIN AREA (TABLE + DETAIL PANEL) OR EMPTY STATE -->
  {#if $toolCallTraces.length === 0}
    <!-- 4. EMPTY STATE -->
    <div class="empty-state-panel">
      <div class="empty-icon-wrap" aria-hidden="true">
        <Terminal size={32} />
      </div>
      <h2 class="empty-title">No tool calls yet</h2>
      <p class="empty-desc">
        No tool calls yet. Ask Glean something to see the MCP traffic here.
      </p>
      <div class="empty-actions">
        <button
          type="button"
          class="empty-btn primary"
          on:click={() => activeView.set('dashboard')}
        >
          <LayoutGrid size={15} />
          <span>Go to Dashboard</span>
        </button>
        <button
          type="button"
          class="empty-btn secondary"
          on:click={() => activeView.set('chat')}
        >
          <MessageSquare size={15} />
          <span>Ask Glean</span>
        </button>
      </div>
    </div>
  {:else}
    <div class="main-split-area">
      <!-- LEFT COLUMN: TABLE (approx 55%) -->
      <div class="table-column panel-surface">
        <!-- Filter Search Bar -->
        <div class="filter-bar">
          <Search size={15} class="filter-icon" aria-hidden="true" />
          <input
            type="text"
            class="filter-input"
            placeholder="Filter by tool name or args..."
            bind:value={filter}
            aria-label="Filter tool traces"
          />
          {#if filter}
            <button
              type="button"
              class="filter-clear-btn"
              on:click={() => filter = ''}
              aria-label="Clear filter"
            >
              ✕
            </button>
          {/if}
        </div>

        <!-- Traces Table -->
        <div class="table-scroll-wrap">
          <table class="traces-table">
            <thead>
              <tr>
                <th class="th-status">Status</th>
                <th class="th-tool">Tool</th>
                <th class="th-time">Time</th>
                <th class="th-ms">ms</th>
              </tr>
            </thead>
            <tbody>
              {#if filteredTraces.length === 0}
                <tr>
                  <td colspan="4" class="no-matches-cell">
                    No matching traces found for "{filter}".
                  </td>
                </tr>
              {:else}
                {#each filteredTraces as trace (trace.id)}
                  {@const ok = isTraceSuccess(trace)}
                  {@const isOver80 = (trace.ms || 0) > 80}
                  <tr
                    class="trace-row"
                    class:selected={trace.id === selectedId}
                    on:click={() => handleSelect(trace.id)}
                    tabindex="0"
                    aria-selected={trace.id === selectedId}
                  >
                    <!-- Status Pill -->
                    <td class="td-status">
                      <span class="status-pill {ok ? 'ok' : 'err'}">
                        {ok ? '200' : 'ERR'}
                      </span>
                    </td>

                    <!-- Tool Name -->
                    <td class="td-tool">
                      <span class="tool-name-text" title={trace.toolName}>
                        {trace.toolName || 'unknown_tool'}
                      </span>
                    </td>

                    <!-- Time -->
                    <td class="td-time">
                      {trace.timestamp || '--:--:--'}
                    </td>

                    <!-- Latency ms -->
                    <td class="td-ms">
                      <span class="latency-text {isOver80 ? 'over80' : 'under80'}">
                        {trace.ms || 0}
                      </span>
                    </td>
                  </tr>
                {/each}
              {/if}
            </tbody>
          </table>
        </div>
      </div>

      <!-- RIGHT COLUMN: DETAIL PANEL (approx 45%) -->
      <div class="detail-column panel-surface">
        {#if selectedTrace}
          <!-- Detail Panel Header -->
          <div class="detail-header">
            <h2 class="detail-tool-name" title={selectedTrace.toolName}>
              {selectedTrace.toolName || 'Tool Execution'}
            </h2>

            <!-- Segmented Toggle: Plain | JSON -->
            <div class="segmented-toggle" role="tablist" aria-label="Trace view mode">
              <button
                type="button"
                class="seg-btn"
                class:active={activeTab === 'plain'}
                on:click={() => activeTab = 'plain'}
                role="tab"
                aria-selected={activeTab === 'plain'}
              >
                Plain
              </button>
              <button
                type="button"
                class="seg-btn"
                class:active={activeTab === 'json'}
                on:click={() => activeTab = 'json'}
                role="tab"
                aria-selected={activeTab === 'json'}
              >
                JSON
              </button>
            </div>
          </div>

          <!-- Detail Panel Content -->
          <div class="detail-body">
            {#if activeTab === 'plain' && explanation}
              <!-- PLAIN ENGLISH VIEW -->
              <div class="plain-view-container">
                <!-- What was asked sentence -->
                <div class="plain-section card-surface">
                  <span class="section-label">Action Requested</span>
                  <p class="plain-sentence">{explanation.asked}</p>
                </div>

                <!-- Arguments key/value chips -->
                <div class="plain-section card-surface">
                  <span class="section-label">Tool Arguments</span>
                  {#if explanation.argsList.length === 0}
                    <p class="plain-empty-args">None (empty arguments payload)</p>
                  {:else}
                    <div class="args-chips-list">
                      {#each explanation.argsList as arg}
                        <div class="arg-chip">
                          <span class="arg-key">{arg.key}:</span>
                          <span class="arg-val">{arg.value}</span>
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>

                <!-- Short summary of the result -->
                <div class="plain-section card-surface">
                  <span class="section-label">Execution Result</span>
                  <p class="plain-summary-text">{explanation.summary}</p>
                </div>
              </div>
            {:else}
              <!-- JSON VIEW (Full code blocks, no nested tiny scrollboxes) -->
              <div class="json-view-container">
                <!-- Request Code Block -->
                <div class="code-section">
                  <div class="code-title-row">
                    <span class="code-title-label">JSON-RPC 2.0 Request</span>
                    <span class="code-meta-tag">tools/call</span>
                  </div>
                  <pre class="code-block"><code>{requestJsonStr}</code></pre>
                </div>

                <!-- Response Code Block -->
                <div class="code-section">
                  <div class="code-title-row">
                    <span class="code-title-label">JSON-RPC 2.0 Response</span>
                    <span class="code-meta-tag">result</span>
                  </div>
                  <pre class="code-block"><code>{responseJsonStr}</code></pre>
                </div>
              </div>
            {/if}
          </div>

          <!-- Detail Panel Footer -->
          <footer class="detail-footer">
            <span class="verified-badge">
              <ShieldCheck size={14} class="shield-icon" aria-hidden="true" />
              Verified from database
            </span>

            <button
              type="button"
              class="copy-json-btn"
              on:click={copyTraceJson}
              title="Copy request and response JSON packet (Key: c)"
            >
              {#if copied}
                <Check size={14} class="copied-icon" />
                <span>Copied!</span>
              {:else}
                <Copy size={14} />
                <span>Copy JSON</span>
              {/if}
            </button>
          </footer>
        {:else}
          <div class="detail-placeholder">
            <p>Select a trace row on the left to inspect its parameters.</p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  /* ============================================================
     PROTOCOL TRACES FULL-PAGE VIEW
     Uses Theme Tokens: flat surfaces, 1px borders, 16px radius, Outfit font
     ============================================================ */
  .traces-container {
    width: 100%;
    max-width: 1100px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 20px;
    font-family: var(--font-ui, 'Outfit', sans-serif);
    color: var(--tr-text);
    box-sizing: border-box;
  }

  /* ---------------- 1. HEADER ROW ---------------- */
  .traces-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
    padding-bottom: 2px;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .page-title {
    font-size: 26px;
    font-weight: 600;
    line-height: 1.2;
    margin: 0;
    color: var(--tr-text);
  }

  .mcp-live-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 24px;
    padding: 0 10px;
    border-radius: 6px;
    background: var(--tr-card);
    border: 1px solid var(--tr-border);
    font-size: 12px;
    font-weight: 500;
    color: var(--tr-muted);
  }

  .live-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--tr-success);
    box-shadow: 0 0 6px var(--tr-success);
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .action-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 36px;
    padding: 0 14px;
    border-radius: 8px;
    font-family: inherit;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    border: 1px solid transparent;
    transition: background-color 150ms ease, border-color 150ms ease, opacity 150ms ease;
  }

  .action-btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .action-btn.secondary {
    background: var(--tr-card);
    border-color: var(--tr-border);
    color: var(--tr-text);
  }
  .action-btn.secondary:hover:not(:disabled) {
    border-color: var(--tr-muted);
  }

  .action-btn.primary {
    background: var(--tr-card);
    border-color: var(--tr-border);
    color: var(--tr-text);
  }
  .action-btn.primary:hover:not(:disabled) {
    border-color: var(--tr-accent);
    color: var(--tr-accent);
  }

  /* ---------------- 2. STATS ROW (4 TILES) ---------------- */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
  }

  .stat-card {
    background: var(--tr-card);
    border: 1px solid var(--tr-border);
    border-radius: 12px;
    padding: 14px 18px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .stat-label {
    font-size: 13px;
    font-weight: 500;
    color: var(--tr-muted);
  }

  .stat-value {
    font-size: 26px;
    font-weight: 600;
    line-height: 1.1;
    color: var(--tr-text);
  }

  .stat-value.success {
    color: var(--tr-success);
  }

  .stat-value.warning {
    color: var(--tr-warning);
  }

  /* ---------------- 3. MAIN SPLIT AREA (~55% / 45%) ---------------- */
  .main-split-area {
    display: grid;
    grid-template-columns: 55% 45%;
    gap: 16px;
    align-items: stretch;
    min-height: 480px;
  }

  .panel-surface {
    background: var(--tr-panel);
    border: 1px solid var(--tr-border);
    border-radius: 16px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* LEFT: Table Column */
  .table-column {
    padding: 12px;
    gap: 12px;
  }

  .filter-bar {
    position: relative;
    display: flex;
    align-items: center;
    background: var(--tr-card);
    border: 1px solid var(--tr-border);
    border-radius: 8px;
    padding: 0 10px;
    height: 38px;
  }

  :global(.filter-icon) {
    color: var(--tr-muted);
    flex-shrink: 0;
    margin-right: 8px;
  }

  .filter-input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    font-family: inherit;
    font-size: 13px;
    color: var(--tr-text);
  }
  .filter-input::placeholder {
    color: var(--tr-muted);
  }

  .filter-clear-btn {
    border: none;
    background: transparent;
    color: var(--tr-muted);
    font-size: 12px;
    cursor: pointer;
    padding: 4px;
  }

  .table-scroll-wrap {
    flex: 1;
    overflow-y: auto;
    max-height: 600px;
  }

  .traces-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0 4px;
    font-size: 13px;
  }

  .traces-table th {
    font-size: 12px;
    font-weight: 500;
    color: var(--tr-muted);
    text-align: left;
    padding: 6px 10px;
    border-bottom: 1px solid var(--tr-border);
  }

  .th-status { width: 68px; }
  .th-tool { width: auto; }
  .th-time { width: 95px; }
  .th-ms { width: 60px; text-align: right; }

  .traces-table td {
    padding: 9px 10px;
    vertical-align: middle;
  }

  .td-ms {
    text-align: right;
  }

  .trace-row {
    background: var(--tr-card);
    cursor: pointer;
    user-select: none;
    transition: background-color 150ms ease, border-color 150ms ease;
    border-radius: 8px;
    animation: traceRowFade 350ms ease-out;
  }

  @keyframes traceRowFade {
    from {
      opacity: 0.3;
      transform: translateY(-3px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .trace-row td:first-child {
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
  }
  .trace-row td:last-child {
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
  }

  .trace-row:hover {
    background: rgba(255, 255, 255, 0.05);
  }
  :global([data-theme="light"]) .trace-row:hover {
    background: #e9effa;
  }

  .trace-row.selected {
    box-shadow: inset 0 0 0 1.5px var(--tr-accent);
    background: rgba(25, 195, 255, 0.08);
  }
  :global([data-theme="light"]) .trace-row.selected {
    background: #e3edff;
    box-shadow: inset 0 0 0 1.5px var(--tr-accent);
  }

  /* Status Pill in Table */
  .status-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 600;
    line-height: 1;
    padding: 3px 6px;
    border-radius: 6px;
  }

  .status-pill.ok {
    background: var(--tr-success-bg);
    color: var(--tr-success);
  }

  .status-pill.err {
    background: var(--tr-danger-bg);
    color: var(--tr-danger);
  }

  .tool-name-text {
    font-weight: 500;
    color: var(--tr-text);
    display: block;
    max-width: 250px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .td-time {
    color: var(--tr-muted);
    font-size: 12px;
  }

  .latency-text {
    font-family: var(--font-mono, monospace);
    font-size: 12px;
    font-weight: 600;
  }

  .latency-text.under80 {
    color: var(--tr-success);
  }

  .latency-text.over80 {
    color: var(--tr-warning);
  }

  .no-matches-cell {
    text-align: center;
    padding: 32px 16px;
    color: var(--tr-muted);
    font-size: 13px;
  }

  /* RIGHT: Detail Column */
  .detail-column {
    display: flex;
    flex-direction: column;
    min-height: 480px;
  }

  .detail-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 18px;
    border-bottom: 1px solid var(--tr-border);
    gap: 12px;
  }

  .detail-tool-name {
    font-size: 16px;
    font-weight: 600;
    margin: 0;
    color: var(--tr-text);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* Segmented Toggle */
  .segmented-toggle {
    display: inline-flex;
    align-items: center;
    background: var(--tr-card);
    border: 1px solid var(--tr-border);
    border-radius: 8px;
    padding: 2px;
    flex-shrink: 0;
  }

  .seg-btn {
    border: none;
    background: transparent;
    padding: 4px 12px;
    border-radius: 6px;
    font-family: inherit;
    font-size: 12px;
    font-weight: 500;
    color: var(--tr-muted);
    cursor: pointer;
    transition: background-color 150ms ease, color 150ms ease;
  }

  .seg-btn.active {
    background: var(--tr-panel);
    color: var(--tr-text);
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  .detail-body {
    flex: 1;
    padding: 18px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  /* Plain View Styling */
  .plain-view-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .plain-section {
    background: var(--tr-card);
    border: 1px solid var(--tr-border);
    border-radius: 10px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .section-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--tr-muted);
  }

  .plain-sentence {
    font-size: 14px;
    font-weight: 500;
    line-height: 1.4;
    color: var(--tr-text);
    margin: 0;
  }

  .plain-empty-args {
    font-size: 13px;
    color: var(--tr-muted);
    margin: 0;
    font-style: italic;
  }

  .args-chips-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 2px;
  }

  .arg-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: var(--tr-panel);
    border: 1px solid var(--tr-border);
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 12px;
  }

  .arg-key {
    font-weight: 600;
    color: var(--tr-muted);
  }

  .arg-val {
    font-weight: 500;
    color: var(--tr-text);
    font-family: var(--font-mono, monospace);
  }

  .plain-summary-text {
    font-size: 13px;
    line-height: 1.45;
    color: var(--tr-text);
    margin: 0;
  }

  /* JSON View Styling (no nested scrollboxes, let panel scroll) */
  .json-view-container {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .code-section {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .code-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .code-title-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--tr-muted);
  }

  .code-meta-tag {
    font-size: 11px;
    font-family: var(--font-mono, monospace);
    color: var(--tr-muted);
  }

  .code-block {
    background: var(--tr-code-bg);
    border: 1px solid var(--tr-border);
    border-radius: 8px;
    padding: 12px;
    margin: 0;
    font-family: var(--font-mono, monospace);
    font-size: 12px;
    line-height: 1.45;
    color: var(--tr-text);
    white-space: pre-wrap;
    word-break: break-all;
    overflow: visible;
  }

  /* Detail Footer */
  .detail-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 18px;
    border-top: 1px solid var(--tr-border);
    background: var(--tr-card);
    gap: 12px;
  }

  .verified-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 500;
    color: var(--tr-success);
  }

  :global(.shield-icon) {
    color: var(--tr-success);
  }

  .copy-json-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 32px;
    padding: 0 12px;
    border-radius: 6px;
    border: 1px solid var(--tr-border);
    background: var(--tr-panel);
    color: var(--tr-text);
    font-family: inherit;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 150ms ease;
  }

  .copy-json-btn:hover {
    border-color: var(--tr-accent);
    color: var(--tr-accent);
  }

  :global(.copied-icon) {
    color: var(--tr-success);
  }

  .detail-placeholder {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 32px;
    color: var(--tr-muted);
    font-size: 13px;
  }

  /* ---------------- 4. EMPTY STATE ---------------- */
  .empty-state-panel {
    background: var(--tr-panel);
    border: 1px solid var(--tr-border);
    border-radius: 16px;
    padding: 64px 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: 12px;
  }

  .empty-icon-wrap {
    width: 60px;
    height: 60px;
    border-radius: 14px;
    background: var(--tr-card);
    border: 1px solid var(--tr-border);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--tr-accent);
    margin-bottom: 4px;
  }

  .empty-title {
    font-size: 20px;
    font-weight: 600;
    color: var(--tr-text);
    margin: 0;
  }

  .empty-desc {
    font-size: 14px;
    color: var(--tr-muted);
    max-width: 440px;
    margin: 0;
    line-height: 1.5;
  }

  .empty-actions {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 8px;
  }

  .empty-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 38px;
    padding: 0 16px;
    border-radius: 8px;
    font-family: inherit;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 150ms ease;
  }

  .empty-btn.primary {
    background: var(--tr-accent);
    border: 1px solid var(--tr-accent);
    color: #ffffff;
  }
  .empty-btn.primary:hover {
    filter: brightness(1.1);
  }

  .empty-btn.secondary {
    background: var(--tr-card);
    border: 1px solid var(--tr-border);
    color: var(--tr-text);
  }
  .empty-btn.secondary:hover {
    border-color: var(--tr-muted);
  }

  /* ---------------- RESPONSIVE BREAKPOINT (<800px) ---------------- */
  @media (max-width: 800px) {
    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .main-split-area {
      grid-template-columns: 1fr;
    }

    .table-column {
      max-height: 380px;
    }

    .table-scroll-wrap {
      max-height: 280px;
    }
  }
</style>
