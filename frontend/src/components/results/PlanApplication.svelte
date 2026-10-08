<script>
  // PlanApplication.svelte — two-step plan with visual timeline
  export let data = { schemeName: '', status: '', tasks: [], portal: '', docs: [] };
</script>

<div class="renderer" aria-label="Application plan for {data.schemeName}">
  <h3 class="renderer-title">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
    </svg>
    Application Plan
  </h3>

  {#if data.schemeName}
    <div class="scheme-badge">
      <span class="badge badge-violet">{data.schemeName}</span>
      {#if data.status}<span class="badge badge-teal">{data.status}</span>{/if}
    </div>
  {/if}

  <!-- Two-step visual timeline -->
  {#if data.tasks?.length > 0}
    <ol class="timeline" aria-label="Steps">
      {#each data.tasks as task, i}
        <li class="step">
          <div class="step-dot" aria-hidden="true">{i + 1}</div>
          <div class="step-body">
            <span class="step-label">{task}</span>
          </div>
        </li>
      {/each}
    </ol>
  {/if}

  <!-- Documents needed -->
  {#if data.docs?.length > 0}
    <div class="docs-section">
      <span class="docs-title">Documents needed</span>
      <ul class="docs-list" role="list">
        {#each data.docs as doc}
          <li class="doc-bullet">
            <span class="bullet-dot" aria-hidden="true"></span>
            {doc}
          </li>
        {/each}
      </ul>
    </div>
  {/if}

  {#if data.portal}
    <a href={data.portal} target="_blank" rel="noopener noreferrer" class="portal-link">
      Official portal ↗
    </a>
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

  .scheme-badge { display: flex; gap: var(--sp-2); flex-wrap: wrap; }

  /* Timeline */
  .timeline { list-style: none; display: flex; flex-direction: column; gap: 0; position: relative; }

  .timeline::before {
    content: '';
    position: absolute;
    left: 13px; top: 14px;
    bottom: 14px;
    width: 2px;
    background: var(--border);
    z-index: 0;
  }

  .step {
    display: flex; align-items: flex-start; gap: var(--sp-3);
    position: relative; z-index: 1;
    padding: var(--sp-2) 0;
  }

  .step-dot {
    width: 28px; height: 28px; flex-shrink: 0;
    border-radius: 50%;
    background: var(--violet-bg);
    border: 2px solid var(--violet);
    color: var(--violet-text);
    font-size: 0.75rem; font-weight: 700;
    display: grid; place-items: center;
    font-family: var(--font-display);
  }

  .step-body { padding-top: 4px; }

  .step-label { font-size: 0.88rem; color: var(--text); }

  .docs-section { display: flex; flex-direction: column; gap: var(--sp-2); }

  .docs-title {
    font-size: 0.72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.05em;
    color: var(--text-muted);
  }

  .docs-list { list-style: none; display: flex; flex-direction: column; gap: var(--sp-1); }

  .doc-bullet {
    display: flex; align-items: center; gap: var(--sp-2);
    font-size: 0.84rem; color: var(--text-2);
  }

  .bullet-dot {
    width: 6px; height: 6px; flex-shrink: 0;
    border-radius: 50%; background: var(--teal);
  }

  .portal-link {
    padding: 7px var(--sp-3); border-radius: var(--r-md);
    border: 1px solid var(--teal);
    background: var(--teal-bg);
    color: var(--teal-text); font-size: 0.8rem; font-weight: 600;
    text-decoration: none; align-self: flex-start;
    transition: all var(--t-fast) ease;
  }

  .portal-link:hover { filter: brightness(1.1); }

  .disclaimer {
    font-size: 0.68rem; color: var(--text-muted); opacity: 0.7;
    border-top: 1px solid var(--border); padding-top: var(--sp-2);
  }
</style>
