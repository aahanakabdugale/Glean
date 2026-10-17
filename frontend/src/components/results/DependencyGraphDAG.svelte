<script>
  import CenterSheet from './CenterSheet.svelte';
  import { activePersona } from '../../lib/store.js';

  export let data = {
    totalAudited: 6,
    criticalBlockers: 0,
    impendingRisks: 1,
    members: [],
    criticalPath: [],
    spokenBrief: '',
    memberName: ''
  };
  export let onAction = (/** @type {string} */ _text) => {};
  export let onClose = () => {};

  $: targetName = data.memberName || ($activePersona && $activePersona !== 'all' ? $activePersona : null);

  // If specific targetName exists, pick that member; else pick first or member with risks
  $: activeMember = (targetName && (data.members || []).find(m => m.name.toLowerCase() === targetName.toLowerCase())) ||
    ((data.members && data.members.length === 1) ? data.members[0] : null) ||
    ((data.members || []).find(m => (m.risks && m.risks.length > 0) || (m.blockers && m.blockers.length > 0))) ||
    (data.members && data.members[0]) || {
      name: targetName || 'Chandler',
      risks: targetName && targetName.toLowerCase() === 'jace' ? [] : [{ doc: 'Passport', daysLeft: 6, atRiskScheme: 'Ayushman Vay Vandana Card (AB PM-JAY)' }],
      blockers: []
    };

  $: memberName = activeMember.name || targetName || 'Chandler';
  $: hasRisks = activeMember.risks && activeMember.risks.length > 0;
  $: hasBlockers = activeMember.blockers && activeMember.blockers.length > 0;
  $: isSorted = !hasRisks && !hasBlockers;

  $: blockerCount = data.criticalBlockers !== undefined ? data.criticalBlockers : 0;
  $: riskCount = data.impendingRisks !== undefined ? data.impendingRisks : (isSorted ? 0 : 1);
  $: safeCount = Math.max(0, (data.totalAudited || 6) - blockerCount - (riskCount > 0 ? 1 : 0));

  $: topRisk = hasRisks ? activeMember.risks[0] : null;
  $: topBlocker = hasBlockers ? activeMember.blockers[0] : null;

  $: docName = topRisk?.doc || topBlocker?.doc || 'Document';
  $: daysLeft = topRisk?.daysLeft !== undefined ? topRisk.daysLeft : 0;
  $: blockedCount = Math.max(1, (activeMember.risks?.length || 0) + (activeMember.blockers?.length || 0));

  // Build unified CenterSheet props
  $: query = `Audit document dependencies for ${memberName}`;

  $: headline = isSorted
    ? `${memberName}'s paperwork is completely sorted with 0 blockers.`
    : (hasBlockers
      ? `${memberName}'s ${docName.toLowerCase()} is expired and blocks ${blockedCount} scheme${blockedCount > 1 ? 's' : ''}.`
      : `${memberName}'s ${docName.toLowerCase()} expires in ${daysLeft} days and blocks ${blockedCount} scheme${blockedCount > 1 ? 's' : ''}.`);

  $: accentWord = isSorted ? 'completely sorted' : docName.toLowerCase();
  $: accentColor = isSorted ? 'green' : (hasBlockers ? 'red' : 'amber');

  $: chips = isSorted
    ? [
        { label: '0 blockers', color: 'green' },
        { label: '0 impending risks', color: 'green' },
        { label: `${safeCount || 3} safe`, color: 'green' }
      ]
    : [
        { label: `${blockerCount} blockers`, color: blockerCount > 0 ? 'red' : 'green' },
        { label: `${riskCount} impending risk`, color: 'amber' },
        { label: `${safeCount} safe`, color: 'green' }
      ];

  // Map scheme nodes
  $: schemeNodes = isSorted
    ? [{ title: 'All Schemes', subtitle: 'Fully unblocked', color: 'green' }]
    : ((activeMember.risks && activeMember.risks.length > 0)
        ? activeMember.risks.map(r => ({
            title: r.atRiskScheme.replace(' (AB PM-JAY)', '').replace(' Card', ''),
            subtitle: 'Blocked',
            color: 'amber',
            locked: true
          }))
        : [
            { title: 'Ayushman Vay Vandana', subtitle: 'Blocked', color: 'amber', locked: true },
            { title: 'Senior Citizens Savings', subtitle: 'Blocked', color: 'amber', locked: true }
          ]);

  $: stages = isSorted
    ? [
        {
          label: 'Member',
          connectorColor: 'green',
          nodes: [{ title: memberName, subtitle: 'All verified', color: 'green' }]
        },
        {
          label: 'Vault',
          connectorColor: 'green',
          nodes: [{ title: 'Documents', subtitle: `${safeCount || 3} safe & active`, color: 'green' }]
        },
        {
          label: 'Schemes',
          nodes: schemeNodes
        }
      ]
    : [
        {
          label: 'Member',
          connectorColor: accentColor,
          nodes: [{ title: memberName, subtitle: 'Action required', color: accentColor }]
        },
        {
          label: 'Document',
          connectorColor: accentColor,
          nodes: [{ title: docName, subtitle: hasBlockers ? 'Expired' : `${daysLeft}d left`, color: accentColor }]
        },
        {
          label: 'Schemes',
          nodes: schemeNodes
        }
      ];

  $: detailsText = isSorted
    ? `All documents for ${memberName} are healthy, valid, and fully compliant with all government and banking schemes. No upcoming renewal bottlenecks detected.`
    : ((data.criticalPath && data.criticalPath[0]?.text)
        ? data.criticalPath[0].text
        : `Schedule renewal for ${memberName}'s ${docName} (${daysLeft}d left). Prevents a bottleneck in ${schemeNodes.map(s => s.title).join(' and ')}.`);

  $: primaryAction = isSorted ? 'View Document Vault' : 'Plan Renewal Now';

  function handlePrimary() {
    if (isSorted) {
      onAction(`Show vault documents for ${memberName}`);
    } else {
      onAction(`Plan renewal for ${memberName}'s ${docName}`);
    }
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
  details={detailsText}
  onPrimary={handlePrimary}
  {onClose}
/>
