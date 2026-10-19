<script>
  import { activePersona, showSuggestedActions } from '../lib/store.js';
  import { ChevronRight, X, ShieldCheck, Users, Calendar } from '@lucide/svelte';

  export let onAction = (/** @type {string} */ _text) => {};

  $: elder = $activePersona && ['chandler', 'amy', 'justin'].includes($activePersona.toLowerCase())
    ? $activePersona
    : 'Chandler';

  $: actionSections = [
    {
      title: 'Schemes & Entitlements',
      icon: ShieldCheck,
      color: 'var(--ok)',
      actions: [
        { label: `Plan SCSS for ${elder}`, desc: 'Senior Citizen Savings Scheme application & tenure', prompt: `Plan the SCSS application for ${elder}` },
        { label: 'Check US Medicare for Chandler', desc: 'Verify Part A & B enrollment criteria', prompt: 'Check US Medicare eligibility for Chandler' },
        { label: 'Social Security for Chandler', desc: 'Retirement age benefit & credit estimate', prompt: 'Check Social Security retirement eligibility for Chandler' },
        { label: 'Ayushman Checklist', desc: 'Required paperwork for senior healthcare card', prompt: 'What documents are needed for Ayushman Vay Vandana?' },
        { label: 'Medicare Checklist', desc: 'Complete checklist for Medicare assembly', prompt: 'What documents are needed for Medicare?' },
      ]
    },
    {
      title: 'Family Administration',
      icon: Users,
      color: 'var(--info)',
      actions: [
        { label: 'Family Roster', desc: 'Review all tracked family members & relations', prompt: 'List all family members' },
        { label: 'Annual Family Review', desc: 'Full household audit of expired documents & welfare', prompt: 'Run the annual family review' },
        { label: 'Family Dashboard', desc: 'Live overview of metrics, tasks & urgent alerts', prompt: 'Show me the family dashboard' },
      ]
    },
    {
      title: 'Daily & Tasks',
      icon: Calendar,
      color: 'var(--soon)',
      actions: [
        { label: 'Morning Briefing', desc: 'Immediate priorities, active deadlines & renewals', prompt: $activePersona && $activePersona !== 'all' ? `Give me the morning briefing for ${$activePersona}` : 'Give me the full family briefing' },
        { label: 'Tasks in Next 30 Days', desc: 'Upcoming renewal milestones & calendar appointments', prompt: 'What tasks are coming up in the next 30 days?' },
      ]
    }
  ];

  function close() {
    showSuggestedActions.set(false);
  }

  function handleSelect(prompt) {
    close();
    onAction(prompt);
  }
</script>

<svelte:window on:keydown={(e) => e.key === 'Escape' && close()} />

<!-- Backdrop: covers the entire viewport, dimming top bar, chips & canvas behind it -->
<div
  class="drawer-backdrop"
  on:click={close}
  role="presentation"
></div>

<!-- Side Banner / Drawer: in front of everything (z-index 10000) -->
<aside
  class="side-drawer"
  role="dialog"
  aria-modal="true"
  aria-label="Suggested Actions"
