<script>
  import { activePersona } from '../lib/store.js';
  import { ChevronDown, Sparkles } from '@lucide/svelte';

  export let onChipClick = (/** @type {string} */ _text) => {};

  let showMore = false;

  $: elder = $activePersona && ['chandler', 'amy', 'justin'].includes($activePersona.toLowerCase())
    ? $activePersona
    : 'Chandler';

  $: primaryPills = [
    { label: 'What is expiring soon?', prompt: 'What documents are expiring soon?' },
    { label: 'Check schemes', prompt: `What schemes does ${elder} qualify for?` },
  ];

  $: morePills = [
    { label: `Plan SCSS for ${elder}`, prompt: `Plan the SCSS application for ${elder}` },
    { label: 'Morning briefing', prompt: $activePersona && $activePersona !== 'all' ? `Give me the morning briefing for ${$activePersona}` : 'Give me the full family briefing' },
    { label: 'Annual family review', prompt: 'Run the annual family review' },
    { label: 'Ayushman checklist', prompt: 'What documents are needed for Ayushman Vay Vandana?' },
    { label: 'Family member roster', prompt: 'List all family members' },
    { label: 'Tasks in next 30 days', prompt: 'What tasks are coming up in the next 30 days?' },
  ];
</script>

<div class="suggestion-area" role="region" aria-label="Suggested questions">
  <div class="pills-row">
    {#each primaryPills as pill}
      <button
        type="button"
        class="vr-pill"
        on:click={() => onChipClick(pill.prompt)}
      >
        <span>{pill.label}</span>
      </button>
    {/each}

    <!-- "More" popover / dropdown button -->
    <button
      type="button"
      class="vr-pill more-btn"
      class:active={showMore}
      on:click={() => (showMore = !showMore)}
      aria-expanded={showMore}
      aria-label="More suggested actions"
    >
      <span>More</span>
      <ChevronDown size={14} class="chevron {showMore ? 'open' : ''}" />
    </button>
  </div>

  {#if showMore}
    <div class="more-drawer">
      {#each morePills as pill}
        <button
          type="button"
          class="vr-pill secondary"
          on:click={() => { onChipClick(pill.prompt); showMore = false; }}
        >
          <span>{pill.label}</span>
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .suggestion-area {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--sp-8);
  }

  .pills-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: var(--sp-8);
    max-width: 100%;
  }

  .more-btn {
    color: var(--text-muted);
  }
  .more-btn.active {
    border-color: var(--accent);
    color: var(--accent);
    background: var(--surface-2);
  }

  .chevron {
    transition: transform var(--dur-fast) var(--ease);
  }
  .chevron.open {
    transform: rotate(180deg);
  }

  .more-drawer {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: var(--sp-8);
    padding: var(--sp-8);
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
    border-radius: var(--r-card);
    box-shadow: var(--shadow-card);
    animation: fade-down 150ms var(--ease);
  }

  .vr-pill.secondary {
    background: var(--surface);
    font-size: var(--fs-label);
  }

  @keyframes fade-down {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: translateY(0); }
  }
</style>
