<script>
  import CenterSheet from './CenterSheet.svelte';
  import { activePersona } from '../../lib/store.js';

  export let data = {
    totalConflicts: 0,
    protectedValueInr: 0,
    conflicts: [],
    restructuringSteps: [],
    spokenBrief: '',
    memberName: ''
  };
  export let onAction = (/** @type {string} */ _text) => {};
  export let onClose = () => {};

  $: hasConflicts = (data.conflicts && data.conflicts.length > 0) || (data.totalConflicts !== undefined && data.totalConflicts > 0);

  $: memberName = data.memberName ||
    ($activePersona && $activePersona !== 'all' ? $activePersona : null) ||
    ((data.conflicts && data.conflicts[0]?.parties) ? data.conflicts[0].parties.split(' ')[0].replace(/[^a-zA-Z]/g, '') : null) ||
    'Amy';

  $: primaryConflict = (data.conflicts && data.conflicts[0]) || {
    parties: `${memberName}`,
    clause: 'AB PM-JAY Guidelines Clause 4.2: Senior citizens covered under existing Central/State Govt health schemes cannot receive dual benefits without an explicit option declaration.',
    risk: 'Application rejected at portal scrutiny or cancellation of existing outpatient medicine coverage.'
  };

  $: protectedLakh = data.protectedValueInr
    ? `₹${(data.protectedValueInr / 100000).toFixed(2)} Lakh`
    : '₹10.48 Lakh';

  $: totalCollisions = data.totalConflicts !== undefined ? data.totalConflicts : (hasConflicts ? 2 : 0);

  $: query = `Simulate bureaucratic red tape conflicts for ${memberName}`;

  $: headline = !hasConflicts
    ? `${memberName}'s profile has 0 bureaucratic collisions. All records clear.`
    : `Two health schemes clash for ${memberName}. Form-B keeps ${protectedLakh} protected.`;

  $: accentWord = !hasConflicts ? '0 bureaucratic collisions' : 'clash';
  $: accentColor = !hasConflicts ? 'green' : 'red';

  $: chips = !hasConflicts
    ? [
        { label: '0 collisions', color: 'green' },
        { label: 'Clean Vault', color: 'green' }
      ]
    : [
        { label: `${totalCollisions} collision${totalCollisions !== 1 ? 's' : ''}`, color: 'red' },
        { label: `Protected ${protectedLakh}`, color: 'green' }
      ];

  $: stages = !hasConflicts
    ? [
        {
          label: 'Identity',
          connectorColor: 'green',
          nodes: [{ title: 'Aadhaar & PAN', subtitle: 'Linked & verified', color: 'green' }]
        },
        {
          label: 'Tax & Benefits',
          connectorColor: 'green',
          nodes: [{ title: 'Welfare Filings', subtitle: 'Single source compliant', color: 'green' }]
        },
        {
          label: 'Compliance',
          nodes: [{ title: 'Red Tape Audit', subtitle: 'Zero hazards', color: 'green' }]
        }
      ]
    : [
        {
          label: 'Target',
          connectorColor: 'red',
          nodes: [
            {
              title: 'Ayushman Vay Vandana',
              subtitle: '₹5,00,000 in-patient',
              color: 'cyan'
            }
          ]
        },
        {
          label: 'Clash',
          connectorColor: 'red',
          nodes: [
            {
              title: 'Clause 4.2',
              subtitle: 'Dual benefit blocked',
              color: 'red'
            }
          ]
        },
        {
          label: 'Active',
          nodes: [
            {
              title: 'CGHS / ECHS',
              subtitle: 'Outpatient medicines',
              color: 'cyan'
            }
          ]
        }
      ];

  $: detailsText = !hasConflicts
    ? `Bureaucratic cross-check verified for ${memberName}: no overlapping welfare claims, no dual statutory deductions, and no identity mismatches across central and state registries.`
    : `Governing Rule: ${primaryConflict.clause}\n\nPortal Scrutiny Risk: ${primaryConflict.risk}`;

  $: primaryAction = !hasConflicts ? 'View Compliance Audit' : 'Generate Form-B Declaration';
  $: secondaryAction = !hasConflicts ? 'Check Guidelines' : 'Review all';

  function handlePrimary() {
    if (!hasConflicts) {
      onAction(`Show compliance audit details for ${memberName}`);
    } else {
      onAction(`Apply option declaration for ${memberName}`);
    }
  }

  function handleSecondary() {
    onAction("Show all bureaucratic conflict resolutions");
  }
</script>

<CenterSheet
  {query}
  {headline}
  {accentWord}
  {accentColor}
  {chips}
  {stages}
  {primaryAction}
  {secondaryAction}
  details={detailsText}
  onPrimary={handlePrimary}
  onSecondary={handleSecondary}
  {onClose}
/>
