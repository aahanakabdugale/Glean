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
  import { X } from '@lucide/svelte';

  export let onSend = (/** @type {string} */ _text) => {};

  $: elder = $activePersona && $activePersona !== 'all' ? $activePersona : 'Chandler';

  // Find latest assistant reply for the big caption and answer card
  $: lastAssistantMsg = [...$messages].reverse().find(m => m.role === 'assistant');
  $: lastUserMsg = [...$messages].reverse().find(m => m.role === 'user');

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

  // Floating Ambient Status Chips (as specified in "4. Ambient")
  const ambientChips = [
    {
      id: 'chip-passport',
      side: 'left',
      posClass: 'pos-top-left',
      animClass: 'float-1',
      dotClass: 'dot-urgent',
      label: 'Passport 6d',
      prompt: 'What documents are expiring soon?',
    },
    {
      id: 'chip-insurance',
      side: 'left',
      posClass: 'pos-mid-left',
      animClass: 'float-2',
      dotClass: 'dot-soon',
      label: 'Insurance 12d',
      prompt: 'What tasks are coming up in the next 30 days?',
    },
    {
      id: 'chip-transit',
      side: 'left',
      posClass: 'pos-bot-left',
      animClass: 'float-3',
      dotClass: 'dot-ok',
      label: 'Transit pass 15d',
      prompt: 'Check scheme checklist for Ayushman card',
    },
    {
      id: 'chip-schemes',
      side: 'right',
      posClass: 'pos-top-right',
      animClass: 'float-2',
      dotClass: 'dot-info',
      label: '3 schemes may fit',
      prompt: 'What schemes does my family qualify for?',
    },
    {
      id: 'chip-members',
      side: 'right',
      posClass: 'pos-bot-right',
      animClass: 'float-1',
      dotClass: 'dot-info',
      label: '6 family members',
      prompt: 'List all family members',
    },
  ];

  function dismissResult() {
    clearMessages();
  }
</script>

