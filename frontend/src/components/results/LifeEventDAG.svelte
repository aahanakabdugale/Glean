<script>
  import CenterSheet from './CenterSheet.svelte';
  import { activePersona } from '../../lib/store.js';

  function getIsoDate(days) {
    const d = new Date();
    d.setDate(d.getDate() + days);
    return d.toISOString().split('T')[0];
  }

  export let data = {
    title: 'Retirement & Senior Transition for Justin',
    memberName: 'Justin',
    relation: 'father',
    birthYear: 1968,
    statusTransition: 'Employed ➔ Retired Senior',
    unlockedSchemes: [],
    vaultDocs: [],
    missingDocs: ['Age proof', 'Aadhaar card', 'Bank account passbook', 'Pension/Superannuation Order'],
    phases: [
      { dayOffset: 7, dueDate: getIsoDate(7), task: 'Consolidate pension papers & superannuation documents for Justin' },
      { dayOffset: 30, dueDate: getIsoDate(30), task: 'Apply for Senior Citizens Savings Scheme (SCSS) / deposit setup for Justin' },
      { dayOffset: 60, dueDate: getIsoDate(60), task: 'Review health coverage & register for Ayushman Vay Vandana card for Justin' },
      { dayOffset: 90, dueDate: getIsoDate(90), task: 'Submit annual Digital Life Certificate (Jeevan Pramaan) for Justin' }
    ],
    spokenBrief: ''
  };
  export let onAction = (/** @type {string} */ _text) => {};
  export let onClose = () => {};

  let selectedIndex = 0;

  $: member = data.memberName || ($activePersona && $activePersona !== 'all' ? $activePersona : null) || 'Justin';
  $: missingCount = (data.missingDocs && Array.isArray(data.missingDocs)) ? data.missingDocs.length : 0;
  $: phases = (data.phases && data.phases.length > 0) ? data.phases : [
    { dayOffset: 7, dueDate: getIsoDate(7), task: `Consolidate documents and milestone tasks for ${member}` },
    { dayOffset: 30, dueDate: getIsoDate(30), task: `Complete scheme applications and registration for ${member}` },
    { dayOffset: 60, dueDate: getIsoDate(60), task: `Verify scheme benefits and coverage for ${member}` }
  ];

  $: currentPhase = phases[selectedIndex] || phases[0];
  $: daysToStart = phases[0]?.dayOffset || 7;

  $: cleanTitle = (data.title || `Life Event Transition for ${member}`)
    .replace(/^🎯\s*Life-Event Roadmap Orchestrated:\s*/i, '')
    .split(' for ')[0];

  $: query = `Orchestrate ${cleanTitle.toLowerCase()} for ${member}`;

  $: headline = missingCount === 0
    ? `${member}'s transition roadmap is ready. All prerequisite documents verified.`
    : `${member}'s transition starts in ${daysToStart} days. ${missingCount} documents are still missing.`;

  $: accentWord = missingCount === 0 ? 'transition roadmap' : `${missingCount} documents`;

  $: chips = missingCount === 0
    ? [
        { label: '0 documents missing', color: 'green' },
        { label: `${phases.length} milestones scheduled`, color: 'cyan' }
      ]
    : [
        { label: `${missingCount} documents missing`, color: 'amber' },
        { label: `${phases.length} milestones scheduled`, color: 'cyan' }
      ];

  function formatPhaseSub(p) {
    if (p.dueDate && p.dueDate.includes('-')) {
      const parts = p.dueDate.split('-');
      return `Day ${p.dayOffset} · ${parts[1]}-${parts[2]}`;
    }
    return `Day ${p.dayOffset}`;
  }

  $: stages = phases.map((p, idx) => ({
    label: `+${p.dayOffset}d`,
    connectorColor: 'cyan',
    clickable: true,
    nodes: [
      {
        title: `+${p.dayOffset}d`,
        subtitle: formatPhaseSub(p),
        color: 'cyan',
        active: selectedIndex === idx,
        id: String(idx)
      }
    ]
  }));

  function handleNodeClick(node) {
    if (node.id !== undefined) {
      selectedIndex = parseInt(node.id, 10);
    }
  }

  function handlePrimary() {
    if (missingCount > 0) {
      onAction(`What documents are needed for ${member}'s transition?`);
    } else {
      onClose();
    }
  }
</script>

<CenterSheet
  {query}
  {headline}
  {accentWord}
  accentColor="cyan"
  {chips}
  {stages}
  primaryAction={missingCount > 0 ? "Check Missing Documents" : "Done"}
  secondaryAction="Dismiss"
  onPrimary={handlePrimary}
  onSecondary={onClose}
  onNodeClick={handleNodeClick}
  {onClose}
>
  <!-- Direct milestone detail box visible immediately without accordion clicking -->
  <div class="milestone-box">
    <div class="milestone-header">
      <span class="step-pill">Stage {selectedIndex + 1} of {phases.length}</span>
      <span class="due-text">Due {currentPhase.dueDate} · in {currentPhase.dayOffset} days</span>
    </div>

    <div class="task-description">
      {currentPhase.task}
    </div>

    {#if missingCount > 0}
      <div class="prereqs-block">
        <span class="prereqs-title">Missing Prerequisite Documents</span>
        <div class="prereq-pills">
          {#each data.missingDocs as doc}
            <span class="doc-badge">
              <span class="amber-dot" aria-hidden="true"></span>
              <span>{doc}</span>
            </span>
          {/each}
        </div>
      </div>
    {:else}
      <div class="prereqs-block">
        <span class="doc-badge ok">
          <span class="green-dot" aria-hidden="true"></span>
          <span>All prerequisite documents verified in vault</span>
        </span>
      </div>
    {/if}
  </div>
</CenterSheet>

<style>
  .milestone-box {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--cs-pill-border);
    border-radius: 16px;
    padding: 16px 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    box-sizing: border-box;
    margin: 4px 0;
  }

  .milestone-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
  }

  .step-pill {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #22d3ee;
    background: rgba(34, 211, 238, 0.12);
    border: 1px solid rgba(34, 211, 238, 0.25);
    padding: 3px 10px;
    border-radius: 999px;
  }

  .due-text {
    font-size: 13px;
    color: var(--cs-muted);
    font-family: var(--font-mono, monospace);
  }

  .task-description {
    font-size: 15px;
    font-weight: 500;
    line-height: 1.5;
    color: var(--cs-ink);
  }

  .prereqs-block {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding-top: 10px;
    border-top: 1px solid var(--cs-pill-border);
  }

  .prereqs-title {
    font-size: 11px;
    font-weight: 600;
    color: var(--cs-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .prereq-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .doc-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--cs-pill);
    border: 1px solid var(--cs-pill-border);
    border-radius: 999px;
    padding: 4px 12px;
    font-size: 13px;
    color: var(--cs-ink);
  }

  .doc-badge.ok {
    border-color: rgba(52, 211, 153, 0.3);
    background: rgba(52, 211, 153, 0.08);
  }

  .amber-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #fbbf24;
    box-shadow: 0 0 6px #fbbf24;
    flex-shrink: 0;
  }

  .green-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #34d399;
    box-shadow: 0 0 6px #34d399;
    flex-shrink: 0;
  }
</style>