>
  <!-- Drawer Header -->
  <header class="drawer-header">
    <div class="header-text-group">
      <h2 class="drawer-title">Suggested Actions</h2>
      <p class="drawer-subtitle">Family paperwork shortcuts & administrative queries</p>
    </div>
    <button
      type="button"
      class="close-btn"
      on:click={close}
      aria-label="Close panel"
      title="Close (Esc)"
    >
      <X size={18} />
    </button>
  </header>

  <!-- Scrollable Content -->
  <div class="drawer-content">
    {#each actionSections as section}
      <section class="action-section">
        <div class="section-heading">
          <svelte:component this={section.icon} size={16} style="color: {section.color}; flex-shrink: 0;" />
          <span class="section-title">{section.title}</span>
          <span class="section-count">{section.actions.length}</span>
        </div>

        <div class="action-list">
          {#each section.actions as action}
            <button
              type="button"
              class="action-card"
              on:click={() => handleSelect(action.prompt)}
            >
              <div class="action-info">
                <span class="action-label">{action.label}</span>
                <span class="action-desc">{action.desc}</span>
              </div>
              <div class="arrow-circle">
                <ChevronRight size={15} />
              </div>
            </button>
          {/each}
        </div>
      </section>
    {/each}
  </div>

  <!-- Drawer Footer -->
  <footer class="drawer-footer">
    <p class="footer-tip">💡 <strong>Tip:</strong> You can also speak or type any question in your own words.</p>
  </footer>
</aside>

<style>
  /* Full-screen backdrop dims top bar, canvas & chips */
  .drawer-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(10, 15, 26, 0.55);
    backdrop-filter: blur(5px);
    -webkit-backdrop-filter: blur(5px);
    z-index: 9999;
    animation: fade-in 180ms ease;
  }

  /* Slide-out Side Banner: at the absolute top layer of the screen */
  .side-drawer {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    width: min(480px, 94vw);
    background: var(--surface);
    border-left: 1px solid var(--line);
    box-shadow: -12px 0 40px rgba(0, 0, 0, 0.22);
    z-index: 10000;
    display: flex;
    flex-direction: column;
    animation: slide-in 220ms cubic-bezier(0.16, 1, 0.3, 1);
  }

  @keyframes slide-in {
    from { transform: translateX(100%); }
    to { transform: translateX(0); }
  }

  @keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  /* Header */
  .drawer-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 24px 28px 20px 28px;
    border-bottom: 1px solid var(--line-soft);
    background: var(--surface);
    flex-shrink: 0;
  }

  .header-text-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .drawer-title {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--text);
  }

  .drawer-subtitle {
    margin: 0;
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.4;
  }

  .close-btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: 1px solid var(--line-soft);
    background: var(--surface-2);
    color: var(--text-muted);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all var(--dur-fast) var(--ease);
    flex-shrink: 0;
  }
  .close-btn:hover {
    color: var(--text);
    border-color: var(--line);
    background: var(--line-soft);
    transform: rotate(90deg);
  }

  /* Scrollable Content */
  .drawer-content {
    flex: 1;
    overflow-y: auto;
    padding: 24px 28px;
    display: flex;
    flex-direction: column;
    gap: 30px;
  }

  /* Custom sleek scrollbar */
  .drawer-content::-webkit-scrollbar {
    width: 6px;
  }
  .drawer-content::-webkit-scrollbar-thumb {
    background: var(--line);
    border-radius: 999px;
  }
  .drawer-content::-webkit-scrollbar-thumb:hover {
    background: var(--text-muted);
  }
  .drawer-content::-webkit-scrollbar-track {
    background: transparent;
  }

  /* Section */
  .action-section {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .section-heading {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .section-title {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
  }

  .section-count {
    font-size: 11px;
    font-weight: 600;
    background: var(--surface-2);
    color: var(--text-muted);
    padding: 1px 7px;
    border-radius: var(--r-pill);
    border: 1px solid var(--line-soft);
  }

  .action-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  /* Action Card: Clean, spacious, high-contrast */
  .action-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 14px 18px;
    background: var(--surface);
    border: 1px solid var(--line-soft);
    border-radius: 14px;
    text-align: left;
    cursor: pointer;
    transition: all var(--dur-fast) var(--ease);
    width: 100%;
    box-sizing: border-box;
  }

  .action-card:hover {
    background: var(--surface-2);
    border-color: var(--accent);
    transform: translateX(4px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  }

  .action-info {
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 0;
  }

  .action-label {
    font-size: 14.5px;
    font-weight: 600;
    color: var(--text);
    line-height: 1.35;
  }

  .action-desc {
    font-size: 12.5px;
    color: var(--text-muted);
    line-height: 1.4;
  }

  .arrow-circle {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: var(--surface-2);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    flex-shrink: 0;
    transition: all var(--dur-fast) var(--ease);
  }

  .action-card:hover .arrow-circle {
    background: var(--accent);
    color: #ffffff;
    transform: translateX(2px);
  }

  /* Footer */
  .drawer-footer {
    padding: 16px 28px;
    border-top: 1px solid var(--line-soft);
    background: var(--surface);
    flex-shrink: 0;
  }

  .footer-tip {
    margin: 0;
    font-size: 12.5px;
    color: var(--text-muted);
    text-align: center;
    line-height: 1.4;
  }
</style>
