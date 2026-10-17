<script>
  import { X, ChevronDown, Lock } from 'lucide-svelte';
  import { onMount } from 'svelte';

  export let query = '';
  export let headline = '';
  export let accentWord = '';
  export let accentColor = '#3b82f6'; // hex or css variable
  export let chips = []; // [{ label, color }]
  export let stages = []; // [{ label, nodes: [{ title, subtitle, color, locked?, active?, id? }], reverseConnector?: boolean }]
  export let primaryAction = '';
  export let secondaryAction = '';
  export let details = '';
  export let onPrimary = () => {};
  export let onSecondary = () => {};
  export let onClose = () => {};
  export let onNodeClick = (/** @type {any} */ _node) => {};

  let showDetails = false;

  // Split headline into prefix, accentWord, and suffix
  $: headlineParts = splitHeadline(headline, accentWord);

  function splitHeadline(text, word) {
    if (!word || !text) return { prefix: text || '', accent: '', suffix: '' };
    const idx = text.toLowerCase().indexOf(word.toLowerCase());
    if (idx === -1) return { prefix: text, accent: '', suffix: '' };
    return {
      prefix: text.slice(0, idx),
      accent: text.slice(idx, idx + word.length),
      suffix: text.slice(idx + word.length)
    };
  }

  // Handle escape key
  function handleKeyDown(e) {
    if (e.key === 'Escape') {
      onClose();
    }
  }

  onMount(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  });

  // Map color names to CSS hex
  function resolveColor(col) {
    const map = {
      amber: '#fbbf24',
      red: '#f87171',
      green: '#34d399',
      violet: '#a78bfa',
      cyan: '#22d3ee',
      blue: '#38bdf8',
      muted: 'var(--cs-muted)'
    };
    return map[col] || col || 'var(--cs-accent)';
  }
</script>

<div
  class="center-sheet-wrapper"
  role="dialog"
  aria-modal="true"
  aria-label="Result details"
  style="--feature-accent: {resolveColor(accentColor)};"
