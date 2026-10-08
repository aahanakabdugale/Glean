<script>
  // QuickChips.svelte
  // Horizontally-scrolling prompt shortcuts. Clicking a chip
  // fires the onChipClick callback with the prompt text.

  export let onChipClick = (/** @type {string} */ _text) => {};

  const chips = [
    { emoji: '📋', label: 'Morning Briefing',    prompt: 'Give me the full family briefing' },
    { emoji: '⏳', label: 'Expiring Docs',        prompt: 'What documents are expiring soon?' },
    { emoji: '🎯', label: "Ramesh's Schemes",     prompt: 'What schemes does Ramesh qualify for?' },
    { emoji: '🚀', label: 'Plan SCSS for Suresh', prompt: 'Plan the SCSS application for Suresh' },
    { emoji: '📑', label: 'Ayushman Checklist',   prompt: 'What documents are needed for Ayushman Vay Vandana?' },
    { emoji: '👨‍👩‍👧‍👦', label: 'Family List',          prompt: 'List all family members' },
    { emoji: '📅', label: 'Upcoming Tasks',       prompt: 'What tasks are coming up in the next 30 days?' },
  ];
</script>

<div class="chips-row" role="list" aria-label="Quick actions">
  {#each chips as chip}
    <li role="listitem" style="list-style:none;display:contents">
    <button
      class="chip"
      on:click={() => onChipClick(chip.prompt)}
      aria-label={chip.label}
    >
      <span class="chip-emoji" aria-hidden="true">{chip.emoji}</span>
      <span>{chip.label}</span>
    </button>
    </li>
  {/each}
</div>

<style>
  .chips-row {
    display: flex;
    gap: var(--sp-2);
    overflow-x: auto;
    padding: var(--sp-1) 2px;
    scrollbar-width: none;
    flex-shrink: 0;
  }

  .chips-row::-webkit-scrollbar { display: none; }

  .chip {
    display: flex;
    align-items: center;
    gap: var(--sp-2);
    padding: 7px var(--sp-3);
    border-radius: var(--r-full);
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text-2);
    font-size: 0.78rem;
    font-weight: 500;
    white-space: nowrap;
    cursor: pointer;
    transition: all var(--t-fast) var(--ease-out);
    font-family: var(--font-body);
  }

  .chip:hover {
    background: var(--violet-bg);
    border-color: var(--violet);
    color: var(--violet-text);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px color-mix(in srgb, var(--violet) 20%, transparent);
  }

  .chip:active {
    transform: translateY(0);
  }

  .chip-emoji {
    font-size: 0.9rem;
  }
</style>
