<script>
  import { FileCheck, Check, ExternalLink, Info } from '@lucide/svelte';

  export let data = { name: '', summary: '', items: [], notes: '', sourceUrl: '', applyUrl: '' };
  let checked = {};
</script>

<div class="checklist-container" role="region" aria-label="Document checklist for {data.name}">
  <div class="header-row">
    <FileCheck size={16} class="header-icon" />
    <span class="text-label uppercase">Required Documents: {data.name}</span>
  </div>

  {#if data.summary}
    <p class="summary-text text-body">{data.summary}</p>
  {/if}

  {#if data.items?.length > 0}
    <div class="items-list" role="list">
      {#each data.items as item, i}
        <div class="vr-list-row {checked[i] ? 'ok' : 'info'}" role="listitem">
          <button
            type="button"
            class="check-circle"
            class:ticked={checked[i]}
            on:click={() => checked = {...checked, [i]: !checked[i]}}
            aria-pressed={checked[i]}
            aria-label="{checked[i] ? 'Unmark' : 'Mark'} {item}"
          >
            {#if checked[i]}
              <Check size={14} />
            {/if}
          </button>
          <span class="item-name text-body" class:done={checked[i]}>{item}</span>
        </div>
      {/each}
    </div>
  {/if}

  {#if data.notes}
    <div class="notes-box">
      <Info size={14} class="notes-icon" />
      <span class="notes-text text-small">{data.notes}</span>
    </div>
  {/if}

  <div class="actions-row">
    {#if data.applyUrl}
      <a href={data.applyUrl} target="_blank" rel="noopener noreferrer" class="vr-btn vr-btn-primary">
        <span>Apply online</span>
        <ExternalLink size={14} />
      </a>
    {/if}
    {#if data.sourceUrl}
      <a href={data.sourceUrl} target="_blank" rel="noopener noreferrer" class="vr-btn vr-btn-secondary">
        <span>Official portal</span>
        <ExternalLink size={14} />
      </a>
    {/if}
  </div>

  <p class="disclaimer text-label">Guidance only, verify on the official site.</p>
</div>

<style>
  .checklist-container {
    display: flex;
    flex-direction: column;
    gap: var(--sp-12);
    width: 100%;
  }

  .header-row {
    display: flex;
    align-items: center;
    gap: var(--sp-8);
    color: var(--text-muted);
  }

  .uppercase {
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .summary-text {
    color: var(--text-soft);
  }

  .items-list {
    display: flex;
    flex-direction: column;
    gap: var(--sp-8);
  }

  .check-circle {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    border: 2px solid var(--line);
    background: transparent;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
    margin-right: var(--sp-8);
    color: var(--ok);
    transition: all var(--dur-fast) var(--ease);
  }

  .check-circle.ticked {
    border-color: var(--ok);
    background: var(--ok-bg);
  }

  .item-name {
    flex: 1;
    color: var(--text);
  }

  .item-name.done {
    text-decoration: line-through;
    color: var(--text-muted);
  }

  .notes-box {
    display: flex;
    align-items: flex-start;
    gap: var(--sp-8);
    background: var(--surface-2);
    padding: var(--sp-12);
    border-radius: var(--r-sm);
    color: var(--text-soft);
  }

  .notes-icon {
    flex-shrink: 0;
    margin-top: 2px;
    color: var(--accent);
  }

  .actions-row {
    display: flex;
    gap: var(--sp-8);
    flex-wrap: wrap;
    margin-top: var(--sp-4);
  }

  .disclaimer {
    color: var(--text-muted);
  }
</style>