<div class="ambient-canvas">
  <!-- Subtle Dotted Grid across entire canvas -->
  <div class="dotted-grid" aria-hidden="true"></div>

  <!-- Concentric Sonar Rings expanding from the central orb -->
  <div class="sonar-container" aria-hidden="true">
    <div class="sonar-ring ring-1"></div>
    <div class="sonar-ring ring-2"></div>
    <div class="sonar-ring ring-3"></div>
    <div class="sonar-ring ring-4"></div>
  </div>

  <!-- ================= FLOATING AMBIENT STATUS CHIPS ================= -->
  <!-- Desktop Absolute Placements / Mobile Row -->
  <div class="ambient-chips-container" role="region" aria-label="Quick glance status chips">
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
  <div class="center-stage">
    <!-- Glowing Central Orb -->
    <div class="orb-stage">
      <Orb state={$orbState} size="hero" onClick={handleOrbClick} />
      <Waveform state={$orbState} />
    </div>

    <!-- Spoken Caption with highlight word -->
    <div class="caption-area" aria-live="polite">
      <p class="caption-text">
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

    <!-- ================= STRUCTURED ANSWER CARD (WHEN ACTIVE) ================= -->
    {#if lastAssistantMsg}
      <div class="structured-answer-card vr-card" role="region" aria-label="Assistant response">
        <div class="card-header-bar">
          {#if lastUserMsg}
            <div class="user-query-pill">
              <span class="text-small">You asked: <strong>{lastUserMsg.text}</strong></span>
            </div>
          {/if}
          <button
            type="button"
            class="dismiss-btn"
            on:click={dismissResult}
            aria-label="Dismiss result and return to ambient view"
            title="Return to ambient view"
          >
            <X size={15} />
            <span>Return to Ambient</span>
          </button>
        </div>

        <div class="assistant-content">
          {#if lastAssistantMsg.resultType === 'expiring_docs' && lastAssistantMsg.resultData}
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
            <p class="plain-reply text-body">{lastAssistantMsg.text}</p>
          {/if}

          {#if lastAssistantMsg.toolCall}
            <ToolCallChip
              toolName={lastAssistantMsg.toolCall.name}
              toolArgs={lastAssistantMsg.toolCall.args}
              rawResult={lastAssistantMsg.toolCall.result}
              isLive={lastAssistantMsg.toolCall.isLive}
              ms={lastAssistantMsg.toolCall.ms}
            />
          {/if}
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  /* ================= AMBIENT CANVAS ================= */
  .ambient-canvas {
    position: relative;
    width: 100%;
    min-height: calc(100vh - 130px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding: var(--sp-32) var(--sp-16) var(--sp-64) var(--sp-16);
    overflow: hidden;
  }

  /* Dotted Grid Background */
  .dotted-grid {
    position: absolute;
    inset: 0;
    background-image: radial-gradient(circle, var(--line) 1.25px, transparent 1.25px);
    background-size: 28px 28px;
    opacity: 0.55;
    pointer-events: none;
    z-index: 0;
  }
  :global([data-theme="dark"]) .dotted-grid {
    opacity: 0.16;
    background-image: radial-gradient(circle, rgba(255, 255, 255, 0.25) 1.25px, transparent 1.25px);
  }

  /* Concentric Sonar Rings */
  .sonar-container {
    position: absolute;
    top: 130px;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 0;
    height: 0;
    pointer-events: none;
    z-index: 0;
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
    opacity: 0.14;
  }
  .ring-2 {
    width: 620px;
    height: 620px;
    opacity: 0.085;
  }
  .ring-3 {
    width: 920px;
    height: 920px;
    opacity: 0.045;
  }
  .ring-4 {
    width: 1260px;
    height: 1260px;
    opacity: 0.025;
  }

  /* ================= FLOATING AMBIENT CHIPS ================= */
  .ambient-chips-container {
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 5;
    max-width: 1320px;
    margin: 0 auto;
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
  }
  .dot-soon {
    background: var(--soon);
  }
  .dot-ok {
    background: var(--ok);
  }
  .dot-info {
    background: var(--accent);
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
    gap: var(--sp-20);
    max-width: 560px;
    width: 100%;
    margin-top: var(--sp-8);
  }

  /* Orb + Waveform */
  .orb-stage {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--sp-16);
  }

  /* Spoken Caption */
  .caption-area {
    text-align: center;
    max-width: 520px;
    padding: 0 var(--sp-12);
  }

  .caption-text {
    font-family: var(--font-ui);
    font-size: var(--fs-caption);
    font-weight: 300;
    line-height: var(--lh-caption);
    color: var(--text);
  }

  .caption-em {
    font-weight: 600;
    color: var(--caption-em);
  }

  /* Pills Wrapper */
  .pills-wrapper {
    width: 100%;
    display: flex;
    justify-content: center;
  }

  /* Bottom Dock */
  .bottom-dock {
    width: 100%;
    max-width: 520px;
  }

  /* ================= STRUCTURED ANSWER CARD ================= */
  .structured-answer-card {
    width: 100%;
    padding: var(--sp-24);
    display: flex;
    flex-direction: column;
    gap: var(--sp-16);
    background: var(--surface);
    border: 1px solid var(--line-soft);
    border-radius: var(--r-card);
    box-shadow: var(--shadow-pop);
    animation: fade-up 220ms var(--ease);
    margin-top: var(--sp-16);
  }

  @keyframes fade-up {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .card-header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--sp-12);
    padding-bottom: var(--sp-12);
    border-bottom: 1px solid var(--line-soft);
  }

  .user-query-pill {
    background: var(--surface-2);
    padding: var(--sp-4) var(--sp-12);
    border-radius: var(--r-pill);
    color: var(--text-soft);
  }

  .dismiss-btn {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-6);
    background: transparent;
    border: 1px solid var(--line-soft);
    border-radius: var(--r-pill);
    padding: var(--sp-4) var(--sp-12);
    color: var(--text-muted);
    font-family: var(--font-ui);
    font-size: var(--fs-small);
    font-weight: 500;
    cursor: pointer;
    transition: all var(--dur-fast) var(--ease);
  }
  .dismiss-btn:hover {
    background: var(--surface-2);
    color: var(--text);
    border-color: var(--line);
  }

  .assistant-content {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: var(--sp-12);
  }

  .plain-reply {
    color: var(--text);
    line-height: var(--lh-body);
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
      font-size: 24px;
    }
    .ambient-canvas {
      padding: var(--sp-16) var(--sp-12) var(--sp-48) var(--sp-12);
    }
  }
</style>
