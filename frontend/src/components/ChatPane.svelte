<script>
  // ChatPane.svelte
  // The scrollable list of messages. Each message is a MessageBubble.
  // aria-live="polite" announces new messages to screen readers.

  import { messages } from '../lib/store.js';
  import MessageBubble from './MessageBubble.svelte';
  import { afterUpdate } from 'svelte';

  let listEl;

  // Auto-scroll to bottom whenever messages update
  afterUpdate(() => {
    if (listEl) {
      listEl.scrollTop = listEl.scrollHeight;
    }
  });
</script>

<div
  class="chat-pane"
  bind:this={listEl}
  role="log"
  aria-live="polite"
  aria-label="Conversation"
  aria-relevant="additions"
>
  {#if $messages.length === 0}
    <!-- Empty state -->
    <div class="empty-state">
      <!-- Inline SVG illustration: scattered dots converging -->
      <svg width="64" height="64" viewBox="0 0 64 64" fill="none" aria-hidden="true">
        <circle cx="10" cy="20" r="4" fill="var(--violet)" opacity="0.25"/>
        <circle cx="28" cy="10" r="5" fill="var(--teal)"   opacity="0.35"/>
        <circle cx="50" cy="18" r="3" fill="var(--sky)"    opacity="0.25"/>
        <circle cx="16" cy="46" r="4" fill="var(--amber)"  opacity="0.30"/>
        <circle cx="48" cy="50" r="5" fill="var(--coral)"  opacity="0.25"/>
        <!-- Converging lines to centre -->
        <line x1="10" y1="20" x2="32" y2="32" stroke="var(--violet)" stroke-width="1" opacity="0.2"/>
        <line x1="28" y1="10" x2="32" y2="32" stroke="var(--teal)"   stroke-width="1" opacity="0.2"/>
        <line x1="50" y1="18" x2="32" y2="32" stroke="var(--sky)"    stroke-width="1" opacity="0.2"/>
        <line x1="16" y1="46" x2="32" y2="32" stroke="var(--amber)"  stroke-width="1" opacity="0.2"/>
        <line x1="48" y1="50" x2="32" y2="32" stroke="var(--coral)"  stroke-width="1" opacity="0.2"/>
        <circle cx="32" cy="32" r="7" fill="var(--violet)" opacity="0.8"/>
      </svg>

      <h2 class="empty-title">Hi, I'm Glean.</h2>
      <p class="empty-body">
        Your family's documents, deadlines and scheme eligibility — gathered in one place.
        Ask me anything, or tap a quick action below.
      </p>
      <ul class="empty-hints" aria-label="Example questions">
        <li><em>"What documents are expiring soon?"</em></li>
        <li><em>"What schemes does Ramesh qualify for?"</em></li>
        <li><em>"Plan the SCSS application for Suresh."</em></li>
        <li><em>"Give me the family morning briefing."</em></li>
      </ul>
      <p class="empty-disclaimer">
        Glean gives guidance only. Verify on the official site.
      </p>
    </div>
  {:else}
    {#each $messages as msg, i (msg.id)}
      <MessageBubble {msg} index={i} />
    {/each}
  {/if}
</div>

<style>
  .chat-pane {
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-xl);
    padding: var(--sp-5);
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: var(--sp-4);
    box-shadow: var(--shadow);
    transition: var(--theme-transition);
    scroll-behavior: smooth;
  }

  /* Empty state */
  .empty-state {
    margin: auto;
    max-width: 420px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--sp-4);
    padding: var(--sp-8) 0;
  }

  .empty-title {
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -0.03em;
  }

  .empty-body {
    font-size: 0.92rem;
    color: var(--text-2);
    line-height: 1.6;
  }

  .empty-hints {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: var(--sp-2);
    text-align: left;
    width: 100%;
  }

  .empty-hints li {
    font-size: 0.85rem;
    color: var(--text-muted);
    padding: 8px var(--sp-3);
    background: var(--surface-2);
    border-radius: var(--r-md);
    border-left: 3px solid var(--violet);
  }

  .empty-disclaimer {
    font-size: 0.72rem;
    color: var(--text-muted);
    opacity: 0.7;
  }
</style>
