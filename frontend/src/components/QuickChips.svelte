<script>
  import { activePersona, showSuggestedActions } from '../lib/store.js';
  import { ChevronRight } from '@lucide/svelte';

  export let onChipClick = (/** @type {string} */ _text) => {};

  $: elder = $activePersona && ['chandler', 'amy', 'justin'].includes($activePersona.toLowerCase())
    ? $activePersona
    : 'Chandler';

  $: primaryPills = [
    { label: 'What is expiring soon?', prompt: 'What documents are expiring in the next 60 days?' },
    { label: `Check schemes for ${elder}`, prompt: `What schemes does ${elder} qualify for?` },
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

    <!-- "More Actions" button (clean text, no sparkle, opens root side banner) -->
    <button
      type="button"
      class="vr-pill more-btn"
      class:active={$showSuggestedActions}
      on:click={() => showSuggestedActions.set(true)}
      aria-expanded={$showSuggestedActions}
      aria-label="Open suggested actions side banner"
    >
      <span>More Actions</span>
      <ChevronRight size={14} class="more-arrow" />
    </button>
  </div>
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
    color: var(--text-soft);
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-weight: 500;
  }
  .more-btn.active,
  .more-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
    background: var(--surface-2);
  }

  .more-arrow {
    transition: transform var(--dur-fast) var(--ease);
  }
  .more-btn:hover .more-arrow {
    transform: translateX(2px);
  }
</style>
