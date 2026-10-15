<script>
  import { toolCallTraces, clearToolTraces, showTracePanel } from '../lib/store.js';
  import { X, Search, Activity, Terminal, Copy, Check, ChevronDown, Trash2 } from '@lucide/svelte';

  let filter = '';
  let expandedId = null;
  let copiedId = null;

  $: filteredTraces = $toolCallTraces.filter(t => {
    if (!filter) return true;
    const q = filter.toLowerCase();
    return (
      (t.toolName || '').toLowerCase().includes(q) ||
      (t.status || '').toLowerCase().includes(q) ||
      JSON.stringify(t.toolArgs || {}).toLowerCase().includes(q)
    );
  });

  $: avgLatency = $toolCallTraces.length > 0
    ? Math.round($toolCallTraces.reduce((acc, t) => acc + (t.ms || 0), 0) / $toolCallTraces.length)
    : 0;

  function isTraceOk(trace) {
    if (trace.isLive) return true;
    if (!trace.status) return false;
    const s = trace.status.toLowerCase();
    return s.includes('200') || s.includes('ok') || s === 'success';
  }

  function toggleExpand(id) {
    expandedId = expandedId === id ? null : id;
  }

  async function copyJson(trace) {
    const payload = {
      request: trace.requestPayload || { method: "tools/call", params: { name: trace.toolName, arguments: trace.toolArgs } },
      response: trace.responsePayload || { result: trace.rawResult || trace.result },
    };
    try {
      await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
      copiedId = trace.id;
      setTimeout(() => { copiedId = null; }, 1800);
    } catch (e) {
      // Clipboard fallback
    }
  }

  function handleKeydown(e) {
    if (e.key === 'Escape') {
      showTracePanel.set(false);
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="trace-backdrop" on:click={() => showTracePanel.set(false)} role="presentation">
  <div
    class="trace-drawer"
    on:click|stopPropagation
    on:keydown|stopPropagation
    role="dialog"
    aria-modal="true"
    aria-label="Live MCP Tool Call Trace Panel"
    tabindex="-1"
  >
    <!-- Drawer Header -->
    <header class="drawer-header">
      <div class="header-top">
        <div class="title-wrap">
          <Activity size={17} class="accent-icon" />
          <h2 class="drawer-title">Protocol Traces</h2>
        </div>
        <button
          type="button"
          class="close-btn"
          on:click={() => showTracePanel.set(false)}
          aria-label="Close trace panel"
          title="Close panel (Esc)"
        >
          <X size={17} />
        </button>
      </div>

      <!-- Clean Stat Badges Row -->
      <div class="meta-pills-row">
        <span class="pill-tag endpoint">
          <span class="status-dot"></span>
          /mcp
        </span>
        <span class="pill-tag">
          <strong>{$toolCallTraces.length}</strong> calls
        </span>
        {#if avgLatency > 0}
          <span class="pill-tag">
            <strong>{avgLatency}ms</strong> avg
          </span>
        {/if}
      </div>

      <!-- Search & Clear Row -->
      <div class="search-row">
        <div class="search-input-wrap">
          <Search size={14} class="search-icon" />
          <input
            type="search"
            placeholder="Filter by tool name or args..."
            bind:value={filter}
            class="filter-input"
          />
        </div>
        <button
          type="button"
          class="clear-btn"
          on:click={clearToolTraces}
          disabled={$toolCallTraces.length === 0}
          title="Clear all traces"
        >
          <Trash2 size={13} />
          <span>Clear</span>
        </button>
      </div>
    </header>

    <!-- Trace Items Stream -->
    <div class="trace-stream-wrap">
      {#if filteredTraces.length === 0}
        <div class="empty-state">
          <Terminal size={32} class="empty-icon" />
          <h3 class="empty-title">No traces {$toolCallTraces.length > 0 ? 'matching filter' : 'recorded yet'}</h3>
          <p class="empty-desc">
            Interact with voice or suggestions to inspect live JSON-RPC 2.0 tool-call packets.
          </p>
        </div>
      {:else}
        <div class="trace-list-container" role="list">
          {#each filteredTraces as trace (trace.id)}
            <div class="trace-row-wrap" class:expanded={expandedId === trace.id} role="listitem">
              <!-- Compact, Sleek 1-Row Summary -->
              <button
                type="button"
                class="trace-row-btn"
                on:click={() => toggleExpand(trace.id)}
                aria-expanded={expandedId === trace.id}
              >
                <!-- Left: Status Code + Tool Name -->
                <div class="row-left">
                  <span class="code-pill {isTraceOk(trace) ? 'ok' : 'error'}">
                    {isTraceOk(trace) ? '200' : 'ERR'}
                  </span>
                  <span class="tool-name">{trace.toolName}</span>
                </div>

                <!-- Right: Latency + Time + Chevron -->
                <div class="row-right">
                  <span class="latency-text">{trace.ms || 0}ms</span>
                  <span class="time-text">{trace.timestamp}</span>
                  <ChevronDown size={14} class="chevron {expandedId === trace.id ? 'open' : ''}" />
                </div>
              </button>

              <!-- Inline Expanded JSON-RPC Payload -->
              {#if expandedId === trace.id}
                <div class="payload-panel">
                  <div class="payload-actions">
                    <span class="payload-heading">JSON-RPC 2.0 Packet</span>
                    <button
                      type="button"
                      class="copy-btn"
                      on:click={() => copyJson(trace)}
                      title="Copy full JSON payload"
                    >
                      {#if copiedId === trace.id}
                        <Check size={12} class="copied-icon" />
                        <span>Copied</span>
                      {:else}
                        <Copy size={12} />
                        <span>Copy JSON</span>
                      {/if}
                    </button>
                  </div>

                  <div class="code-box">
                    <span class="code-label">Request (tools/call)</span>
                    <pre class="json-pre">{JSON.stringify(trace.requestPayload || { method: "tools/call", params: { name: trace.toolName, arguments: trace.toolArgs } }, null, 2)}</pre>
                  </div>

                  <div class="code-box">
                    <span class="code-label">Response</span>
                    <pre class="json-pre">{JSON.stringify(trace.responsePayload || { result: trace.rawResult || trace.result }, null, 2)}</pre>
                  </div>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  /* ================= BACKDROP & DRAWER ================= */
  .trace-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(3px);
    z-index: 50;
    display: flex;
    justify-content: flex-end;
    animation: fadeIn 150ms ease-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .trace-drawer {
    width: var(--drawer-w);
    max-width: 100vw;
    height: 100dvh;
    background: var(--surface);
    border-left: 1px solid var(--line-soft);
    border-top-left-radius: 20px;
    border-bottom-left-radius: 20px;
    box-shadow: var(--shadow-pop);
    display: flex;
    flex-direction: column;
    animation: slideIn 220ms cubic-bezier(0.16, 1, 0.3, 1);
    overflow: hidden;
  }

  @keyframes slideIn {
    from { transform: translateX(100%); }
    to { transform: translateX(0); }
  }

  @media (max-width: 720px) {
    .trace-drawer {
      width: 100vw;
      border-radius: 0;
    }
  }

  /* ================= HEADER ================= */
  .drawer-header {
    padding: 18px 20px 14px 20px;
    border-bottom: 1px solid var(--line-soft);
    display: flex;
    flex-direction: column;
    gap: 12px;
    background: var(--surface);
    flex-shrink: 0;
  }

  .header-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .title-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  :global(.accent-icon) {
    color: var(--accent);
  }

  .drawer-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--text);
    margin: 0;
  }

  .close-btn {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    border: none;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 150ms ease, color 150ms ease;
  }
  .close-btn:hover {
    background: var(--surface-2);
    color: var(--text);
  }

  /* Meta Pills */
  .meta-pills-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .pill-tag {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 2px 8px;
    border-radius: 6px;
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
    font-size: 12px;
    color: var(--text-muted);
  }

  .pill-tag strong {
    color: var(--text);
    font-weight: 600;
  }

  .pill-tag.endpoint {
    color: var(--text-soft);
    font-family: var(--font-mono);
    font-size: 11.5px;
    font-weight: 500;
  }

  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--ok);
  }

  /* Search & Clear */
  .search-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .search-input-wrap {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
    border-radius: 8px;
    padding: 0 10px;
    height: 34px;
    transition: border-color 150ms ease, background 150ms ease;
  }

  .search-input-wrap:focus-within {
    border-color: var(--accent);
    background: var(--surface);
  }

  :global(.search-icon) {
    color: var(--text-muted);
    flex-shrink: 0;
  }

  .filter-input {
    flex: 1;
    border: none;
    background: transparent;
    font-family: var(--font-ui);
    font-size: 12.5px;
    color: var(--text);
    outline: none;
  }

  .clear-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    height: 34px;
    padding: 0 10px;
    border-radius: 8px;
    border: 1px solid var(--line-soft);
    background: var(--surface);
    color: var(--text-muted);
    font-family: var(--font-ui);
    font-size: 12.5px;
    font-weight: 500;
    cursor: pointer;
    transition: all 150ms ease;
    flex-shrink: 0;
  }

  .clear-btn:hover:not(:disabled) {
    background: var(--surface-2);
    color: var(--text);
    border-color: var(--line);
  }

  .clear-btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  /* ================= TRACE STREAM ================= */
  .trace-stream-wrap {
    flex: 1;
    overflow-y: auto;
    padding: 14px 16px;
  }

  /* Unified List Container */
  .trace-list-container {
    display: flex;
    flex-direction: column;
    border: 1px solid var(--line-soft);
    border-radius: 12px;
    background: var(--surface);
    overflow: hidden;
  }

  .trace-row-wrap {
    border-bottom: 1px solid var(--line-soft);
    transition: background 120ms ease;
  }

  .trace-row-wrap:last-child {
    border-bottom: none;
  }

  .trace-row-wrap.expanded {
    background: var(--surface);
  }

  /* Clean Single Row Button */
  .trace-row-btn {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 9px 12px;
    background: transparent;
    border: none;
    cursor: pointer;
    text-align: left;
    transition: background 120ms ease;
  }

  .trace-row-btn:hover {
    background: var(--surface-2);
  }

  .row-left {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    flex: 1;
  }

  .code-pill {
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
    flex-shrink: 0;
    line-height: 1.2;
  }

  .code-pill.ok {
    background: rgba(52, 168, 83, 0.12);
    color: var(--ok-text);
  }

  .code-pill.error {
    background: rgba(234, 67, 53, 0.12);
    color: var(--urgent-text);
  }

  .tool-name {
    font-family: var(--font-mono);
    font-size: 12.5px;
    font-weight: 500;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .row-right {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .latency-text {
    font-family: var(--font-mono);
    font-size: 11.5px;
    color: var(--text-muted);
  }

  .time-text {
    font-size: 11.5px;
    color: var(--text-muted);
  }

  :global(.chevron) {
    color: var(--text-muted);
    transition: transform 180ms ease;
    flex-shrink: 0;
  }

  :global(.chevron.open) {
    transform: rotate(180deg);
  }

  /* ================= EXPANDED PAYLOAD ================= */
  .payload-panel {
    background: var(--surface-2);
    border-top: 1px solid var(--line-soft);
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    animation: expandIn 160ms ease-out;
  }

  @keyframes expandIn {
    from {
      opacity: 0;
      transform: translateY(-4px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .payload-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .payload-heading {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
  }

  .copy-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: var(--surface);
    border: 1px solid var(--line-soft);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 11.5px;
    font-weight: 500;
    color: var(--text-soft);
    cursor: pointer;
    transition: all 150ms ease;
  }

  .copy-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
  }

  :global(.copied-icon) {
    color: var(--ok);
  }

  .code-box {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .code-label {
    font-size: 11px;
    font-weight: 500;
    color: var(--text-muted);
  }

  .json-pre {
    background: var(--surface);
    border: 1px solid var(--line-soft);
    border-radius: 6px;
    padding: 8px 10px;
    max-height: 180px;
    overflow-y: auto;
    font-family: var(--font-mono);
    font-size: 11.5px;
    line-height: 1.45;
    color: var(--text);
    white-space: pre-wrap;
    word-break: break-all;
    margin: 0;
  }

  /* Empty State */
  .empty-state {
    padding: 48px 16px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }

  :global(.empty-icon) {
    color: var(--text-muted);
  }

  .empty-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--text);
    margin: 0;
  }

  .empty-desc {
    font-size: 12.5px;
    color: var(--text-muted);
    max-width: 280px;
    line-height: 1.4;
    margin: 0;
  }
</style>
