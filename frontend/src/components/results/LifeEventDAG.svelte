<script>
  import CenterSheet from './CenterSheet.svelte';
  import { activePersona } from '../../lib/store.js';

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
      { dayOffset: 7, dueDate: '2026-10-24', task: 'Consolidate pension papers & superannuation documents for Justin' },
      { dayOffset: 30, dueDate: '2026-11-16', task: 'Apply for Senior Citizens Savings Scheme (SCSS) / deposit setup for Justin' },
      { dayOffset: 60, dueDate: '2026-12-16', task: 'Review health coverage & register for Ayushman Vay Vandana card for Justin' },
      { dayOffset: 90, dueDate: '2027-01-15', task: 'Submit annual Digital Life Certificate (Jeevan Pramaan) for Justin' }
    ],
    spokenBrief: ''
  };
  export let onAction = (/** @type {string} */ _text) => {};
  export let onClose = () => {};

  let selectedIndex = 0;

  $: member = data.memberName || ($activePersona && $activePersona !== 'all' ? $activePersona : null) || 'Justin';
  $: missingCount = (data.missingDocs && Array.isArray(data.missingDocs)) ? data.missingDocs.length : 0;
  $: phases = (data.phases && data.phases.length > 0) ? data.phases : [
    { dayOffset: 7, dueDate: '2026-10-24', task: `Consolidate documents and milestone tasks for ${member}` },
    { dayOffset: 30, dueDate: '2026-11-16', task: `Complete scheme applications and registration for ${member}` },
    { dayOffset: 60, dueDate: '2026-12-16', task: `Verify scheme benefits and coverage for ${member}` }
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
        { label: `${phases.length} milestones active`, color: 'cyan' }
      ]
    : [
        { label: `${missingCount} documents missing`, color: 'amber' },
        { label: `${phases.length} milestones active`, color: 'cyan' }
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

  $: detailsData = {
    title: `Stage ${selectedIndex + 1} of ${phases.length} · due ${currentPhase.dueDate}`,
    body: currentPhase.task,
    pills: (missingCount > 0)
      ? data.missingDocs
      : ['All prerequisite documents verified in vault']
  };

  function handleNodeClick(node) {
    if (node.id !== undefined) {
      selectedIndex = parseInt(node.id, 10);
    }
  }

  function handlePrimary() {
    onAction(`Add ${cleanTitle.toLowerCase()} tasks for ${member} to calendar`);
  }

  function handleSecondary() {
    onAction(`What documents are needed for ${member}'s transition?`);
  }
</script>

<CenterSheet
  {query}
  {headline}
  {accentWord}
  accentColor="cyan"
  {chips}
  {stages}
  primaryAction="Add Tasks to Family Calendar"
  secondaryAction={missingCount > 0 ? "Checklist" : "View Roadmap"}
  details={detailsData}
  onPrimary={handlePrimary}
  onSecondary={handleSecondary}
  onNodeClick={handleNodeClick}
  {onClose}
/>
