<script>
  // ToolCallChip.svelte
  // Shows which MCP tool was called, its arguments, and the raw result.
  // Expandable — collapsed by default. Proves the live MCP link to judges.

  export let toolName = '';
  export let toolArgs = {};
  export let rawResult = '';
  export let isLive = false;
  export let ms = 0;

  let open = false;
</script>

{#if toolName}
  <div class="chip-wrap">
    <!-- Header row — always visible, click to expand -->
    <button
      class="chip-header"
      on:click={() => (open = !open)}
      aria-expanded={open}
      aria-controls="tool-body-{toolName}"
    >
      <!-- Tool icon + name -->
      <span class="chip-left">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/>
          <path d="M2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
        <code class="tool-name">{toolName}()</code>
      </span>

      <!-- Right: timing + live/demo badge + chevron -->
      <span class="chip-right">
        {#if ms > 0}<span class="timing">{ms}ms</span>{/if}
        <span class="live-badge" class:live={isLive} class:demo={!isLive}>
          {isLive ? '⚡ Live HTTP' : '🔵 Demo fallback'}
        </span>
        <svg
          class="chevron"
          class:rotated={open}
          width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
          aria-hidden="true"
        >
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </span>
    </button>

    <!-- Expandable body -->
    {#if open}
      <div class="chip-body" id="tool-body-{toolName}" role="region" aria-label="Tool call details">
        <div class="section">
          <span class="section-label">Arguments</span>
          <pre class="code-block">{JSON.stringify(toolArgs, null, 2)}</pre>
        </div>
        {#if rawResult}
          <div class="section">
            <span class="section-label">Raw Result</span>
            <pre class="code-block result">{rawResult}</pre>
          </div>
        {/if}
      </div>
    {/if}
  </div>
{/if}

<style>
  .chip-wrap {
    margin-top: var(--sp-2);
    border-radius: var(--r-md);
    border: 1px solid var(--border);
    background: var(--surface-2);
    overflow: hidden;
    font-family: var(--font-mono);
    font-size: 0.72rem;
    transition: var(--theme-transition);
  }

  .chip-header {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--sp-2);
    padding: 6px var(--sp-3);
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-muted);
    font-family: var(--font-mono);
    font-size: 0.72rem;
    text-align: left;
    transition: background var(--t-fast) ease;
  }

  .chip-header:hover {
    background: var(--surface-3);
  }

  .chip-left {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--violet-text);
    font-weight: 500;
  }

  .tool-name {
    font-size: 0.72rem;
    color: var(--violet-text);
  }

  .chip-right {
    display: flex;
    align-items: center;
    gap: var(--sp-2);
    flex-shrink: 0;
  }

  .timing {
    color: var(--text-muted);
    font-size: 0.68rem;
  }

  .live-badge {
    padding: 2px 7px;
    border-radius: var(--r-full);
    font-size: 0.65rem;
    font-weight: 600;
  }

  .live-badge.live {
    background: var(--teal-bg);
    color: var(--teal-text);
  }

  .live-badge.demo {
    background: var(--amber-bg);
    color: var(--amber-text);
  }

  .chevron {
    transition: transform var(--t-fast) ease;
    flex-shrink: 0;
  }

  .chevron.rotated {
    transform: rotate(180deg);
  }

  .chip-body {
    border-top: 1px solid var(--border);
    padding: var(--sp-3);
    display: flex;
    flex-direction: column;
    gap: var(--sp-3);
  }

  .section {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .section-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-muted);
  }

  .code-block {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-sm);
    padding: var(--sp-2) var(--sp-3);
    color: var(--text-2);
    font-size: 0.7rem;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 180px;
    overflow-y: auto;
    line-height: 1.5;
  }

  .code-block.result {
    color: var(--teal-text);
  }
</style>
