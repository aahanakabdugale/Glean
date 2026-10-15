<script>
  import { onMount } from 'svelte';
  import { activeView } from '../lib/store.js';
  import { callGetFamilyDashboard } from '../lib/mcp.js';
  import { urgencyOf, formatDaysLeft } from '../lib/urgency.js';
  import {
    Users,
    FileText,
    Calendar,
    ShieldCheck,
    RotateCw,
    ArrowLeft,
    AlertCircle,
    ChevronRight
  } from '@lucide/svelte';

  export let onAction = (prompt) => {};

  let loading = true;
  let error = '';
  let dashboardData = {
    metrics: {
      totalMembers: 6,
      totalDocs: 18,
      expiringDocs: 3,
      urgentDocs: 1,
      pendingTasks: 4,
      upcomingTasks: 3,
      overdueTasks: 0,
      schemeOpportunities: 4,
    },
    members: [],
    expiring: [],
    tasks: [],
    benefits: [],
    raw: '',
  };

  async function loadDashboard() {
    loading = true;
    error = '';
    try {
      const res = await callGetFamilyDashboard();
      if (res && res.resultData) {
        dashboardData = res.resultData;
      }
    } catch (err) {
      error = err.message || 'Failed to load dashboard';
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    loadDashboard();
  });

  function handleActionClick(prompt) {
    onAction(prompt);
  }

  const schemes = [
    {
      title: 'Ayushman Vay Vandana (AB PM-JAY)',
      beneficiary: 'Amy & Chandler (Age 70+)',
      detail: '₹5 Lakh annual health coverage with zero waiting period',
      status: 'ok',
      badge: 'May Qualify',
      prompt: 'Check scheme checklist for Ayushman card'
    },
    {
      title: 'Senior Citizens Savings Scheme (SCSS)',
      beneficiary: 'Chandler (Age 60+)',
      detail: '8.2% sovereign quarterly interest at post offices and banks',
      status: 'ok',
      badge: 'May Qualify',
      prompt: 'Plan the SCSS application for Chandler'
    },
    {
      title: 'Atal Pension Yojana (APY)',
      beneficiary: 'Justin (Age window transition)',
      detail: 'Guaranteed government-backed lifelong monthly pension',
      status: 'soon',
      badge: 'Age Window',
      prompt: 'What schemes does Justin qualify for?'
    },
    {
      title: 'Sukanya Samriddhi Yojana (SSY)',
      beneficiary: 'Family Dependents',
      detail: 'High-yield sovereign tax-free compounding savings',
      status: 'info',
      badge: 'Eligible',
      prompt: 'Check checklist for Sukanya Samriddhi Yojana'
    }
  ];
</script>

