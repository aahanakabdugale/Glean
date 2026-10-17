<script>
  import { orbState, activePersona, messages, alexaMicEnabled, toggleAlexaMic, clearMessages } from '../lib/store.js';
  import Orb from './Orb.svelte';
  import Waveform from './Waveform.svelte';
  import QuickChips from './QuickChips.svelte';
  import InputDock from './InputDock.svelte';
  import ToolCallChip from './ToolCallChip.svelte';
  import ExpiringDocs from './results/ExpiringDocs.svelte';
  import FamilyBrief from './results/FamilyBrief.svelte';
  import SchemeEligibility from './results/SchemeEligibility.svelte';
  import SchemeChecklist from './results/SchemeChecklist.svelte';
  import PlanApplication from './results/PlanApplication.svelte';
  import UpcomingTasks from './results/UpcomingTasks.svelte';
  import DependencyGraphDAG from './results/DependencyGraphDAG.svelte';
  import ConflictSimulatorDAG from './results/ConflictSimulatorDAG.svelte';
  import VoiceDialectsDAG from './results/VoiceDialectsDAG.svelte';
  import LifeEventDAG from './results/LifeEventDAG.svelte';
  import CenterSheet from './results/CenterSheet.svelte';
  import { X } from '@lucide/svelte';

  export let onSend = (/** @type {string} */ _text) => {};

  $: elder = $activePersona && $activePersona !== 'all' ? $activePersona : 'Chandler';

  // Find latest assistant reply for the big caption and answer card
  $: lastAssistantMsg = [...$messages].reverse().find(m => m.role === 'assistant');
  $: lastUserMsg = [...$messages].reverse().find(m => m.role === 'user');

  // Adapt general typed / spoken / quick-chip query results to Center Sheet structure
  function getGeneralSheetProps(assistantMsg, userMsg) {
    const query = userMsg?.text || 'Voice Query';
    const type = assistantMsg?.resultType;
    const data = assistantMsg?.resultData;
    const text = assistantMsg?.text || '';

    if (type === 'scheme_eligibility' && data) {
      const person = data.personName || 'Chandler';
      const count = data.eligible?.length || 0;
      return {
        query,
        headline: `${person} qualifies for ${count} welfare schemes.`,
        accentWord: `${count} welfare schemes`,
        chips: [
          { label: `${count} eligible`, color: 'green' },
          ...(data.checkNeeded?.length ? [{ label: `${data.checkNeeded.length} verify criteria`, color: 'amber' }] : [])
        ]
      };
    }

    if (type === 'expiring_docs' && data) {
      const count = data.expiringDocs?.length || 0;
      return {
        query,
        headline: `${count} family documents expire within 90 days.`,
        accentWord: `${count} family documents`,
        chips: [{ label: `${count} expiring soon`, color: 'amber' }]
      };
    }

    if (type === 'family_dashboard' && data) {
      const memberCount = data.metrics?.totalMembers ?? (data.members?.length || 6);
      const docsCount = data.metrics?.totalDocs ?? (data.expiring?.length || 0);
      const urgentCount = data.metrics?.urgentDocs ?? 0;
      const tasksCount = data.metrics?.pendingTasks ?? (data.tasks?.length || 0);
      return {
        query,
        headline: `${memberCount} family members are tracked in your vault dashboard.`,
        accentWord: `${memberCount} family members`,
        chips: [
          { label: `${memberCount} members`, color: 'cyan' },
          { label: `${docsCount} documents`, color: 'blue' },
          ...(urgentCount > 0 ? [{ label: `${urgentCount} urgent`, color: 'red' }] : []),
          { label: `${tasksCount} pending tasks`, color: 'amber' }
        ]
      };
    }

    if (type === 'family_brief' && data) {
      const memberCount = data.members?.length || 6;
      return {
        query,
        headline: `${memberCount} family members are protected under Glean.`,
        accentWord: `${memberCount} family members`,
        chips: [{ label: `${memberCount} members`, color: 'cyan' }, { label: 'Vault synced', color: 'green' }]
      };
    }

    if (type === 'upcoming_tasks' && data) {
      const count = data.tasks?.length || 0;
      return {
        query,
        headline: `${count} upcoming deadlines require attention.`,
        accentWord: `${count} upcoming deadlines`,
        chips: [{ label: `${count} tasks pending`, color: 'amber' }]
      };
    }

    if (type === 'scheme_checklist' && data) {
      const name = data.schemeName || 'Scheme';
      return {
        query,
        headline: `Required paperwork checklist for ${name}.`,
        accentWord: name,
        chips: [{ label: 'Official portal rules', color: 'cyan' }]
      };
    }

    if (type === 'plan_application' && data) {
      return {
        query,
        headline: 'Application plan and submission route prepared.',
        accentWord: 'Application plan',
        chips: [{ label: 'Ready for submission', color: 'green' }]
      };
    }

    // Plain text responses (e.g., "how many family members are there")
    const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
    let headline = '';
    let accentWord = '';

    if (query.toLowerCase().includes('family') || query.toLowerCase().includes('roster') || query.toLowerCase().includes('rooster') || query.toLowerCase().includes('member') || query.toLowerCase().includes('who')) {
      const count = Array.isArray(data) ? data.length : (data?.members?.length || (lines.filter(l => l.includes('(')).length || 6));
      headline = `${count} family members are registered in your vault.`;
      accentWord = `${count} family members`;
    } else if (lines.length > 0) {
      const firstLine = lines[0];
      headline = firstLine.length > 70 ? firstLine.slice(0, 68) + '…' : firstLine;
      const words = headline.split(' ');
      if (words.length >= 3) {
        accentWord = words.slice(1, 3).join(' ');
      }
    } else {
      headline = 'Here is what was found for your query.';
      accentWord = 'query';
    }

    return {
      query,
      headline,
      accentWord,
      chips: []
    };
  }

  // Format caption text with key word highlighted
  function formatCaption(msg, micEnabled, currentElder, currentOrbState) {
    if (!micEnabled) {
      return {
        prefix: 'Alexa microphone is ',
        highlight: 'muted',
        suffix: '. Tap the orb or mic button to unmute.'
      };
    }

    if (currentOrbState === 'listening') {
      return {
        prefix: 'Listening to ',
        highlight: currentElder,
        suffix: '… Ask anything about paperwork or schemes.'
      };
    }

    if (currentOrbState === 'thinking') {
      return {
        prefix: 'Glean is ',
        highlight: 'analyzing paperwork',
        suffix: ' and matching government databases…'
      };
    }

    // Default ambient caption matching the design spec
    if (!msg || !msg.text) {
      if (currentElder === 'Chandler' || currentElder === 'Family') {
        return {
          prefix: "Chandler's passport expires in ",
          highlight: '6 days',
          suffix: '.'
        };
      }
      return {
        prefix: `Ready for `,
        highlight: currentElder,
        suffix: `. How can I help with your family's paperwork?`
      };
    }

    const t = msg.text.trim();
    if (t.includes('urgent') || t.includes('expired') || t.includes('days left')) {
      return { prefix: 'Found paperwork that needs attention: ', highlight: 'urgent deadlines', suffix: ' detected.' };
    }
    if (t.includes('may qualify') || t.includes('eligible') || t.includes('almost eligible')) {
      return { prefix: 'Identified relevant government schemes: ', highlight: 'may qualify', suffix: ' for benefits.' };
    }
    if (t.includes('Application plan') || t.includes('Plan')) {
      return { prefix: 'Generated official roadmap: ', highlight: 'application plan', suffix: ' created with dated tasks.' };
    }
    const words = t.split(' ');
    if (words.length <= 8) {
      return { prefix: words.slice(0, 3).join(' ') + ' ', highlight: words.slice(3, 5).join(' '), suffix: ' ' + words.slice(5).join(' ') };
    }
    return { prefix: words.slice(0, 4).join(' ') + ' ', highlight: words.slice(4, 7).join(' '), suffix: ' ' + words.slice(7, 12).join(' ') + '…' };
  }

  $: caption = formatCaption(lastAssistantMsg, $alexaMicEnabled, elder, $orbState);

  // Orb click handler
  function handleOrbClick() {
    if (!$alexaMicEnabled) {
      toggleAlexaMic();
      return;
    }
    if ($orbState === 'idle') {
      orbState.set('listening');
      setTimeout(() => {
        if ($orbState === 'listening') orbState.set('idle');
      }, 4000);
    } else if ($orbState === 'listening') {
      orbState.set('idle');
    }
  }

  // Floating Ambient Status Chips — Breakthrough Capabilities adapted to active persona
  $: dialectPrompt = (elder === 'Jace')
    ? 'Explain sovereign savings for young adult'
    : ((elder === 'Gwen')
      ? 'Explain education loan subsidy for university student'
      : ((elder === 'Riley')
        ? 'Explain Section 80D tax deductions for working parent'
        : ((elder === 'Justin')
          ? 'Explain SCSS and pension for parent'
          : ((elder === 'Amy')
            ? 'Explain PM Vaya Vandana for grandmother'
            : 'Explain SCSS for grandparent'))));

  $: lifeEventPrompt = (elder === 'Jace' || elder === 'Gwen')
    ? `Orchestrate adulthood independence transition for ${elder}`
    : ((elder === 'Riley')
      ? `Orchestrate relocation and family transition for ${elder}`
      : ((elder === 'Justin')
        ? `Orchestrate retirement transition for ${elder}`
        : `Orchestrate super-senior healthcare transition for ${elder}`));

  $: ambientChips = [
    {
      id: 'chip-conflict',
      side: 'left',
      posClass: 'pos-top-left',
      animClass: 'float-1',
      dotClass: (elder === 'Chandler' || elder === 'Amy') ? 'dot-urgent' : 'dot-live',
      label: 'Conflict Simulator',
      prompt: `Simulate bureaucratic red tape conflicts for ${elder}`,
    },
    {
      id: 'chip-roster',
      side: 'left',
      posClass: 'pos-mid-left',
      animClass: 'float-2',
      dotClass: 'dot-ok',
      label: 'Family Roster',
      prompt: `List all family members and relations`,
    },
    {
      id: 'chip-dependency',
      side: 'left',
      posClass: 'pos-bot-left',
      animClass: 'float-3',
      dotClass: (elder === 'Jace') ? 'dot-live' : 'dot-soon',
      label: 'Dependency Graph',
      prompt: `Audit document dependencies for ${elder}`,
    },
    {
      id: 'chip-dialect',
      side: 'right',
      posClass: 'pos-top-right',
      animClass: 'float-2',
      dotClass: 'dot-info',
      label: 'Voice Dialects',
      prompt: dialectPrompt,
    },
    {
      id: 'chip-life-event',
      side: 'right',
      posClass: 'pos-bot-right',
      animClass: 'float-1',
      dotClass: 'dot-accent',
      label: 'Life Event Engine',
      prompt: lifeEventPrompt,
    },
  ];

  $: isCenterSheet = Boolean(lastAssistantMsg);

  function dismissResult() {
    clearMessages();
  }
