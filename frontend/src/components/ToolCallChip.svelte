<script>
  import { ChevronDown, Terminal } from '@lucide/svelte';

  export let toolName = '';
  export let toolArgs = {};
  export let rawResult = '';
  export let isLive = false;
  export let ms = 0;

  let open = false;
</script>

{#if toolName}
  <div class="tool-chip-wrap">
    <!-- Header: small mono chip with source tag (Live in green, Demo in yellow) -->
    <button
      type="button"
      class="chip-btn"
      on:click={() => (open = !open)}
      aria-expanded={open}
      aria-label="Inspect tool call {toolName}"
    >
      <div class="chip-left">
        <Terminal size={14} class="chip-icon" aria-hidden="true" />
        <span class="tool-name">{toolName}()</span>
      </div>

      <div class="chip-right">
        {#if ms > 0}
          <span class="latency-text">{ms}ms</span>
        {/if}
        <span class="source-tag {isLive ? 'live' : 'demo'}">
          {isLive ? 'Live' : 'Demo fallback'}
        </span>
        <ChevronDown size={14} class="chevron {open ? 'open' : ''}" aria-hidden="true" />
      </div>
    </button>

    <!-- Expandable raw JSON in mono on --surface-2, max height 240px -->
    {#if open}
      <div class="chip-details" role="region" aria-label="Tool call parameters and result">
        <div class="detail-block">
          <span class="block-title">Arguments</span>
          <pre class="json-code">{JSON.stringify(toolArgs, null, 2)}</pre>
        </div>
        {#if rawResult}
          <div class="detail-block">
            <span class="block-title">Raw Output</span>
            <pre class="json-code result-scroll">{rawResult}</pre>
          </div>
        {/if}
      </div>
    {/if}
  </div>
{/if}

<style>
  .tool-chip-wrap {
    margin-top: var(--sp-8);
    display: inline-block;
    max-width: 100%;
  }

  .chip-btn {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-12);
    height: 30px;
    padding: 0 var(--sp-12);
    border-radius: var(--r-pill);
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
    font-family: var(--font-mono);
    font-size: var(--fs-label);
    color: var(--text-soft);
    cursor: pointer;
    transition: all var(--dur-fast) var(--ease);
  }

  .chip-btn:hover {
    border-color: var(--line);
    color: var(--text);
  }

  .chip-left {
    display: flex;
    align-items: center;
    gap: var(--sp-6);
  }

  .chip-icon {
    color: var(--text-muted);
  }

  .tool-name {
    font-weight: 500;
  }

  .chip-right {
    display: flex;
    align-items: center;
    gap: var(--sp-8);
  }

  .latency-text {
    font-size: 11px;
    color: var(--text-muted);
  }

  /* Source tag (Live in green, Demo fallback in yellow) */
  .source-tag {
    display: inline-flex;
    align-items: center;
    padding: 1px 6px;
    border-radius: var(--r-pill);
    font-size: 11px;
    font-weight: 500;
  }
  .source-tag.live {
    background: var(--ok-bg);
    color: var(--badge-ok-color);
  }
  .source-tag.demo {
    background: var(--soon-bg);
    color: var(--badge-soon-color);
  }

  .chevron {
    transition: transform var(--dur-fast) var(--ease);
    color: var(--text-muted);
  }
  .chevron.open {
    transform: rotate(180deg);
  }

  /* Expandable body on --surface-2, max height 240px */
  .chip-details {
    margin-top: var(--sp-6);
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
    border-radius: var(--r-sm);
    padding: var(--sp-12);
    max-height: 240px;
    overflow-y: auto;
    font-family: var(--font-mono);
  }

  .detail-block {
    margin-bottom: var(--sp-8);
  }
  .detail-block:last-child {
    margin-bottom: 0;
  }

  .block-title {
    display: block;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    margin-bottom: var(--sp-4);
  }

  .json-code {
    font-size: var(--fs-label);
    line-height: var(--lh-mono);
    color: var(--text);
    white-space: pre-wrap;
    word-break: break-all;
  }

  .result-scroll {
    max-height: 120px;
    overflow-y: auto;
  }
</style>
