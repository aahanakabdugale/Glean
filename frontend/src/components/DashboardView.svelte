<script>
  import { onMount } from 'svelte';
  import { activeView } from '../lib/store.js';
  import { callGetFamilyDashboard, callCompleteTask } from '../lib/mcp.js';
  import { urgencyOf, formatDaysLeft } from '../lib/urgency.js';
  import {
    Users,
    FileText,
    Calendar,
    ShieldCheck,
    RotateCw,
    ArrowLeft,
    AlertCircle,
    ChevronRight,
    Check
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

  let completedTasks = {};

  async function markTaskDone(task) {
    if (completedTasks[task.title]) return;
    completedTasks = { ...completedTasks, [task.title]: true };
    if (dashboardData.metrics.pendingTasks > 0) {
      dashboardData.metrics.pendingTasks--;
    }
    if (dashboardData.metrics.upcomingTasks > 0) {
      dashboardData.metrics.upcomingTasks--;
    }
    try {
      await callCompleteTask(task.title, task.member || '');
    } catch (e) {
      console.error('Failed to complete task', e);
    }
  }

  let selectedCountry = 'all'; // 'all' | 'US' | 'IN'

  const schemes = [
    // US Federal Schemes
    {
      title: 'Medicare (Parts A & B)',
      country: 'US',
      countryLabel: 'US',
      beneficiary: 'Chandler & Amy (Age 65+)',
      detail: 'Federal health coverage for inpatient hospital care (Part A) and outpatient doctor visits (Part B)',
      status: 'ok',
      badge: 'May Qualify',
      prompt: 'Check Medicare eligibility for Chandler'
    },
    {
      title: 'Social Security Retirement (OASI)',
      country: 'US',
      countryLabel: 'US',
      beneficiary: 'Chandler (Age 62+)',
      detail: 'Guaranteed lifetime federal retirement pension; early claiming eligibility starts at age 62',
      status: 'ok',
      badge: 'Eligible',
      prompt: 'Plan Social Security retirement for Chandler'
    },
    {
      title: '401(k) & IRA Catch-Up (SECURE 2.0)',
      country: 'US',
      countryLabel: 'US',
      beneficiary: 'Justin (Age 50+, Employed)',
      detail: 'Federal tax policy permitting extra annual retirement contributions above standard elective limits',
      status: 'ok',
      badge: 'Eligible',
      prompt: 'Check 401k catch-up rules for Justin'
    },
    {
      title: 'SNAP (Food Assistance)',
      country: 'US',
      countryLabel: 'US',
      beneficiary: 'Family Dependents',
      detail: 'Federal nutrition assistance support via electronic benefits transfer (EBT) card',
      status: 'info',
      badge: 'Income Rule',
      prompt: 'What documents are needed for SNAP?'
    },
    // India National Schemes
    {
      title: 'Ayushman Vay Vandana (AB PM-JAY)',
      country: 'IN',
      countryLabel: 'India',
      beneficiary: 'Amy & Chandler (Age 70+)',
      detail: '₹5 Lakh annual universal healthcare cover with zero waiting period for all seniors aged 70 and above',
      status: 'ok',
      badge: 'May Qualify',
      prompt: 'Check scheme checklist for Ayushman card'
    },
    {
      title: 'Senior Citizens Savings Scheme (SCSS)',
      country: 'IN',
      countryLabel: 'India',
      beneficiary: 'Chandler (Age 60+)',
      detail: '8.2% sovereign quarterly interest at post offices and authorized banking institutions',
      status: 'ok',
      badge: 'May Qualify',
      prompt: 'Plan the SCSS application for Chandler'
    },
    {
      title: 'Atal Pension Yojana (APY)',
      country: 'IN',
      countryLabel: 'India',
      beneficiary: 'Justin (Age window transition)',
      detail: 'Guaranteed government-backed lifelong monthly pension up to ₹5,000 after age 60',
      status: 'soon',
      badge: 'Age Window',
      prompt: 'What schemes does Justin qualify for?'
    },
    {
      title: 'Sukanya Samriddhi Yojana (SSY)',
      country: 'IN',
      countryLabel: 'India',
      beneficiary: 'Family Dependents',
      detail: 'High-yield sovereign tax-free compounding savings account for girl children under 10',
      status: 'info',
      badge: 'Eligible',
      prompt: 'Check checklist for Sukanya Samriddhi Yojana'
    }
  ];

  $: filteredSchemes = selectedCountry === 'all'
    ? schemes
    : schemes.filter(s => s.country === selectedCountry);

  $: usCount = schemes.filter(s => s.country === 'US').length;
  $: inCount = schemes.filter(s => s.country === 'IN').length;
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
        <span>Ask Glean</span>
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
        on:click={() => handleActionClick("What documents are expiring in the next 60 days?")}
      >
        <div class="metric-top">
          <FileText size={18} class="metric-icon icon-urgent" />
          <span class="metric-label">Expiring Documents</span>
        </div>
        <div class="metric-bottom">
          <span class="metric-num">{dashboardData.metrics.expiringDocs ?? dashboardData.expiring?.length ?? 3}</span>
          <span class="vr-badge {(dashboardData.metrics.urgentDocs ?? 1) > 0 ? 'urgent' : 'ok'}">{dashboardData.metrics.urgentDocs ?? 1} Urgent</span>
        </div>
      </button>

      <button
        type="button"
        class="metric-cell"
        on:click={() => handleActionClick("What tasks are coming up in the next 30 days?")}
      >
        <div class="metric-top">
          <Calendar size={18} class="metric-icon icon-soon" />
          <span class="metric-label">Upcoming Tasks</span>
        </div>
        <div class="metric-bottom">
          <span class="metric-num">{dashboardData.metrics.upcomingTasks ?? dashboardData.tasks?.length ?? 4}</span>
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
          <span class="metric-num">{dashboardData.metrics.schemeOpportunities || schemes.length}</span>
          <span class="vr-badge ok">US & IN Ready</span>
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
            on:click={() => handleActionClick("What documents are expiring in the next 60 days?")}
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
              on:click={() => handleActionClick(`What documents are expiring in the next 60 days for ${doc.member || doc.owner}?`)}
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
            on:click={() => handleActionClick("What tasks are coming up in the next 30 days?")}
          >
            <span>View all</span>
            <ChevronRight size={14} />
          </button>
        </div>

        <div class="flat-list">
          {#each dashboardData.tasks as task}
            {@const isDone = !!completedTasks[task.title]}
            {@const level = task.daysLeft && task.daysLeft <= 7 ? 'urgent' : 'soon'}
            <div
              class="flat-row task-row"
              class:task-completed={isDone}
              on:click={() => handleActionClick("What tasks are coming up in the next 30 days?")}
              role="button"
              tabindex="0"
              on:keydown={(e) => e.key === 'Enter' && handleActionClick("What tasks are coming up in the next 30 days?")}
            >
              <div class="task-leading">
                <button
                  type="button"
                  class="task-check-circle"
                  class:ticked={isDone}
                  on:click|stopPropagation={() => markTaskDone(task)}
                  aria-label="{isDone ? 'Completed' : 'Mark as complete'}: {task.title}"
                  title="{isDone ? 'Task completed' : 'Click to mark complete'}"
                >
                  {#if isDone}
                    <Check size={13} />
                  {/if}
                </button>
                <div class="row-main">
                  <div class="row-title">
                    <span class="title-bold" class:done-text={isDone}>{task.title}</span>
                  </div>
                  <span class="row-meta">Due {task.dueDate} {task.member ? `· ${task.member}` : ''}</span>
                </div>
              </div>
              <div class="row-end">
                {#if isDone}
                  <span class="vr-badge ok">Done</span>
                {:else}
                  <span class="vr-badge {level}">{formatDaysLeft(task.daysLeft) || task.status || 'Scheduled'}</span>
                {/if}
                <ChevronRight size={16} class="arrow" />
              </div>
            </div>
          {/each}
        </div>
      </section>
    </div>

    <!-- 3. Government Scheme Matches Panel (Clean Flat Rows) -->
    <section class="flat-panel" aria-label="Government scheme opportunities">
      <div class="panel-top scheme-panel-top">
        <div class="panel-heading-block">
          <div class="title-with-badge">
            <h2 class="panel-title">Government Scheme Matches</h2>
            <span class="vr-badge ok">{schemes.length} Verified</span>
          </div>
          <p class="panel-desc">Benefits identified for your family’s age and eligibility profiles across regions</p>
        </div>

        <!-- Clean Subtle Region Filter Tabs -->
        <div class="region-tabs" role="tablist" aria-label="Filter schemes by region">
          <button
            type="button"
            role="tab"
            aria-selected={selectedCountry === 'all'}
            class="tab-btn"
            class:active={selectedCountry === 'all'}
            on:click={() => selectedCountry = 'all'}
          >
            <span>All ({schemes.length})</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={selectedCountry === 'US'}
            class="tab-btn"
            class:active={selectedCountry === 'US'}
            on:click={() => selectedCountry = 'US'}
          >
            <span>US ({usCount})</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={selectedCountry === 'IN'}
            class="tab-btn"
            class:active={selectedCountry === 'IN'}
            on:click={() => selectedCountry = 'IN'}
          >
            <span>India ({inCount})</span>
          </button>
        </div>
      </div>

      <div class="flat-list">
        {#each filteredSchemes as s}
          <button
            type="button"
            class="flat-row scheme-row"
            on:click={() => handleActionClick(s.prompt)}
          >
            <div class="row-main">
              <div class="row-title">
                <span class="region-pill">{s.countryLabel}</span>
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

  .region-pill {
    font-size: 11.5px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: var(--r-pill);
    background: var(--surface-2);
    color: var(--accent);
    border: 1px solid var(--line-soft);
    display: inline-flex;
    align-items: center;
    letter-spacing: 0.03em;
    flex-shrink: 0;
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

  .link-action {
    background: transparent;
    border: none;
    color: var(--accent);
    font-size: 14.5px;
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
    padding: 16px 26px;
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

  .task-leading {
    display: flex;
    align-items: center;
    gap: 14px;
    min-width: 0;
  }

  .task-check-circle {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    border: 1.5px solid var(--line);
    background: transparent;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
    transition: all var(--dur-fast) var(--ease);
    color: var(--ok);
    padding: 0;
  }

  .task-check-circle:hover {
    border-color: var(--ok);
    background: var(--ok-bg);
  }

  .task-check-circle.ticked {
    border-color: var(--ok);
    background: var(--ok-bg);
    color: var(--ok);
  }

  .task-completed {
    opacity: 0.6;
  }

  .done-text {
    text-decoration: line-through;
    opacity: 0.75;
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
    font-size: 16px;
    font-weight: 600;
    color: var(--text);
  }

  .title-sep {
    color: var(--line);
    font-weight: 400;
  }

  .title-sub {
    font-size: 16px;
    font-weight: 400;
    color: var(--text);
  }

  .title-target {
    font-size: 15px;
    font-weight: 500;
    color: var(--accent);
  }

  .row-meta {
    font-size: 14.5px;
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
    font-size: 15px;
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
