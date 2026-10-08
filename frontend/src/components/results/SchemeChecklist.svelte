<script>
  // SchemeChecklist.svelte — document checklist with step bullets
  export let data = { name: '', summary: '', items: [], notes: '', sourceUrl: '', applyUrl: '' };
  let checked = {};
</script>

<div class="renderer" aria-label="Document checklist for {data.name}">
  <h3 class="renderer-title">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
    </svg>
    {data.name}
  </h3>

  {#if data.summary}<p class="summary">{data.summary}</p>{/if}

  {#if data.items?.length > 0}
    <ul class="checklist" role="list" aria-label="Required documents">
      {#each data.items as item, i}
        <li class="check-item">
          <button
            class="check-btn"
            class:ticked={checked[i]}
            on:click={() => checked = {...checked, [i]: !checked[i]}}
            aria-pressed={checked[i]}
            aria-label="{checked[i] ? 'Unmark' : 'Mark'}: {item}"
          >
            {#if checked[i]}
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" aria-hidden="true">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            {/if}
          </button>
          <span class="check-label" class:done={checked[i]}>{item}</span>
        </li>
      {/each}
    </ul>
  {/if}

  {#if data.notes}<p class="notes">{data.notes}</p>{/if}

  <div class="links">
    {#if data.sourceUrl}
      <a href={data.sourceUrl} target="_blank" rel="noopener noreferrer" class="link-btn">
        Official details ↗
      </a>
    {/if}
    {#if data.applyUrl}
      <a href={data.applyUrl} target="_blank" rel="noopener noreferrer" class="link-btn apply">
        Apply online ↗
      </a>
    {/if}
  </div>

  <p class="disclaimer">Guidance only. Verify on the official site.</p>
</div>

<style>
  .renderer { display: flex; flex-direction: column; gap: var(--sp-3); }

  .renderer-title {
    display: flex; align-items: center; gap: var(--sp-2);
    font-size: 0.88rem; font-weight: 700; color: var(--text); line-height: 1.3;
  }

  .summary { font-size: 0.82rem; color: var(--text-2); }

  .checklist { list-style: none; display: flex; flex-direction: column; gap: var(--sp-2); }

  .check-item { display: flex; align-items: flex-start; gap: var(--sp-2); }

  .check-btn {
    width: 20px; height: 20px; flex-shrink: 0; margin-top: 1px;
    border-radius: 5px; border: 2px solid var(--border-strong);
    background: transparent; cursor: pointer;
    display: grid; place-items: center;
    transition: all var(--t-base) var(--ease-spring);
  }

  .check-btn.ticked { background: var(--green); border-color: var(--green); color: white; }

  .check-label { font-size: 0.88rem; color: var(--text); line-height: 1.4; }
  .check-label.done { text-decoration: line-through; color: var(--text-muted); }

  .notes {
    font-size: 0.78rem; color: var(--text-muted);
    padding: var(--sp-2) var(--sp-3);
    background: var(--violet-bg);
    border-radius: var(--r-md);
    border-left: 3px solid var(--violet);
  }

  .links { display: flex; gap: var(--sp-2); flex-wrap: wrap; }

  .link-btn {
    padding: 6px var(--sp-3); border-radius: var(--r-md);
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text-2); font-size: 0.78rem; font-weight: 600;
    text-decoration: none; transition: all var(--t-fast) ease;
  }

  .link-btn:hover { background: var(--teal-bg); color: var(--teal-text); border-color: var(--teal); }
  .link-btn.apply { background: var(--teal-bg); color: var(--teal-text); border-color: var(--teal); }

  .disclaimer {
    font-size: 0.68rem; color: var(--text-muted); opacity: 0.7;
    border-top: 1px solid var(--border); padding-top: var(--sp-2);
  }
</style>
