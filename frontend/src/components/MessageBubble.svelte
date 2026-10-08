<script>
  // MessageBubble.svelte
  // One message in the chat — either from the user or from Glean.
  // Glean messages route to a rich renderer if resultType is set,
  // or fall back to plain text.

  import ToolCallChip from './ToolCallChip.svelte';
  import { settings } from '../lib/store.js';

  // Lazy-loaded result renderers (imported inline so App.svelte stays small)
  import ExpiringDocs     from './results/ExpiringDocs.svelte';
  import UpcomingTasks    from './results/UpcomingTasks.svelte';
  import SchemeEligibility from './results/SchemeEligibility.svelte';
  import SchemeChecklist  from './results/SchemeChecklist.svelte';
  import PlanApplication  from './results/PlanApplication.svelte';
  import FamilyBrief      from './results/FamilyBrief.svelte';

  export let msg = {};
  export let index = 0;

  const RENDERERS = {
    expiring_docs:      ExpiringDocs,
    upcoming_tasks:     UpcomingTasks,
    scheme_eligibility: SchemeEligibility,
    scheme_checklist:   SchemeChecklist,
    plan_application:   PlanApplication,
    family_brief:       FamilyBrief,
  };

  $: renderer = msg.resultType ? RENDERERS[msg.resultType] : null;
  // Stagger entrance animation based on position
  $: delay = Math.min(index * 40, 200);
</script>

<div
  class="bubble-wrap"
  class:user={msg.role === 'user'}
  class:assistant={msg.role === 'assistant'}
  style="animation-delay: {delay}ms"
  aria-label="{msg.role === 'user' ? 'You said' : 'Glean said'}: {msg.text?.slice(0, 80)}"
>
  {#if msg.role === 'assistant'}
    <!-- Glean avatar dot -->
    <div class="avatar" aria-hidden="true">
      <svg width="20" height="20" viewBox="0 0 36 36" fill="none">
        <rect width="36" height="36" rx="10" fill="var(--violet)"/>
        <circle cx="11" cy="9"  r="2.2" fill="white" opacity="0.55"/>
        <circle cx="18" cy="7"  r="2.2" fill="white" opacity="0.75"/>
        <circle cx="25" cy="9"  r="2.2" fill="white"/>
        <circle cx="27" cy="18" r="2.2" fill="white"/>
        <circle cx="27" cy="25" r="2.2" fill="var(--teal)"/>
        <circle cx="21" cy="27" r="2.2" fill="var(--teal)" opacity="0.85"/>
      </svg>
    </div>
  {/if}

  <div class="content">
    <!-- Sender label -->
    <span class="sender-label" aria-hidden="true">
      {msg.role === 'user' ? 'You' : 'Glean'}
    </span>

    <!-- Bubble -->
    <div class="bubble">
      {#if msg.streaming}
        <!-- Thinking indicator while streaming -->
        <span class="thinking" aria-label="Glean is thinking">
          <span></span><span></span><span></span>
        </span>
      {:else if renderer && msg.resultData}
        <!-- Rich structured renderer -->
        <svelte:component this={renderer} data={msg.resultData} />
      {:else}
        <!-- Plain text fallback (whitespace-preserving) -->
        <p class="plain-text">{msg.text}</p>
      {/if}
    </div>

    <!-- Tool call chip (only on assistant messages, if enabled) -->
    {#if msg.role === 'assistant' && msg.toolCall && $settings.showToolCalls}
      <ToolCallChip
        toolName={msg.toolCall.name}
        toolArgs={msg.toolCall.args}
        rawResult={msg.toolCall.result}
        isLive={msg.toolCall.isLive}
        ms={msg.toolCall.ms}
      />
    {/if}
  </div>
</div>

<style>
  .bubble-wrap {
    display: flex;
    gap: var(--sp-2);
    max-width: 86%;
    animation: slide-up var(--t-base) var(--ease-out) both;
  }

  @keyframes slide-up {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .bubble-wrap.user {
    align-self: flex-end;
    flex-direction: row-reverse;
  }

  .bubble-wrap.assistant {
    align-self: flex-start;
    max-width: 90%;
  }

  .avatar {
    flex-shrink: 0;
    margin-top: 18px; /* aligns with bubble top */
  }

  .content {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .sender-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--text-muted);
  }

  .bubble-wrap.user .sender-label { text-align: right; }

  .bubble {
    padding: var(--sp-3) var(--sp-4);
    border-radius: var(--r-lg);
    line-height: 1.6;
    font-size: 0.9rem;
  }

  /* User bubble: sky gradient */
  .bubble-wrap.user .bubble {
    background: linear-gradient(135deg, var(--sky) 0%, color-mix(in srgb, var(--sky) 70%, var(--violet)) 100%);
    color: white;
    border-bottom-right-radius: 4px;
    box-shadow: 0 3px 12px color-mix(in srgb, var(--sky) 30%, transparent);
  }

  /* Assistant bubble: surface */
  .bubble-wrap.assistant .bubble {
    background: var(--surface-2);
    border: 1px solid var(--border);
    color: var(--text);
    border-bottom-left-radius: 4px;
    box-shadow: var(--shadow);
  }

  .plain-text {
    white-space: pre-wrap;
    margin: 0;
  }

  /* Thinking dots */
  .thinking {
    display: flex;
    gap: 5px;
    padding: var(--sp-1) 0;
  }

  .thinking span {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--violet);
    animation: dot-bounce 1.2s ease-in-out infinite;
  }

  .thinking span:nth-child(2) { animation-delay: 0.2s; }
  .thinking span:nth-child(3) { animation-delay: 0.4s; }

  @keyframes dot-bounce {
    0%, 80%, 100% { transform: translateY(0);    opacity: 0.4; }
    40%           { transform: translateY(-6px);  opacity: 1; }
  }
</style>
