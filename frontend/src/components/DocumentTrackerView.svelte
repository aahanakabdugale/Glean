<script>
  import { onMount } from 'svelte';
  import { activeView, activePersona, alexaMicEnabled, settings } from '../lib/store.js';
  import { callGetDocumentTracker, callCompleteTask } from '../lib/mcp.js';
  import { cleanTextForSpeech } from '../lib/speech.js';
  import {
    ClipboardCheck,
    CheckCircle2,
    Clock,
    AlertCircle,
    ArrowLeft,
    RotateCw,
    Search,
    X,
    ChevronRight,
    Check
  } from '@lucide/svelte';

  export let onAction = (/** @type {string} */ _prompt) => {};

  let loading = true;
  let error = '';
  let activeTab = 'all'; // 'all' | 'completed' | 'partial' | 'remaining'
  let searchQuery = '';
  let trackerData = {
    target: 'Household',
    spokenText: '',
    counts: { completed: 0, partial: 0, remaining: 0, total: 0 },
    items: []
  };

  const familyMembers = ['all', 'Chandler', 'Amy', 'Justin', 'Riley', 'Jace', 'Gwen'];

  async function loadTracker() {
    loading = true;
    error = '';
    try {
      const persona = $activePersona && $activePersona !== 'all' ? $activePersona : '';
      const res = await callGetDocumentTracker(persona);
      if (res && res.resultData) {
        trackerData = res.resultData;
        if (res.spokenText) {
          speak(res.spokenText);
        }
      }
    } catch (e) {
      error = e.message || 'Failed to load document tracker';
    } finally {
      loading = false;
    }
  }

  function speak(text) {
    if (!$alexaMicEnabled || !$settings.voiceEnabled) return;
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const clean = cleanTextForSpeech(text);
    if (!clean) return;
    const utt = new SpeechSynthesisUtterance(clean);
    utt.rate = 1.05;
    window.speechSynthesis.speak(utt);
  }

  $: rawItems = trackerData.items || [];
  $: items = (() => {
    const seen = new Set();
    const res = [];
    for (const item of rawItems) {
      const key = `${item.category}:${(item.member || '').toLowerCase()}:${(item.title || '').toLowerCase()}:${item.status}`;
      if (!seen.has(key)) {
        seen.add(key);
        res.push(item);
      }
    }
    return res;
  })();

  $: computedCompleted = items.filter(i => i.status === 'completed').length;
  $: computedPartial = items.filter(i => i.status === 'partial').length;
  $: computedRemaining = items.filter(i => i.status === 'remaining').length;
  $: computedTotal = items.length;

  $: counts = {
    completed: computedCompleted,
    partial: computedPartial,
    remaining: computedRemaining,
    total: computedTotal
  };

  $: completedPercent = counts.total ? Math.round((counts.completed / counts.total) * 100) : 0;
  $: partialPercent = counts.total ? Math.round((counts.partial / counts.total) * 100) : 0;
  $: remainingPercent = counts.total ? Math.max(0, 100 - completedPercent - partialPercent) : 0;

  // Search and Tab filtering
  $: filteredItems = items.filter(item => {
    if (activeTab !== 'all' && item.status !== activeTab) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = (item.title || '').toLowerCase().includes(q);
      const matchMember = (item.member || '').toLowerCase().includes(q);
      const matchStatus = (item.statusLabel || '').toLowerCase().includes(q);
      return matchTitle || matchMember || matchStatus;
    }
    return true;
  });

  onMount(() => {
    loadTracker();
  });

  function selectPersona(mem) {
    activePersona.set(mem);
    loadTracker();
  }

  async function handleItemAction(item) {
    if (item.category === 'task' && item.status === 'remaining') {
      try {
        await callCompleteTask(item.title, item.member || '');
        loadTracker();
        return;
      } catch (e) {}
    }
    if (item.actionPrompt) {
      onAction(item.actionPrompt);
    }
  }
</script>