</script>

<svelte:window on:keydown={(e) => { if (e.key === 'Escape' && isCenterSheet) dismissResult(); }} />

<div class="ambient-canvas">
  {#if isCenterSheet}
    <button
      type="button"
      class="sheet-backdrop"
      on:click={dismissResult}
      aria-label="Return to ambient"
      tabindex="-1"
    ></button>
  {/if}
  <!-- Subtle Dotted Grid across entire canvas -->
  <div class="dotted-grid" aria-hidden="true"></div>

  <!-- Concentric Sonar Rings expanding from the central orb -->
  <div class="sonar-container" class:faded-out={isCenterSheet} aria-hidden="true">
    <div class="sonar-ring ring-1"></div>
    <div class="sonar-ring ring-2"></div>
    <div class="sonar-ring ring-3"></div>
    <div class="sonar-ring ring-4"></div>
  </div>

  <!-- ================= FLOATING AMBIENT STATUS CHIPS ================= -->
  <!-- Desktop Absolute Placements / Mobile Row -->
  <div
    class="ambient-chips-container"
    class:faded-out={isCenterSheet}
    role="region"
    aria-label="Quick glance status chips"
  >
    {#each ambientChips as chip}
      <button
        type="button"
        class="ambient-chip {chip.posClass} {chip.animClass}"
        on:click={() => onSend(chip.prompt)}
        aria-label="{chip.label}: click to query"
      >
        <span class="chip-status-dot {chip.dotClass}" aria-hidden="true"></span>
        <span class="chip-text">{chip.label}</span>
      </button>
    {/each}
  </div>

  <!-- ================= CENTRAL HERO STAGE ================= -->
  <div class="center-stage" class:has-sheet={isCenterSheet}>
    {#if isCenterSheet}
      <!-- Concentric Circles & Halos centered directly on the 64px Sheet Orb -->
      <div class="sheet-orb-concentric" aria-hidden="true">
        <div class="concentric-layer halo-outer"></div>
        <div class="concentric-layer halo-middle"></div>
        <div class="concentric-wire wire-1"></div>
        <div class="concentric-wire wire-2"></div>
        <div class="concentric-wire wire-3"></div>
      </div>
    {/if}

    <!-- Glowing Central Orb -->
    <div class="orb-stage" class:sheet-orb={isCenterSheet}>
      <Orb state={$orbState} size={isCenterSheet ? "sheet" : "hero"} onClick={handleOrbClick} />
      {#if !isCenterSheet}
        <Waveform state={$orbState} />
      {/if}
    </div>

    {#if !isCenterSheet}
      <!-- Spoken Caption with highlight word -->
      <div class="caption-area" aria-live="polite">
        <p class="caption-text" class:mic-muted={!$alexaMicEnabled}>
          {caption.prefix}<span class="caption-em">{caption.highlight}</span>{caption.suffix}
        </p>
      </div>

      <!-- Suggestion Pills (What is expiring soon? | Check schemes | More ▾) -->
      <div class="pills-wrapper">
        <QuickChips onChipClick={onSend} />
      </div>

      <!-- Ask Bar / Mic input dock -->
      <div class="bottom-dock">
        <InputDock onSend={onSend} />
      </div>
    {/if}

    <!-- ================= CENTER SHEET (FOR ALL QUERIES) ================= -->
    {#if isCenterSheet && lastAssistantMsg}
      <div class="sheet-container">
        {#if lastAssistantMsg.resultType === 'dependency_audit' && lastAssistantMsg.resultData}
          <DependencyGraphDAG
            data={{ ...lastAssistantMsg.resultData, memberName: lastAssistantMsg.resultData.memberName || elder }}
            onAction={(cmd) => onSend(cmd)}
            onClose={dismissResult}
          />
        {:else if lastAssistantMsg.resultType === 'bureaucratic_conflicts' && lastAssistantMsg.resultData}
          <ConflictSimulatorDAG
            data={{ ...lastAssistantMsg.resultData, memberName: lastAssistantMsg.resultData.memberName || elder }}
            onAction={(cmd) => onSend(cmd)}
            onClose={dismissResult}
          />
        {:else if lastAssistantMsg.resultType === 'explain_generation' && lastAssistantMsg.resultData}
          <VoiceDialectsDAG
            data={{ ...lastAssistantMsg.resultData, memberName: lastAssistantMsg.resultData.memberName || elder }}
            onAction={(cmd) => onSend(cmd)}
            onClose={dismissResult}
          />
        {:else if lastAssistantMsg.resultType === 'life_event' && lastAssistantMsg.resultData}
          <LifeEventDAG
            data={{ ...lastAssistantMsg.resultData, memberName: lastAssistantMsg.resultData.memberName || elder }}
            onAction={(cmd) => onSend(cmd)}
            onClose={dismissResult}
          />
        {:else}
          {@const sp = getGeneralSheetProps(lastAssistantMsg, lastUserMsg)}
          <CenterSheet
            query={sp.query}
            headline={sp.headline}
            accentWord={sp.accentWord}
            chips={sp.chips}
            onClose={dismissResult}
          >
            <div class="general-sheet-content">
              {#if lastAssistantMsg.resultType === 'family_dashboard' && lastAssistantMsg.resultData}
                <FamilyBrief data={{
                  raw: lastAssistantMsg.text,
                  expiringCount: lastAssistantMsg.resultData.metrics?.expiringDocs ?? 0,
                  tasksCount: lastAssistantMsg.resultData.metrics?.pendingTasks ?? 0
                }} />
              {:else if lastAssistantMsg.resultType === 'expiring_docs' && lastAssistantMsg.resultData}
                <ExpiringDocs data={lastAssistantMsg.resultData} />
              {:else if lastAssistantMsg.resultType === 'family_brief' && lastAssistantMsg.resultData}
                <FamilyBrief data={lastAssistantMsg.resultData} />
              {:else if lastAssistantMsg.resultType === 'scheme_eligibility' && lastAssistantMsg.resultData}
                <SchemeEligibility data={lastAssistantMsg.resultData} />
              {:else if lastAssistantMsg.resultType === 'scheme_checklist' && lastAssistantMsg.resultData}
                <SchemeChecklist data={lastAssistantMsg.resultData} />
              {:else if lastAssistantMsg.resultType === 'plan_application' && lastAssistantMsg.resultData}
                <PlanApplication data={lastAssistantMsg.resultData} />
              {:else if lastAssistantMsg.resultType === 'upcoming_tasks' && lastAssistantMsg.resultData}
                <UpcomingTasks data={lastAssistantMsg.resultData} />
              {:else}
                <div class="general-text-response">
                  {#each (lastAssistantMsg.text || '').split('\n') as paragraph}
                    {#if paragraph.trim() && !paragraph.trim().match(/^[=-]{3,}/)}
                      <p class="general-text-p">{paragraph}</p>
                    {/if}
                  {/each}
                </div>
              {/if}
            </div>
          </CenterSheet>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  /* ================= AMBIENT CANVAS ================= */
  .ambient-canvas {
    position: relative;
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding: var(--sp-24) var(--sp-16) var(--sp-20) var(--sp-16);
    overflow: visible;
  }

  /* Dotted Grid Background - subtle design texture, non-intrusive */
  .dotted-grid {
    position: absolute;
    inset: 0;
    background-image: radial-gradient(circle, rgba(60, 64, 67, 0.12) 1px, transparent 1.25px);
    background-size: 28px 28px;
    opacity: 1;
    pointer-events: none;
    z-index: 0;
  }
  :global([data-theme="dark"]) .dotted-grid {
    opacity: 1;
    background-image: radial-gradient(circle, rgba(255, 255, 255, 0.09) 1px, transparent 1.25px);
  }

  /* Concentric Sonar Rings - perfectly centered on the 140px hero orb center (padding 24px + margin-top 12px + half-orb 70px = 106px) */
  .sonar-container {
    position: absolute;
    top: 106px;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 0;
    height: 0;
    pointer-events: none;
    z-index: 0;
    transition: opacity 300ms ease;
  }

  .sonar-container.faded-out {
    opacity: 0;
    pointer-events: none;
  }

  .sonar-ring {
    position: absolute;
    border-radius: 50%;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    border: 1px solid var(--accent);
  }

  .ring-1 {
    width: 340px;
    height: 340px;
    opacity: 0.18;
  }
  .ring-2 {
    width: 620px;
    height: 620px;
    opacity: 0.12;
  }
  .ring-3 {
    width: 920px;
    height: 920px;
    opacity: 0.07;
  }
  .ring-4 {
    width: 1260px;
    height: 1260px;
    opacity: 0.04;
  }

  /* ================= FLOATING AMBIENT CHIPS ================= */
  .ambient-chips-container {
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 5;
    max-width: 1320px;
    margin: 0 auto;
    transition: opacity 300ms ease;
  }

  .ambient-chips-container.faded-out {
    opacity: 0;
    pointer-events: none;
  }

  .ambient-chip {
    position: absolute;
    pointer-events: auto;
    display: inline-flex;
    align-items: center;
    gap: var(--sp-8);
    height: 36px;
    padding: 0 var(--sp-16);
    background: var(--surface);
    border: 1px solid var(--line-soft);
    border-radius: var(--r-pill);
    box-shadow: 0 4px 14px rgba(60, 64, 67, 0.09);
    cursor: pointer;
    font-family: var(--font-ui);
    font-size: 13px;
    font-weight: 500;
    color: var(--text);
    transition: transform var(--dur-fast) var(--ease), border-color var(--dur-fast) var(--ease), box-shadow var(--dur-fast) var(--ease);
    white-space: nowrap;
  }

  :global([data-theme="dark"]) .ambient-chip {
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);
    background: var(--surface);
  }

  .ambient-chip:hover {
    border-color: var(--accent);
    transform: scale(1.05) translateY(-2px);
    box-shadow: 0 6px 20px rgba(66, 133, 244, 0.16);
  }

  .chip-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .dot-urgent {
    background: var(--urgent);
    box-shadow: 0 0 6px rgba(234, 67, 53, 0.5);
  }
  .dot-soon {
    background: var(--soon);
    box-shadow: 0 0 6px rgba(251, 188, 4, 0.5);
  }
  .dot-ok {
    background: var(--ok);
    box-shadow: 0 0 6px rgba(52, 168, 83, 0.5);
  }
  .dot-info {
    background: #8b5cf6;
    box-shadow: 0 0 6px rgba(139, 92, 246, 0.5);
  }
  .dot-accent {
    background: var(--accent);
    box-shadow: 0 0 6px rgba(66, 133, 244, 0.5);
  }
  .dot-live {
    background: #06b6d4;
    box-shadow: 0 0 8px rgba(6, 182, 212, 0.7);
  }

  /* Precise positions matching the "4. Ambient" layout design — safely spaced along sonar rings */
  .pos-top-left {
    right: calc(50% + 430px);
    top: 75px;
  }
  .pos-mid-left {
    right: calc(50% + 350px);
    top: 220px;
  }
  .pos-bot-left {
    right: calc(50% + 440px);
    top: 380px;
  }
  .pos-top-right {
    left: calc(50% + 430px);
    top: 105px;
  }
  .pos-bot-right {
    left: calc(50% + 360px);
    top: 275px;
  }

  /* Gentle Floating Animations */
  .float-1 {
    animation: ambient-bob-1 4.5s ease-in-out infinite;
  }
  .float-2 {
    animation: ambient-bob-2 5.2s ease-in-out infinite;
    animation-delay: 0.8s;
  }
  .float-3 {
    animation: ambient-bob-3 4.8s ease-in-out infinite;
    animation-delay: 1.6s;
  }

  @keyframes ambient-bob-1 {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-3px); }
  }
  @keyframes ambient-bob-2 {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-4px); }
  }
  @keyframes ambient-bob-3 {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-3px); }
  }

  /* ================= CENTER STAGE ================= */
  .center-stage {
    position: relative;
    z-index: 10;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--sp-16);
    max-width: 560px;
    width: 100%;
    margin-top: 12px;
    transition: max-width 400ms var(--ease), gap 400ms var(--ease);
  }

  .center-stage.has-sheet {
    max-width: 860px;
    gap: 0;
    margin-top: 0;
  }

  /* Orb + Waveform */
  .orb-stage {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--sp-16);
    transition: all 400ms var(--ease);
  }

  .orb-stage.sheet-orb {
    gap: 0;
    margin-bottom: -32px;
    position: relative;
    z-index: 25;
  }

  /* ================= CONCENTRIC CIRCLES & HALOS AROUND SHEET ORB ================= */
  .sheet-orb-concentric {
    position: absolute;
    top: 32px;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 0;
    height: 0;
    pointer-events: none;
    z-index: 2;
  }

  .concentric-layer {
    position: absolute;
    border-radius: 50%;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    pointer-events: none;
  }

  /* 1. Outer halo: r=24 ratio (128px) */
  .concentric-layer.halo-outer {
    width: 128px;
    height: 128px;
    background: var(--logo-halo);
    opacity: 0.85;
  }

  /* 2. Middle ring: r=18 ratio (96px) */
  .concentric-layer.halo-middle {
    width: 96px;
    height: 96px;
    background: var(--logo-ring);
    opacity: 0.65;
  }

  /* 3. Concentric wire circles radiating outward */
  .concentric-wire {
    position: absolute;
    border-radius: 50%;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    border: 1px solid var(--accent);
    pointer-events: none;
  }

  .wire-1 {
    width: 180px;
    height: 180px;
    opacity: 0.20;
  }

  .wire-2 {
    width: 260px;
    height: 260px;
    opacity: 0.12;
  }

  .wire-3 {
    width: 380px;
    height: 380px;
    opacity: 0.06;
  }

  .sheet-container {
    width: 100%;
    display: flex;
    justify-content: center;
    position: relative;
    z-index: 12;
  }

  .sheet-backdrop {
    position: fixed;
    inset: 0;
    background: transparent;
    border: none;
    z-index: 6;
    cursor: default;
    padding: 0;
    margin: 0;
  }

  /* Spoken Caption */
  .caption-area {
    text-align: center;
    max-width: 600px;
    padding: 0 var(--sp-16);
    margin-top: 10px;
  }

  .caption-text {
    font-family: var(--font-ui);
    font-size: 22px;
    font-weight: 400;
    line-height: 1.45;
    letter-spacing: -0.01em;
    color: var(--text);
    text-wrap: balance;
  }

  .caption-em {
    font-weight: 600;
    color: var(--caption-em);
  }

  .caption-text.mic-muted .caption-em {
    color: var(--urgent);
  }

  /* Pills Wrapper */
  .pills-wrapper {
    width: 100%;
    display: flex;
    justify-content: center;
    margin-top: 10px;
  }

  /* Bottom Dock */
  .bottom-dock {
    width: 100%;
    max-width: 520px;
    margin-top: 10px;
  }

  /* ================= GENERAL CENTER SHEET CONTENT ================= */
  .general-sheet-content {
    width: 100%;
    max-height: 58vh;
    overflow-y: auto;
    padding-right: 4px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .general-sheet-content::-webkit-scrollbar {
    width: 6px;
  }

  .general-sheet-content::-webkit-scrollbar-track {
    background: transparent;
  }

  .general-sheet-content::-webkit-scrollbar-thumb {
    background: var(--cs-pill-border);
    border-radius: 999px;
  }

  .general-text-response {
    background: var(--cs-pill);
    border: 1px solid var(--cs-pill-border);
    border-radius: 18px;
    padding: 16px 20px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .general-text-p {
    margin: 0;
    font-size: 14.5px;
    line-height: 1.6;
    color: var(--cs-ink);
    font-family: inherit;
  }

  /* ================= RESPONSIVE ================= */
  @media (max-width: 1080px) {
    .ambient-chips-container {
      position: static;
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: var(--sp-8);
      margin-bottom: var(--sp-16);
      max-width: 600px;
    }

    .ambient-chip {
      position: static;
      animation: none;
    }

    .pos-top-left, .pos-mid-left, .pos-bot-left, .pos-top-right, .pos-bot-right {
      left: auto;
      right: auto;
      top: auto;
    }

    .ring-3, .ring-4 {
      display: none;
    }
  }

  @media (max-width: 640px) {
    .caption-text {
      font-size: 18px;
      line-height: 1.4;
    }
    .ambient-canvas {
      padding: var(--sp-16) var(--sp-12) var(--sp-48) var(--sp-12);
    }
  }
</style>