>
  <!-- Main Glass Sheet Container -->
  <div class="center-sheet" role="document">
    <!-- (a) Top Header Row -->
    <div class="sheet-top-row">
      <div class="query-pill">
        <span class="query-label">You asked ·</span>
        <span class="query-text">{query}</span>
      </div>

      <button
        type="button"
        class="ambient-close-btn"
        on:click={onClose}
        aria-label="Close"
        title="Close (Esc)"
      >
        <X size={16} />
      </button>
    </div>

    <!-- (b) Headline with Single Accent Word -->
    {#if headline}
      <h2 class="sheet-headline">
        {headlineParts.prefix}<span class="headline-accent">{headlineParts.accent}</span>{headlineParts.suffix}
      </h2>
    {/if}

    <!-- (c) Status Chips Row -->
    {#if chips && chips.length > 0}
      <div class="status-chips-row">
        {#each chips as chip}
          <div class="status-chip">
            <span
              class="glowing-dot"
              style="--dot-color: {resolveColor(chip.color)};"
              aria-hidden="true"
            ></span>
            <span class="chip-label">{chip.label}</span>
          </div>
        {/each}
      </div>
    {/if}

    <!-- (d) The DAG Graph -->
    {#if stages && stages.length > 0}
      <div class="dag-graph-track" role="region" aria-label="Visual process flow">
        {#each stages as stage, sIdx}
          <div class="stage-column">
            {#if stage.label}
              <span class="stage-label">{stage.label}</span>
            {/if}

            <div class="stage-nodes-stack">
              {#each (stage.nodes || []) as node}
                <button
                  type="button"
                  class="dag-node-card"
                  class:locked={node.locked}
                  class:active={node.active}
                  on:click={() => onNodeClick(node)}
                  disabled={!node.active && !stage.clickable && !onNodeClick}
                >
                  <span
                    class="glowing-dot"
                    style="--dot-color: {resolveColor(node.color)};"
                    aria-hidden="true"
                  ></span>

                  <div class="node-texts">
                    <span class="node-title">{node.title}</span>
                    {#if node.subtitle}
                      <span class="node-subtitle">{node.subtitle}</span>
                    {/if}
                  </div>

                  {#if node.locked}
                    <span class="node-lock-wrap"><Lock size={14} /></span>
                  {/if}
                </button>
              {/each}
            </div>
          </div>

          <!-- Connector to Next Stage -->
          {#if sIdx < stages.length - 1}
            <div class="dag-connector-col" aria-hidden="true">
              <svg class="connector-svg desktop-svg" viewBox="0 0 36 20" preserveAspectRatio="none">
                <path
                  d="M 0 10 L 36 10"
                  stroke={resolveColor(stage.connectorColor || accentColor)}
                  stroke-width="1.75"
                  stroke-dasharray="3.5 3"
                  class="flow-dash"
                  fill="none"
                />
              </svg>

              <!-- Mobile Vertical Connector -->
              <svg class="connector-svg mobile-svg" viewBox="0 0 20 28" preserveAspectRatio="none">
                <path
                  d="M 10 0 L 10 28"
                  stroke={resolveColor(stage.connectorColor || accentColor)}
                  stroke-width="1.75"
                  stroke-dasharray="3.5 3"
                  class="flow-dash"
                  fill="none"
                />
              </svg>
            </div>
          {/if}
        {/each}
      </div>
    {/if}

    <!-- (e) General / Structured Results Content Slot -->
    <slot />

    <!-- (f) Optional Extra Row (e.g. Persona Pills for Voice Dialects) -->
    <slot name="extra" />

    <!-- (g) Actions Row -->
    {#if primaryAction || secondaryAction || details}
      <div class="sheet-actions-row">
        {#if primaryAction}
          <button
            type="button"
            class="btn-primary-pill"
            on:click={onPrimary}
          >
            {primaryAction}
          </button>
        {/if}

        {#if secondaryAction}
          <button
            type="button"
            class="btn-ghost-pill"
            on:click={onSecondary}
          >
            {secondaryAction}
          </button>
        {/if}

        {#if details}
          <button
            type="button"
            class="btn-ghost-pill details-btn"
            class:open={showDetails}
            on:click={() => (showDetails = !showDetails)}
            aria-expanded={showDetails}
          >
            <span class="chevron-wrap" class:rotated={showDetails}><ChevronDown size={14} /></span>
            <span>Details</span>
          </button>
        {/if}
      </div>
    {/if}

    <!-- (g) Folded Details Section -->
    {#if showDetails && details}
      <div class="folded-details-section">
        {#if typeof details === 'string'}
          <p class="details-body-text">{details}</p>
        {:else if typeof details === 'object'}
          {#if details.title}
            <div class="details-title">{details.title}</div>
          {/if}
          {#if details.body}
            <div class="details-body">{details.body}</div>
          {/if}
          {#if details.pills && details.pills.length > 0}
            <div class="details-pills-row">
              {#each details.pills as pill}
                <div class="details-pill">
                  <span class="glowing-dot" style="--dot-color: #fbbf24;" aria-hidden="true"></span>
                  <span class="details-pill-text">{pill}</span>
                </div>
              {/each}
            </div>
          {/if}
        {/if}
        <slot name="details-content" />
      </div>
    {/if}
  </div>
</div>

<style>
  /* ================= WRAPPER & BACKDROP ================= */
  .center-sheet-wrapper {
    position: relative;
    width: 100%;
    max-width: 860px;
    margin: 0 auto;
    display: flex;
    justify-content: center;
    z-index: 50;
    font-family: var(--font-ui);
    animation: sheet-fade-up 380ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }

  @keyframes sheet-fade-up {
    0% {
      opacity: 0;
      transform: translateY(14px) scale(0.985);
    }
    100% {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .center-sheet-wrapper {
      animation: none !important;
    }
    .flow-dash {
      animation: none !important;
    }
  }

  /* ================= CENTER SHEET CARD ================= */
  .center-sheet {
    width: 100%;
    background: var(--cs-sheet);
    border: 1px solid var(--cs-pill-border);
    border-radius: 28px;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    box-shadow: 0 24px 64px rgba(0, 0, 0, 0.28), 0 2px 8px rgba(0, 0, 0, 0.08);
    padding: 28px 32px 24px 32px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    box-sizing: border-box;
    color: var(--cs-ink);
  }

  /* ================= (A) TOP ROW ================= */
  .sheet-top-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .query-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--cs-pill);
    border: 1px solid var(--cs-pill-border);
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 13px;
    color: var(--cs-muted);
    max-width: 80%;
  }

  .query-label {
    color: var(--cs-muted);
    font-weight: 400;
  }

  .query-text {
    color: var(--cs-ink);
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .ambient-close-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: transparent;
    border: 1px solid var(--cs-pill-border);
    border-radius: 999px;
    padding: 0;
    color: var(--cs-muted);
    cursor: pointer;
    transition: all 180ms ease;
    flex-shrink: 0;
  }

  .ambient-close-btn:hover {
    background: var(--cs-pill);
    color: var(--cs-ink);
    border-color: var(--cs-ink);
  }

  .ambient-close-btn:focus-visible,
  .btn-primary-pill:focus-visible,
  .btn-ghost-pill:focus-visible,
  .dag-node-card:focus-visible {
    outline: 2px solid var(--feature-accent);
    outline-offset: 2px;
  }

  /* ================= (B) HEADLINE ================= */
  .sheet-headline {
    text-align: center;
    font-size: 26px;
    line-height: 1.35;
    font-weight: 300;
    color: var(--cs-ink);
    margin: 2px 0 0;
    padding: 0 8px;
    letter-spacing: -0.015em;
  }

  .headline-accent {
    font-weight: 600;
    color: var(--cs-accent);
  }

  /* ================= (C) STATUS CHIPS ROW ================= */
  .status-chips-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  .status-chip {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: var(--cs-pill);
    border: 1px solid var(--cs-pill-border);
    border-radius: 999px;
    padding: 4px 12px;
    font-size: 13px;
    font-weight: 400;
    color: var(--cs-ink);
  }

  .glowing-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: var(--dot-color, var(--cs-accent));
    box-shadow: 0 0 8px var(--dot-color, var(--cs-accent));
    flex-shrink: 0;
  }

  /* ================= (D) DAG GRAPH ================= */
  .dag-graph-track {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 4px;
    width: 100%;
    box-sizing: border-box;
    margin: 4px 0;
  }

  .stage-column {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .stage-label {
    font-size: 11px;
    color: var(--cs-muted);
    font-weight: 400;
    text-transform: none; /* small sentence case as per spec */
    padding-left: 2px;
  }

  .stage-nodes-stack {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
  }

  /* Node Cards */
  .dag-node-card {
    display: flex;
    align-items: center;
    gap: 10px;
    background: var(--cs-pill);
    border: 1px solid var(--cs-pill-border);
    border-radius: 18px;
    padding: 10px 14px;
    text-align: left;
    width: 100%;
    box-sizing: border-box;
    cursor: default;
    transition: transform 200ms ease, box-shadow 200ms ease, border-color 200ms ease;
    font-family: inherit;
    color: inherit;
  }

  .dag-node-card:not(:disabled) {
    cursor: pointer;
  }

  .dag-node-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
  }

  .dag-node-card.locked {
    border-style: dashed;
  }

  .dag-node-card.active {
    box-shadow: 0 0 0 2px var(--feature-accent);
    border-color: var(--feature-accent);
  }

  .node-texts {
    display: flex;
    flex-direction: column;
    min-width: 0;
    flex: 1;
  }

  .node-title {
    font-size: 14px;
    font-weight: 500;
    color: var(--cs-ink);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .node-subtitle {
    font-size: 12px;
    color: var(--cs-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .node-lock-wrap {
    color: var(--cs-muted);
    display: inline-flex;
    align-items: center;
    flex-shrink: 0;
  }

  /* Connectors */
  .dag-connector-col {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 48px;
    flex-shrink: 0;
  }

  .connector-svg {
    width: 100%;
    height: 100%;
  }

  .desktop-svg {
    display: block;
  }
  .mobile-svg {
    display: none;
  }

  .flow-dash {
    animation: dash-conduit 1.6s linear infinite;
  }

  @keyframes dash-conduit {
    to {
      stroke-dashoffset: -14;
    }
  }

  /* ================= (F) ACTIONS ROW ================= */
  .sheet-actions-row {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 4px;
  }

  .btn-primary-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: var(--cs-accent);
    color: var(--cs-on-accent);
    border: none;
    border-radius: 999px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    font-family: inherit;
    transition: transform 180ms ease, box-shadow 180ms ease;
  }

  .btn-primary-pill:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px var(--cs-glow);
  }

  .btn-ghost-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    background: var(--cs-pill);
    color: var(--cs-ink);
    border: 1px solid var(--cs-pill-border);
    border-radius: 999px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    font-family: inherit;
    transition: all 180ms ease;
  }

  .btn-ghost-pill:hover {
    background: var(--cs-pill-border);
  }

  .chevron-wrap {
    display: inline-flex;
    align-items: center;
    transition: transform 220ms ease;
  }

  .chevron-wrap.rotated {
    transform: rotate(180deg);
  }

  /* ================= (G) FOLDED DETAILS SECTION ================= */
  .folded-details-section {
    border-top: 1px solid var(--cs-pill-border);
    padding-top: 16px;
    margin-top: 4px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    animation: fade-details 200ms ease;
  }

  @keyframes fade-details {
    from {
      opacity: 0;
      transform: translateY(-4px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .details-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--cs-ink);
    margin: 0;
  }

  .details-body {
    font-size: 14px;
    line-height: 1.5;
    color: var(--cs-muted);
    margin: 0 0 8px 0;
  }

  .details-pills-row {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  .details-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: var(--cs-pill);
    border: 1px solid var(--cs-pill-border);
    border-radius: 999px;
    padding: 4px 12px;
    font-size: 13px;
    font-weight: 500;
    color: var(--cs-ink);
  }

  .details-pill-text {
    white-space: nowrap;
  }

  .details-body-text {
    font-size: 15px;
    line-height: 1.55;
    color: var(--cs-ink);
    margin: 0;
  }

  /* ================= RESPONSIVE DESIGN (< 720px) ================= */
  @media (max-width: 720px) {
    .center-sheet {
      padding: 18px 16px;
      border-radius: 22px;
      gap: 14px;
    }

    .sheet-headline {
      font-size: 20px;
    }

    .dag-graph-track {
      flex-direction: column;
      align-items: stretch;
      gap: 0;
    }

    .stage-column {
      width: 100%;
    }

    .dag-connector-col {
      width: 100%;
      height: 22px;
    }

    .desktop-svg {
      display: none;
    }
    .mobile-svg {
      display: block;
      height: 22px;
    }

    .sheet-actions-row {
      flex-direction: column;
      width: 100%;
    }

    .btn-primary-pill,
    .btn-ghost-pill {
      width: 100%;
    }
  }
</style>