<div class="dash-container" role="region" aria-label="Document and Task Tracker">
  <!-- Clean Header (Identical to DashboardView) -->
  <header class="dash-header">
    <div class="header-text-block">
      <h1 class="dash-title">Document &amp; Task Tracker</h1>
      <p class="dash-subtitle">Overview of completed, partial, and remaining family paperwork and deadlines.</p>
    </div>

    <div class="header-actions">
      <button
        type="button"
        class="hdr-btn secondary"
        on:click={loadTracker}
        disabled={loading}
        title="Refresh tracker data"
      >
        <RotateCw size={15} class={loading ? 'spin' : ''} />
        <span>Refresh</span>
      </button>

      <button
        type="button"
        class="hdr-btn primary"
        on:click={() => activeView.set('chat')}
      >
        <ArrowLeft size={16} />
        <span>Ask Glean</span>
      </button>
    </div>
  </header>

  {#if loading}
    <div class="state-panel">
      <RotateCw size={24} class="spin" />
      <span>Loading document records &amp; deadlines…</span>
    </div>
  {:else if error}
    <div class="state-panel error">
      <AlertCircle size={20} />
      <span>{error}</span>
      <button type="button" class="hdr-btn secondary" on:click={loadTracker}>Retry</button>
    </div>
  {:else}
    <!-- 1. Unified Executive Metrics Strip (Identical to DashboardView) -->
    <div class="metrics-strip">
      <!-- Completed -->
      <button
        type="button"
        class="metric-cell"
        class:selected={activeTab === 'completed'}
        on:click={() => (activeTab = activeTab === 'completed' ? 'all' : 'completed')}
      >
        <div class="metric-top">
          <CheckCircle2 size={18} class="metric-icon icon-ok" />
          <span class="metric-label">Completed (Done)</span>
        </div>
        <div class="metric-bottom">
          <span class="metric-num">{counts.completed}</span>
          <span class="vr-badge ok">{completedPercent}% Resolved</span>
        </div>
      </button>

      <!-- Partial -->
      <button
        type="button"
        class="metric-cell"
        class:selected={activeTab === 'partial'}
        on:click={() => (activeTab = activeTab === 'partial' ? 'all' : 'partial')}
      >
        <div class="metric-top">
          <Clock size={18} class="metric-icon icon-soon" />
          <span class="metric-label">Partial (Expiring Soon)</span>
        </div>
        <div class="metric-bottom">
          <span class="metric-num">{counts.partial}</span>
          <span class="vr-badge soon">{partialPercent}% In Progress</span>
        </div>
      </button>

      <!-- Remaining -->
      <button
        type="button"
        class="metric-cell"
        class:selected={activeTab === 'remaining'}
        on:click={() => (activeTab = activeTab === 'remaining' ? 'all' : 'remaining')}
      >
        <div class="metric-top">
          <AlertCircle size={18} class="metric-icon icon-urgent" />
          <span class="metric-label">Remaining (Urgent)</span>
        </div>
        <div class="metric-bottom">
          <span class="metric-num">{counts.remaining}</span>
          <span class="vr-badge {counts.remaining > 0 ? 'urgent' : 'ok'}">{counts.remaining > 0 ? 'Action Needed' : 'All Clear'}</span>
        </div>
      </button>

      <!-- Total Tracked -->
      <button
        type="button"
        class="metric-cell"
        class:selected={activeTab === 'all'}
        on:click={() => (activeTab = 'all')}
      >
        <div class="metric-top">
          <ClipboardCheck size={18} class="metric-icon icon-info" />
          <span class="metric-label">Total Records</span>
        </div>
        <div class="metric-bottom">
          <span class="metric-num">{counts.total}</span>
          <span class="vr-badge ok">Audited</span>
        </div>
      </button>
    </div>

    <!-- 2. Member & Filter Strip (Matching Dashboard filter pill styling) -->
    <div class="filter-strip-row">
      <!-- Member selector -->
      <div class="filter-group">
        <span class="filter-group-label">FAMILY MEMBER:</span>
        <div class="region-tabs">
          {#each familyMembers as mem}
            <button
              type="button"
              class="tab-btn"
              class:active={($activePersona || 'all').toLowerCase() === mem.toLowerCase()}
              on:click={() => selectPersona(mem)}
            >
              {mem === 'all' ? 'Whole Family' : mem}
            </button>
          {/each}
        </div>
      </div>

      <!-- Status filter tabs -->
      <div class="filter-group">
        <span class="filter-group-label">STATUS:</span>
        <div class="region-tabs">
          <button
            type="button"
            class="tab-btn"
            class:active={activeTab === 'all'}
            on:click={() => (activeTab = 'all')}
          >
            All ({counts.total})
          </button>
          <button
            type="button"
            class="tab-btn"
            class:active={activeTab === 'completed'}
            on:click={() => (activeTab = 'completed')}
          >
            Completed ({counts.completed})
          </button>
          <button
            type="button"
            class="tab-btn"
            class:active={activeTab === 'partial'}
            on:click={() => (activeTab = 'partial')}
          >
            Partial ({counts.partial})
          </button>
          <button
            type="button"
            class="tab-btn"
            class:active={activeTab === 'remaining'}
            on:click={() => (activeTab = 'remaining')}
          >
            Remaining ({counts.remaining})
          </button>
        </div>
      </div>
    </div>

    <!-- 3. Flat Panel (NO nested boxes — Clean hairline dividers!) -->
    <section class="flat-panel" aria-label="Paperwork and deadlines list">
      <div class="panel-top scheme-panel-top">
        <div class="panel-heading-block">
          <div class="title-with-badge">
            <h2 class="panel-title">Tracked Paperwork &amp; Deadlines</h2>
            <span class="vr-badge ok">{filteredItems.length} Records</span>
          </div>
          <p class="panel-desc">Valid documents (&gt;30d) are Completed; expiring soon (&le;30d) are Partial; urgent tasks or expired paperwork are Remaining.</p>
        </div>

        <!-- Search input box -->
        <div class="search-input-wrap">
          <Search size={15} class="search-icon" />
          <input
            type="text"
            placeholder="Search documents or tasks..."
            bind:value={searchQuery}
            class="search-field"
            aria-label="Filter documents by text"
          />
          {#if searchQuery}
            <button
              type="button"
              class="clear-btn"
              on:click={() => (searchQuery = '')}
              aria-label="Clear filter"
            >
              <X size={13} />
            </button>
          {/if}
        </div>
      </div>

      <!-- Flat List -->
      <div class="flat-list">
        {#if filteredItems.length === 0}
          <div class="empty-row">
            <Check size={20} class="empty-check" />
            <span class="empty-text">
              {#if activeTab === 'remaining'}
                No remaining items or expired paperwork. Everything is on schedule!
              {:else if activeTab === 'partial'}
                No items in partial status or expiring within 30 days.
              {:else if activeTab === 'completed'}
                No completed paperwork found matching your selection.
              {:else}
                No records matching your search query.
              {/if}
            </span>
          </div>
        {:else}
          {#each filteredItems as item}
            {@const level = item.status === 'remaining' ? 'urgent' : (item.status === 'partial' ? 'soon' : 'ok')}
            <div class="flat-row item-flat-row">
              <div class="row-main">
                <div class="row-title">
                  <span class="title-bold">{item.member}</span>
                  <span class="title-sep">·</span>
                  <span class="title-sub">{item.title}</span>
                  <span class="category-tag">{item.category}</span>
                </div>
                <div class="row-meta">
                  <span class="meta-label">{item.statusLabel}</span>
                  {#if item.date}
                    <span class="meta-dot">·</span>
                    <span class="meta-date">{item.category === 'document' ? 'Expires' : 'Due'}: {item.date}</span>
                  {/if}
                </div>
              </div>

              <div class="row-end">
                <span class="vr-badge {level}">
                  {item.status === 'completed' ? 'Completed' : (item.status === 'partial' ? 'Partial' : 'Remaining')}
                </span>

                {#if item.actionPrompt}
                  <button
                    type="button"
                    class="row-action-btn {level}"
                    on:click={() => handleItemAction(item)}
                  >
                    <span>
                      {#if item.category === 'task' && item.status === 'remaining'}
                        Mark Done
                      {:else if item.status === 'remaining'}
                        Fix Now
                      {:else if item.status === 'partial'}
                        Renew
                      {:else}
                        Details
                      {/if}
                    </span>
                    <ChevronRight size={14} />
                  </button>
                {/if}
              </div>
            </div>
          {/each}
        {/if}
      </div>
    </section>
  {/if}
</div>

<style>
  /* ================= DASHBOARD LAYOUT & TOKENS ================= */
  .dash-container {
    width: 100%;
    max-width: 1280px;
    margin: 0 auto;
    padding: 32px 32px 64px 32px;
    display: flex;
    flex-direction: column;
    gap: 28px;
    animation: fade-in var(--dur-normal) var(--ease);
  }

  @keyframes fade-in {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
  }

  /* Header */
  .dash-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 24px;
    flex-wrap: wrap;
  }

  .header-text-block {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .dash-title {
    font-family: var(--font-ui);
    font-size: 32px;
    font-weight: 600;
    line-height: 1.2;
    color: var(--text);
    margin: 0;
  }

  .dash-subtitle {
    font-family: var(--font-ui);
    font-size: 16px;
    color: var(--text-muted);
    margin: 0;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: var(--sp-8);
  }

  .hdr-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 40px;
    padding: 0 18px;
    border-radius: var(--r-pill);
    font-family: var(--font-ui);
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--dur-fast) var(--ease);
  }

  .hdr-btn.primary {
    background: var(--accent);
    color: var(--btn-primary-text);
    border: none;
  }
  .hdr-btn.primary:hover {
    background: var(--accent-2);
    transform: translateY(-1px);
  }

  .hdr-btn.secondary {
    background: var(--surface);
    color: var(--text);
    border: 1px solid var(--line);
  }
  .hdr-btn.secondary:hover {
    background: var(--surface-2);
    transform: translateY(-1px);
  }

  .spin {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* State Panel */
  .state-panel {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 64px 24px;
    background: var(--surface);
    border: 1px solid var(--line-soft);
    border-radius: var(--r-card);
    color: var(--text-muted);
    font-size: 16px;
  }

  .state-panel.error {
    color: var(--urgent);
    border-color: rgba(239, 68, 68, 0.2);
    background: rgba(239, 68, 68, 0.04);
  }

  /* ================= 1. METRICS STRIP (Unified Container) ================= */
  .metrics-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    background: var(--surface);
    border: 1px solid var(--line-soft);
    border-radius: var(--r-card);
    box-shadow: var(--shadow-card);
    overflow: hidden;
  }

  .metric-cell {
    padding: 22px 26px;
    border: none;
    border-right: 1px solid var(--line-soft);
    background: transparent;
    display: flex;
    flex-direction: column;
    gap: 12px;
    cursor: pointer;
    text-align: left;
    transition: background var(--dur-fast) var(--ease);
  }
  .metric-cell:last-child {
    border-right: none;
  }
  .metric-cell:hover {
    background: var(--surface-2);
  }
  .metric-cell.selected {
    background: var(--surface-2);
  }

  .metric-top {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .metric-icon {
    flex-shrink: 0;
  }
  .icon-info { color: var(--accent); }
  .icon-urgent { color: var(--urgent); }
  .icon-soon { color: var(--soon); }
  .icon-ok { color: var(--ok); }

  .metric-label {
    font-size: 15px;
    font-weight: 500;
    color: var(--text-muted);
  }

  .metric-bottom {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 8px;
  }

  .metric-num {
    font-size: 36px;
    font-weight: 600;
    line-height: 1;
    color: var(--text);
  }

  /* ================= 2. FILTER STRIP ================= */
  .filter-strip-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    flex-wrap: wrap;
    background: var(--surface);
    border: 1px solid var(--line-soft);
    border-radius: var(--r-card);
    box-shadow: var(--shadow-card);
    padding: 16px 26px;
  }

  .filter-group {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .filter-group-label {
    font-size: 12px;
    font-weight: 700;
    color: var(--text-muted);
    letter-spacing: 0.06em;
    white-space: nowrap;
  }

  .region-tabs {
    display: inline-flex;
    align-items: center;
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
    border-radius: var(--r-pill);
    padding: 3px;
    gap: 4px;
    flex-shrink: 0;
  }

  .tab-btn {
    border: none;
    background: transparent;
    color: var(--text-muted);
    font-family: var(--font-ui);
    font-size: 13.5px;
    font-weight: 500;
    padding: 6px 14px;
    border-radius: var(--r-pill);
    cursor: pointer;
    transition: all var(--dur-fast) var(--ease);
    display: inline-flex;
    align-items: center;
    white-space: nowrap;
  }

  .tab-btn:hover {
    color: var(--text);
  }

  .tab-btn.active {
    background: var(--surface);
    color: var(--accent);
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  }

  /* ================= 3. FLAT PANEL ================= */
  .flat-panel {
    background: var(--surface);
    border: 1px solid var(--line-soft);
    border-radius: var(--r-card);
    box-shadow: var(--shadow-card);
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .panel-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    padding: 22px 26px 18px 26px;
    border-bottom: 1px solid var(--line-soft);
  }

  .scheme-panel-top {
    flex-wrap: wrap;
    gap: 16px;
    align-items: center;
  }

  .panel-heading-block {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .title-with-badge {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  .panel-title {
    font-family: var(--font-ui);
    font-size: 20px;
    font-weight: 600;
    color: var(--text);
    margin: 0;
    line-height: 1.3;
  }

  .panel-desc {
    font-size: 15px;
    color: var(--text-muted);
    margin: 3px 0 0 0;
  }

  /* Search Input Box */
  .search-input-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
    border-radius: var(--r-pill);
    padding: 6px 14px;
    min-width: 260px;
    transition: border-color var(--dur-fast) var(--ease);
  }

  .search-input-wrap:focus-within {
    border-color: var(--accent);
  }

  :global(.search-icon) {
    color: var(--text-muted);
    flex-shrink: 0;
  }

  .search-field {
    background: transparent;
    border: none;
    outline: none;
    color: var(--text);
    font-family: var(--font-ui);
    font-size: 14px;
    width: 100%;
  }

  .clear-btn {
    background: transparent;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    padding: 0;
  }

  /* Flat List & Rows (Clean hairline dividers) */
  .flat-list {
    display: flex;
    flex-direction: column;
  }

  .flat-row {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 16px 26px;
    background: transparent;
    border: none;
    border-bottom: 1px solid var(--line-soft);
    text-align: left;
    transition: background var(--dur-fast) var(--ease);
  }
  .flat-row:last-child {
    border-bottom: none;
  }
  .flat-row:hover {
    background: var(--surface-2);
  }

  .row-main {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
  }

  .row-title {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .title-bold {
    font-size: 15.5px;
    font-weight: 600;
    color: var(--text);
  }

  .title-sep {
    color: var(--text-subtle);
  }

  .title-sub {
    font-size: 15.5px;
    font-weight: 500;
    color: var(--text-muted);
  }

  .category-tag {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    padding: 1px 7px;
    border-radius: var(--r-pill);
    background: var(--surface-2);
    color: var(--text-muted);
    border: 1px solid var(--line-soft);
    letter-spacing: 0.04em;
  }

  .row-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    color: var(--text-muted);
  }

  .meta-dot {
    color: var(--text-subtle);
  }

  .meta-label {
    font-weight: 500;
  }

  .row-end {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-shrink: 0;
  }

  .row-action-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 6px 14px;
    border-radius: var(--r-pill);
    font-family: var(--font-ui);
    font-size: 13.5px;
    font-weight: 500;
    cursor: pointer;
    background: var(--surface);
    border: 1px solid var(--line-soft);
    color: var(--text);
    transition: all var(--dur-fast) var(--ease);
  }

  .row-action-btn:hover {
    background: var(--surface-2);
    border-color: var(--line);
    transform: translateY(-1px);
  }

  .row-action-btn.urgent {
    color: var(--urgent);
    border-color: rgba(239, 68, 68, 0.3);
    background: rgba(239, 68, 68, 0.06);
  }
  .row-action-btn.urgent:hover {
    background: rgba(239, 68, 68, 0.12);
  }

  .row-action-btn.soon {
    color: #b45309;
    border-color: rgba(234, 179, 8, 0.3);
    background: rgba(234, 179, 8, 0.06);
  }
  .row-action-btn.soon:hover {
    background: rgba(234, 179, 8, 0.12);
  }

  .empty-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 48px 26px;
    color: var(--ok);
  }

  .empty-check {
    flex-shrink: 0;
  }

  .empty-text {
    font-size: 15px;
    color: var(--text-muted);
  }

  /* Responsive Adjustments */
  @media (max-width: 900px) {
    .metrics-strip {
      grid-template-columns: repeat(2, 1fr);
    }
    .metric-cell:nth-child(2) {
      border-right: none;
    }
    .metric-cell:nth-child(1),
    .metric-cell:nth-child(2) {
      border-bottom: 1px solid var(--line-soft);
    }
    .filter-strip-row {
      flex-direction: column;
      align-items: flex-start;
    }
  }

  @media (max-width: 600px) {
    .dash-container {
      padding: 20px 16px 48px 16px;
    }
    .metrics-strip {
      grid-template-columns: 1fr;
    }
    .metric-cell {
      border-right: none;
      border-bottom: 1px solid var(--line-soft);
    }
    .metric-cell:last-child {
      border-bottom: none;
    }
  }
</style>