<div class="dash-container" role="region" aria-label="Family Dashboard">
  <!-- Clean Header -->
  <header class="dash-header">
    <div class="header-text-block">
      <h1 class="dash-title">Family Dashboard</h1>
      <p class="dash-subtitle">Overview of your family’s documents, upcoming tasks, and government schemes.</p>
    </div>

    <div class="header-actions">
      <button
        type="button"
        class="hdr-btn secondary"
        on:click={loadDashboard}
        disabled={loading}
        title="Refresh data"
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
        <span>Voice Assistant</span>
      </button>
    </div>
  </header>

  {#if loading}
    <div class="state-panel">
      <RotateCw size={24} class="spin" />
      <span>Loading family data…</span>
    </div>
  {:else if error}
    <div class="state-panel error">
      <AlertCircle size={20} />
      <span>{error}</span>
      <button type="button" class="hdr-btn secondary" on:click={loadDashboard}>Retry</button>
    </div>
  {:else}
    <!-- 1. Unified Executive Metrics Strip (Single sleek bar, NOT separate cards!) -->
    <div class="metrics-strip">
      <button
        type="button"
        class="metric-cell"
        on:click={() => handleActionClick("List all family members")}
      >
        <div class="metric-top">
          <Users size={18} class="metric-icon icon-info" />
          <span class="metric-label">Family Members</span>
        </div>
        <div class="metric-bottom">
          <span class="metric-num">{dashboardData.metrics.totalMembers || dashboardData.members.length || 6}</span>
          <span class="vr-badge ok">Tracked</span>
        </div>
      </button>

      <button
        type="button"
        class="metric-cell"
        on:click={() => handleActionClick("What documents are expiring soon?")}
      >
        <div class="metric-top">
          <FileText size={18} class="metric-icon icon-urgent" />
          <span class="metric-label">Expiring Documents</span>
        </div>
        <div class="metric-bottom">
          <span class="metric-num">{dashboardData.metrics.expiringDocs || 3}</span>
          <span class="vr-badge urgent">1 Urgent</span>
        </div>
      </button>

      <button
        type="button"
        class="metric-cell"
        on:click={() => handleActionClick("What tasks and deadlines are upcoming?")}
      >
        <div class="metric-top">
          <Calendar size={18} class="metric-icon icon-soon" />
          <span class="metric-label">Upcoming Tasks</span>
        </div>
        <div class="metric-bottom">
          <span class="metric-num">{dashboardData.metrics.pendingTasks || 4}</span>
          <span class="vr-badge soon">Next 30d</span>
        </div>
      </button>

      <button
        type="button"
        class="metric-cell"
        on:click={() => handleActionClick("Check scheme eligibility for Chandler")}
      >
        <div class="metric-top">
          <ShieldCheck size={18} class="metric-icon icon-ok" />
          <span class="metric-label">Scheme Matches</span>
        </div>
        <div class="metric-bottom">
          <span class="metric-num">{dashboardData.metrics.schemeOpportunities || 4}</span>
          <span class="vr-badge ok">Qualified</span>
        </div>
      </button>
    </div>

    <!-- 2. Flat Content Panels (NO CARDS INSIDE CARDS — Clean hairline dividers!) -->
    <div class="content-columns">
      <!-- Expiring Documents Panel -->
      <section class="flat-panel" aria-label="Expiring documents">
        <div class="panel-top">
          <div>
            <h2 class="panel-title">Expiring Documents</h2>
            <p class="panel-desc">Documents due for renewal within 60 days</p>
          </div>
          <button
            type="button"
            class="link-action"
            on:click={() => handleActionClick("What documents are expiring soon?")}
          >
            <span>View all</span>
            <ChevronRight size={14} />
          </button>
        </div>

        <div class="flat-list">
          {#each dashboardData.expiring as doc}
            {@const level = urgencyOf(doc.daysLeft)}
            <button
              type="button"
              class="flat-row"
              on:click={() => handleActionClick(`What documents are expiring soon for ${doc.member || doc.owner}?`)}
            >
              <div class="row-main">
                <div class="row-title">
                  <span class="title-bold">{doc.member || doc.owner || 'Family'}</span>
                  <span class="title-sep">·</span>
                  <span class="title-sub">{doc.docType}</span>
                </div>
                <span class="row-meta">Expires {doc.expiryDate}</span>
              </div>
              <div class="row-end">
                <span class="vr-badge {level}">{formatDaysLeft(doc.daysLeft) || doc.status || 'Active'}</span>
                <ChevronRight size={16} class="arrow" />
              </div>
            </button>
          {/each}
        </div>
      </section>

      <!-- Upcoming Deadlines Panel -->
      <section class="flat-panel" aria-label="Upcoming deadlines">
        <div class="panel-top">
          <div>
            <h2 class="panel-title">Upcoming Deadlines</h2>
            <p class="panel-desc">Scheduled renewals and paperwork tasks</p>
          </div>
          <button
            type="button"
            class="link-action"
            on:click={() => handleActionClick("What tasks and deadlines are upcoming?")}
          >
            <span>View all</span>
            <ChevronRight size={14} />
          </button>
        </div>

        <div class="flat-list">
          {#each dashboardData.tasks as task}
            {@const level = task.daysLeft && task.daysLeft <= 7 ? 'urgent' : 'soon'}
            <button
              type="button"
              class="flat-row"
              on:click={() => handleActionClick("What tasks are coming up in the next 30 days?")}
            >
              <div class="row-main">
                <div class="row-title">
                  <span class="title-bold">{task.title}</span>
                </div>
                <span class="row-meta">Due {task.dueDate} {task.member ? `· ${task.member}` : ''}</span>
              </div>
              <div class="row-end">
                <span class="vr-badge {level}">{formatDaysLeft(task.daysLeft) || task.status || 'Scheduled'}</span>
                <ChevronRight size={16} class="arrow" />
              </div>
            </button>
          {/each}
        </div>
      </section>
    </div>

    <!-- 3. Government Scheme Matches Panel (Clean Flat Rows) -->
    <section class="flat-panel" aria-label="Government scheme opportunities">
      <div class="panel-top">
        <div>
          <h2 class="panel-title">Government Scheme Matches</h2>
          <p class="panel-desc">Benefits identified for your family’s age and eligibility profiles</p>
        </div>
        <span class="vr-badge ok">8 Tracked</span>
      </div>

      <div class="flat-list">
        {#each schemes as s}
          <button
            type="button"
            class="flat-row scheme-row"
            on:click={() => handleActionClick(s.prompt)}
          >
            <div class="row-main">
              <div class="row-title">
                <span class="title-bold">{s.title}</span>
                <span class="title-sep">·</span>
                <span class="title-target">{s.beneficiary}</span>
              </div>
              <span class="row-meta">{s.detail}</span>
            </div>
            <div class="row-end">
              <span class="vr-badge {s.status}">{s.badge}</span>
              <span class="action-text">Check ›</span>
            </div>
          </button>
        {/each}
      </div>
    </section>
  {/if}
</div>

<style>
  /* ================= DASHBOARD LAYOUT ================= */
  .dash-container {
    width: 100%;
    max-width: 1180px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 28px;
    padding: var(--sp-12) 0 var(--sp-48) 0;
  }

  /* Header */
  .dash-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: var(--sp-16);
    padding-bottom: var(--sp-4);
  }

  .header-text-block {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .dash-title {
    font-family: var(--font-ui);
    font-size: 30px;
    font-weight: 600;
    line-height: 1.2;
    color: var(--text);
    margin: 0;
  }

  .dash-subtitle {
    font-family: var(--font-ui);
    font-size: 15px;
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
    height: 38px;
    padding: 0 16px;
    border-radius: var(--r-pill);
    font-family: var(--font-ui);
    font-size: 14px;
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
    padding: 20px 24px;
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
    font-size: 14px;
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
    font-size: 32px;
    font-weight: 600;
    line-height: 1;
    color: var(--text);
  }

  /* ================= 2. FLAT PANELS (NO NESTED BOXES!) ================= */
  .content-columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }

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
    padding: 20px 24px 16px 24px;
    border-bottom: 1px solid var(--line-soft);
  }

  .panel-title {
    font-family: var(--font-ui);
    font-size: 18px;
    font-weight: 600;
    color: var(--text);
    margin: 0;
    line-height: 1.3;
  }

  .panel-desc {
    font-size: 14px;
    color: var(--text-muted);
    margin: 3px 0 0 0;
  }

  .link-action {
    background: transparent;
    border: none;
    color: var(--accent);
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 0;
    flex-shrink: 0;
    transition: color var(--dur-fast) var(--ease);
  }
  .link-action:hover {
    color: var(--accent-2);
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
    padding: 16px 24px;
    background: transparent;
    border: none;
    border-bottom: 1px solid var(--line-soft);
    cursor: pointer;
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
    font-size: 15px;
    font-weight: 600;
    color: var(--text);
  }

  .title-sep {
    color: var(--line);
    font-weight: 400;
  }

  .title-sub {
    font-size: 15px;
    font-weight: 400;
    color: var(--text);
  }

  .title-target {
    font-size: 14px;
    font-weight: 500;
    color: var(--accent);
  }

  .row-meta {
    font-size: 14px;
    color: var(--text-muted);
    line-height: 1.4;
  }

  .row-end {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;
  }

  .arrow {
    color: var(--text-muted);
    transition: transform var(--dur-fast) var(--ease);
  }
  .flat-row:hover .arrow {
    transform: translateX(3px);
    color: var(--text);
  }

  .action-text {
    font-size: 14px;
    font-weight: 500;
    color: var(--accent);
  }

  /* Loading & Error States */
  .state-panel {
    background: var(--surface);
    border: 1px solid var(--line-soft);
    border-radius: var(--r-card);
    padding: 48px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    font-size: 15px;
    color: var(--text-muted);
  }
  .state-panel.error {
    color: var(--urgent);
  }

  .spin {
    animation: rotate 1.2s linear infinite;
  }
  @keyframes rotate {
    100% { transform: rotate(360deg); }
  }

  /* ================= RESPONSIVE ================= */
  @media (max-width: 960px) {
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
    .content-columns {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 600px) {
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
