<script>
  import { ClipboardCheck, CheckCircle2, Clock, AlertCircle, ArrowRight, Check } from '@lucide/svelte';

  export let data = {
    target: 'Household',
    spokenText: '',
    counts: { completed: 0, partial: 0, remaining: 0, total: 0 },
    items: []
  };

  export let onAction = (/** @type {string} */ _cmd) => {};

  // Active filter tab: 'all' | 'completed' | 'partial' | 'remaining'
  let activeTab = 'all';

  $: counts = data.counts || { completed: 0, partial: 0, remaining: 0, total: 0 };
  $: items = data.items || [];

  $: completedPercent = counts.total ? Math.round((counts.completed / counts.total) * 100) : 0;
  $: partialPercent = counts.total ? Math.round((counts.partial / counts.total) * 100) : 0;
  $: remainingPercent = counts.total ? Math.max(0, 100 - completedPercent - partialPercent) : 0;

  $: filteredItems = items.filter(item => {
    if (activeTab === 'all') return true;
    return item.status === activeTab;
  });
</script>

<div class="tracker-container" role="region" aria-label="Document and task tracker">
  <!-- Header Bar -->
  <div class="tracker-header">
    <div class="header-title">
      <ClipboardCheck size={18} class="header-icon" />
      <span class="text-label uppercase">Document & Task Tracker</span>
      {#if data.target && data.target !== 'Household' && data.target !== 'All Family Members'}
        <span class="target-badge">{data.target}</span>
      {/if}
    </div>
    <span class="total-counter text-small">{counts.total} Total Tracked</span>
  </div>

  <!-- Metric Badges Row (Clickable to switch tab) -->
  <div class="metrics-row" role="group" aria-label="Paperwork metrics">
    <button
      type="button"
      class="metric-card completed"
      class:selected={activeTab === 'completed'}
      on:click={() => (activeTab = activeTab === 'completed' ? 'all' : 'completed')}
      aria-pressed={activeTab === 'completed'}
    >
      <div class="metric-top">
        <CheckCircle2 size={15} />
        <span class="metric-label">Completed</span>
      </div>
      <div class="metric-value">{counts.completed}</div>
      <span class="metric-sub text-small">{completedPercent}% done</span>
    </button>

    <button
      type="button"
      class="metric-card partial"
      class:selected={activeTab === 'partial'}
      on:click={() => (activeTab = activeTab === 'partial' ? 'all' : 'partial')}
      aria-pressed={activeTab === 'partial'}
    >
      <div class="metric-top">
        <Clock size={15} />
        <span class="metric-label">Partial</span>
      </div>
      <div class="metric-value">{counts.partial}</div>
      <span class="metric-sub text-small">{partialPercent}% in progress</span>
    </button>

    <button
      type="button"
      class="metric-card remaining"
      class:selected={activeTab === 'remaining'}
      on:click={() => (activeTab = activeTab === 'remaining' ? 'all' : 'remaining')}
      aria-pressed={activeTab === 'remaining'}
    >
      <div class="metric-top">
        <AlertCircle size={15} />
        <span class="metric-label">Remaining</span>
      </div>
      <div class="metric-value">{counts.remaining}</div>
      <span class="metric-sub text-small">{remainingPercent}% action required</span>
    </button>
  </div>

  <!-- Tri-color Segmented Progress Bar -->
  <div class="progress-bar-wrap" aria-hidden="true">
    <div class="progress-track">
      {#if counts.completed > 0}
        <div class="segment completed" style="width: {completedPercent}%;"></div>
      {/if}
      {#if counts.partial > 0}
        <div class="segment partial" style="width: {partialPercent}%;"></div>
      {/if}
      {#if counts.remaining > 0}
        <div class="segment remaining" style="width: {remainingPercent}%;"></div>
      {/if}
    </div>
  </div>

  <!-- Interactive Filter Tabs -->
  <div class="filter-tabs" role="tablist" aria-label="Filter documents by status">
    <button
      type="button"
      role="tab"
      class="tab-btn"
      class:active={activeTab === 'all'}
      aria-selected={activeTab === 'all'}
      on:click={() => (activeTab = 'all')}
    >
      <span>All</span>
      <span class="tab-badge">{counts.total}</span>
    </button>

    <button
      type="button"
      role="tab"
      class="tab-btn completed"
      class:active={activeTab === 'completed'}
      aria-selected={activeTab === 'completed'}
      on:click={() => (activeTab = 'completed')}
    >
      <CheckCircle2 size={13} />
      <span>Completed</span>
      <span class="tab-badge">{counts.completed}</span>
    </button>

    <button
      type="button"
      role="tab"
      class="tab-btn partial"
      class:active={activeTab === 'partial'}
      aria-selected={activeTab === 'partial'}
      on:click={() => (activeTab = 'partial')}
    >
      <Clock size={13} />
      <span>Partial</span>
      <span class="tab-badge">{counts.partial}</span>
    </button>

    <button
      type="button"
      role="tab"
      class="tab-btn remaining"
      class:active={activeTab === 'remaining'}
      aria-selected={activeTab === 'remaining'}
      on:click={() => (activeTab = 'remaining')}
    >
      <AlertCircle size={13} />
      <span>Remaining</span>
      <span class="tab-badge">{counts.remaining}</span>
    </button>
  </div>

  <!-- Filtered Items List -->
  <div class="items-list" role="list">
    {#if filteredItems.length === 0}
      <div class="empty-list-state">
        <Check size={20} class="empty-icon" />
        <p class="text-body">
          {#if activeTab === 'remaining'}
            No remaining tasks or documents. All paperwork is healthy!
          {:else if activeTab === 'partial'}
            No documents expiring soon or in partial status.
          {:else if activeTab === 'completed'}
            No completed paperwork found for this filter.
          {:else}
            No paperwork or tasks found.
          {/if}
        </p>
      </div>
    {:else}
      {#each filteredItems as item}
        <div class="item-card {item.status}" role="listitem">
          <div class="item-left">
            <div class="status-icon-wrap {item.status}">
              {#if item.status === 'completed'}
                <CheckCircle2 size={16} />
              {:else if item.status === 'partial'}
                <Clock size={16} />
              {:else}
                <AlertCircle size={16} />
              {/if}
            </div>

            <div class="item-info">
              <div class="item-title-row">
                <strong class="item-title text-body">{item.title}</strong>
                <span class="cat-pill {item.category}">{item.category}</span>
                {#if item.member}
                  <span class="member-pill">{item.member}</span>
                {/if}
              </div>
              <span class="status-label text-small">{item.statusLabel}</span>
            </div>
          </div>

          {#if item.actionPrompt}
            <button
              type="button"
              class="action-btn {item.status}"
              on:click={() => onAction(item.actionPrompt)}
              title="Act on {item.title}"
            >
              <span>{item.status === 'completed' ? 'Details' : (item.category === 'task' ? 'Fix Task' : 'Renew')}</span>
              <ArrowRight size={13} />
            </button>
          {/if}
        </div>
      {/each}
    {/if}
  </div>

  <p class="disclaimer-text text-label">Glean paperwork tracker • Guidance only, verify on official portals.</p>
</div>

<style>
  .tracker-container {
    display: flex;
    flex-direction: column;
    gap: var(--sp-12);
    width: 100%;
  }

  .tracker-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--sp-8);
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: var(--sp-8);
    color: var(--text-muted);
  }

  .uppercase {
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .target-badge {
    background: var(--surface-3);
    color: var(--accent);
    padding: 2px 8px;
    border-radius: 999px;
    font-size: var(--fs-label);
    font-weight: 600;
  }

  .total-counter {
    color: var(--text-muted);
  }

  /* Metric summary cards row */
  .metrics-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--sp-8);
  }

  .metric-card {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    padding: var(--sp-8) var(--sp-12);
    border-radius: var(--radius-md);
    background: var(--surface-2);
    border: 1px solid var(--border-subtle);
    cursor: pointer;
    transition: all var(--dur-fast) var(--ease);
    text-align: left;
  }

  .metric-card:hover {
    background: var(--surface-3);
    border-color: var(--border-strong);
  }

  .metric-card.selected {
    outline: 2px solid currentColor;
    background: var(--surface-3);
  }

  .metric-card.completed {
    color: var(--ok);
  }

  .metric-card.partial {
    color: #eab308;
  }

  .metric-card.remaining {
    color: var(--error);
  }

  .metric-top {
    display: flex;
    align-items: center;
    gap: var(--sp-6);
    font-size: var(--fs-label);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .metric-value {
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1.2;
    margin-top: 2px;
  }

  .metric-sub {
    color: var(--text-muted);
    font-size: var(--fs-label);
    margin-top: 2px;
  }

  /* Progress track */
  .progress-bar-wrap {
    width: 100%;
    padding: var(--sp-2) 0;
  }

  .progress-track {
    display: flex;
    height: 6px;
    border-radius: 999px;
    background: var(--surface-3);
    overflow: hidden;
    gap: 2px;
  }

  .segment.completed {
    background: var(--ok);
  }

  .segment.partial {
    background: #eab308;
  }

  .segment.remaining {
    background: var(--error);
  }

  /* Interactive Filter Tabs */
  .filter-tabs {
    display: flex;
    align-items: center;
    gap: var(--sp-6);
    padding: var(--sp-4) 0;
    border-bottom: 1px solid var(--border-subtle);
    overflow-x: auto;
  }

  .tab-btn {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-6);
    padding: var(--sp-6) var(--sp-12);
    border-radius: 999px;
    font-size: var(--fs-label);
    font-weight: 600;
    background: var(--surface-2);
    color: var(--text-soft);
    border: 1px solid var(--border-subtle);
    cursor: pointer;
    transition: all var(--dur-fast) var(--ease);
    white-space: nowrap;
  }

  .tab-btn:hover {
    background: var(--surface-3);
    color: var(--text);
  }

  .tab-btn.active {
    background: var(--text);
    color: var(--surface-1);
    border-color: var(--text);
  }

  .tab-btn.active.completed {
    background: var(--ok);
    color: #fff;
    border-color: var(--ok);
  }

  .tab-btn.active.partial {
    background: #eab308;
    color: #000;
    border-color: #eab308;
  }

  .tab-btn.active.remaining {
    background: var(--error);
    color: #fff;
    border-color: var(--error);
  }

  .tab-badge {
    padding: 1px 6px;
    border-radius: 999px;
    background: rgba(0, 0, 0, 0.15);
    font-size: 0.72rem;
  }

  .tab-btn.active .tab-badge {
    background: rgba(255, 255, 255, 0.25);
  }

  .tab-btn.active.partial .tab-badge {
    background: rgba(0, 0, 0, 0.2);
  }

  /* Item cards */
  .items-list {
    display: flex;
    flex-direction: column;
    gap: var(--sp-6);
    max-height: 280px;
    overflow-y: auto;
    padding-right: var(--sp-4);
  }

  .item-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--sp-8) var(--sp-12);
    border-radius: var(--radius-md);
    background: var(--surface-2);
    border: 1px solid var(--border-subtle);
    transition: background var(--dur-fast) var(--ease);
  }

  .item-card:hover {
    background: var(--surface-3);
  }

  .item-card.completed {
    border-left: 3px solid var(--ok);
  }

  .item-card.partial {
    border-left: 3px solid #eab308;
  }

  .item-card.remaining {
    border-left: 3px solid var(--error);
  }

  .item-left {
    display: flex;
    align-items: center;
    gap: var(--sp-10);
    min-width: 0;
  }

  .status-icon-wrap.completed {
    color: var(--ok);
  }

  .status-icon-wrap.partial {
    color: #eab308;
  }

  .status-icon-wrap.remaining {
    color: var(--error);
  }

  .item-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  .item-title-row {
    display: flex;
    align-items: center;
    gap: var(--sp-6);
    flex-wrap: wrap;
  }

  .item-title {
    color: var(--text);
  }

  .cat-pill {
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    background: var(--surface-3);
    color: var(--text-muted);
  }

  .member-pill {
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 500;
    background: rgba(14, 165, 233, 0.12);
    color: #0284c7;
  }

  .status-label {
    color: var(--text-muted);
  }

  /* One-click action button */
  .action-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 5px 10px;
    border-radius: var(--radius-sm);
    font-size: var(--fs-label);
    font-weight: 600;
    background: var(--surface-3);
    border: 1px solid var(--border-subtle);
    color: var(--text);
    cursor: pointer;
    flex-shrink: 0;
    transition: all var(--dur-fast) var(--ease);
  }

  .action-btn:hover {
    background: var(--surface-1);
    border-color: var(--border-strong);
  }

  .action-btn.partial {
    color: #b45309;
    background: rgba(234, 179, 8, 0.12);
    border-color: rgba(234, 179, 8, 0.3);
  }

  .action-btn.partial:hover {
    background: rgba(234, 179, 8, 0.22);
  }

  .action-btn.remaining {
    color: var(--error);
    background: rgba(239, 68, 68, 0.12);
    border-color: rgba(239, 68, 68, 0.3);
  }

  .action-btn.remaining:hover {
    background: rgba(239, 68, 68, 0.22);
  }

  .empty-list-state {
    display: flex;
    align-items: center;
    gap: var(--sp-8);
    padding: var(--sp-16);
    color: var(--ok);
    background: var(--surface-2);
    border-radius: var(--radius-md);
  }

  .empty-icon {
    flex-shrink: 0;
  }

  .disclaimer-text {
    color: var(--text-muted);
    margin-top: var(--sp-4);
  }
</style>
