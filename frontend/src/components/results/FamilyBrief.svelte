<script>
  // FamilyBrief.svelte — illustrated summary panel
  // Shows counts + raw text; this is a high-level overview.
  export let data = { raw: '', expiringCount: 0, tasksCount: 0 };
</script>

<div class="renderer" aria-label="Family briefing summary">
  <h3 class="renderer-title">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
    </svg>
    Family Briefing
  </h3>

  <!-- Summary counters -->
  <div class="counters">
    <div class="counter" class:warn={data.expiringCount > 0}>
      <span class="counter-num">{data.expiringCount}</span>
      <span class="counter-label">Documents expiring</span>
    </div>
    <div class="counter" class:warn={data.tasksCount > 0}>
      <span class="counter-num">{data.tasksCount}</span>
      <span class="counter-label">Tasks due soon</span>
    </div>
  </div>

  <!-- Raw text detail -->
  {#if data.raw}
    <pre class="brief-text">{data.raw}</pre>
  {/if}

  <p class="disclaimer">Guidance only. Verify on the official site.</p>
</div>

<style>
  .renderer { display: flex; flex-direction: column; gap: var(--sp-3); }

  .renderer-title {
    display: flex; align-items: center; gap: var(--sp-2);
    font-size: 0.82rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.05em;
    color: var(--text-muted);
  }

  .counters {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--sp-3);
  }

  .counter {
    padding: var(--sp-4);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-md);
    display: flex; flex-direction: column; gap: 4px;
    text-align: center;
    transition: var(--theme-transition);
  }

  .counter.warn {
    background: var(--amber-bg);
    border-color: var(--amber);
  }

  .counter-num {
    font-family: var(--font-display);
    font-size: 2rem; font-weight: 800;
    color: var(--text);
    line-height: 1;
  }

  .counter.warn .counter-num { color: var(--amber-text); }

  .counter-label { font-size: 0.72rem; color: var(--text-muted); }

  .brief-text {
    font-family: var(--font-body);
    font-size: 0.84rem; color: var(--text-2);
    white-space: pre-wrap; line-height: 1.6;
    background: var(--surface-2);
    border-radius: var(--r-md);
    padding: var(--sp-3) var(--sp-4);
    border: 1px solid var(--border);
  }

  .disclaimer {
    font-size: 0.68rem; color: var(--text-muted); opacity: 0.7;
    border-top: 1px solid var(--border); padding-top: var(--sp-2);
  }
</style>
