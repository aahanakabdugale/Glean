<script>
  import { theme, toggleTheme, connectionStatus, activeView, activePersona, familyMembersList } from '../lib/store.js';
</script>

<header class="header">
  <!-- Glean brand: logomark + wordmark + tagline -->
  <button
    class="brand"
    on:click={() => activeView.set('chat')}
    aria-label="Go to Glean home"
  >
    <!-- Logomark: five dots forming a G -->
    <svg class="logo-mark" width="36" height="36" viewBox="0 0 36 36" fill="none" aria-hidden="true">
      <rect width="36" height="36" rx="10" fill="var(--violet)"/>
      <!-- Dots arcing into a G shape -->
      <circle cx="11" cy="9"  r="2.4" fill="white" opacity="0.55"/>
      <circle cx="18" cy="7"  r="2.4" fill="white" opacity="0.75"/>
      <circle cx="25" cy="9"  r="2.4" fill="white"/>
      <circle cx="27" cy="18" r="2.4" fill="white"/>
      <circle cx="27" cy="25" r="2.4" fill="var(--teal)"/>
      <circle cx="21" cy="27" r="2.4" fill="var(--teal)" opacity="0.85"/>
    </svg>

    <div class="brand-text">
      <span class="wordmark">Glean</span>
      <span class="tagline">Your family's paperwork, gathered.</span>
    </div>
  </button>

  <!-- "Who am I?" Persona Selector Dropdown -->
  <div class="persona-selector" title="Select active family member for personalized briefing">
    <label for="persona-select" class="persona-label">
      <span class="persona-avatar" aria-hidden="true">
        {#if $activePersona === 'all'}
          👨‍👩‍👧‍👦
        {:else if $activePersona.toLowerCase() === 'chandler' || $activePersona.toLowerCase().includes('grandpa')}
          👴
        {:else if $activePersona.toLowerCase() === 'amy' || $activePersona.toLowerCase().includes('grandma')}
          👵
        {:else if $activePersona.toLowerCase() === 'justin' || $activePersona.toLowerCase().includes('dad')}
          👨
        {:else if $activePersona.toLowerCase() === 'riley' || $activePersona.toLowerCase().includes('mom')}
          👩
        {:else if $activePersona.toLowerCase() === 'jace'}
          👦
        {:else if $activePersona.toLowerCase() === 'gwen'}
          👧
        {:else}
          👤
        {/if}
      </span>
      <span class="persona-tag">Who am I:</span>
    </label>
    <select
      id="persona-select"
      class="persona-select"
      bind:value={$activePersona}
      aria-label="Select persona: Who am I?"
    >
      <option value="all">Whole Family (Overview)</option>
      <option value="Chandler">Chandler (Grandfather / 70+)</option>
      <option value="Amy">Amy (Grandmother / 70+)</option>
      <option value="Justin">Justin (Father / 50s)</option>
      <option value="Riley">Riley (Mother / 50s)</option>
      <option value="Jace">Jace (Son / Admin)</option>
      <option value="Gwen">Gwen (Daughter / Admin)</option>
      {#each $familyMembersList as m}
        {#if !['chandler', 'amy', 'justin', 'riley', 'jace', 'gwen'].includes(m.name.toLowerCase())}
          <option value={m.name}>{m.name} ({m.relation})</option>
        {/if}
      {/each}
    </select>
  </div>

  <!-- Right-hand controls -->
  <div class="controls">
    <!-- Connection status badge -->
    <div
      class="status-badge"
      class:online={$connectionStatus === 'online'}
      class:offline={$connectionStatus === 'offline'}
      aria-live="polite"
      aria-label="Server connection status: {$connectionStatus === 'online' ? 'Connected' : $connectionStatus === 'offline' ? 'Demo mode' : 'Unknown'}"
    >
      <span class="status-dot" aria-hidden="true"></span>
      <span class="status-text">
        {#if $connectionStatus === 'online'}
          Live MCP
        {:else if $connectionStatus === 'offline'}
          Demo mode
        {:else}
          Connecting…
        {/if}
      </span>
    </div>

    <!-- Dashboard view toggle -->
    <button
      class="icon-btn"
      class:active={$activeView === 'dashboard'}
      on:click={() => activeView.set($activeView === 'dashboard' ? 'chat' : 'dashboard')}
      aria-label="Toggle family dashboard"
      title="Family Dashboard"
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <rect x="3" y="3" width="7" height="7" rx="1"/>
        <rect x="14" y="3" width="7" height="7" rx="1"/>
        <rect x="3" y="14" width="7" height="7" rx="1"/>
        <rect x="14" y="14" width="7" height="7" rx="1"/>
      </svg>
    </button>

    <!-- Settings -->
    <button
      class="icon-btn"
      class:active={$activeView === 'settings'}
      on:click={() => activeView.set($activeView === 'settings' ? 'chat' : 'settings')}
      aria-label="Open settings"
      title="Settings"
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
      </svg>
    </button>

    <!-- Theme toggle -->
    <button
      class="icon-btn theme-btn"
      on:click={toggleTheme}
      aria-label="Switch to {$theme === 'light' ? 'dark' : 'light'} theme"
      title="Toggle theme"
    >
      {#if $theme === 'light'}
        <!-- Moon icon -->
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      {:else}
        <!-- Sun icon -->
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <circle cx="12" cy="12" r="5"/>
          <line x1="12" y1="1" x2="12" y2="3"/>
          <line x1="12" y1="21" x2="12" y2="23"/>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
          <line x1="1" y1="12" x2="3" y2="12"/>
          <line x1="21" y1="12" x2="23" y2="12"/>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
      {/if}
    </button>
  </div>
</header>

<style>
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--sp-3) var(--sp-5);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-xl);
    box-shadow: var(--shadow);
    gap: var(--sp-4);
    flex-shrink: 0;
    transition: var(--theme-transition);
  }

  .brand {
    display: flex;
    align-items: center;
    gap: var(--sp-3);
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    color: inherit;
    text-align: left;
  }

  .brand:hover .wordmark {
    color: var(--violet);
  }

  .logo-mark {
    flex-shrink: 0;
    transition: transform var(--t-base) var(--ease-spring);
  }

  .brand:hover .logo-mark {
    transform: scale(1.08) rotate(-3deg);
  }

  .brand-text {
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .wordmark {
    font-family: var(--font-display);
    font-size: 1.25rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--text);
    transition: color var(--t-base) ease;
    line-height: 1.1;
  }

  .tagline {
    font-size: 0.7rem;
    color: var(--text-muted);
    font-weight: 400;
    letter-spacing: 0.01em;
    white-space: nowrap;
  }

  /* Persona Selector ("Who am I?") */
  .persona-selector {
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: var(--r-full);
    padding: 3px 10px 3px 10px;
    transition: var(--theme-transition);
  }

  .persona-selector:hover,
  .persona-selector:focus-within {
    border-color: var(--violet);
    background: var(--violet-bg);
  }

  .persona-label {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-muted);
    cursor: pointer;
    user-select: none;
  }

  .persona-avatar {
    font-size: 0.95rem;
    line-height: 1;
  }

  .persona-tag {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-muted);
  }

  .persona-select {
    background: transparent;
    border: none;
    color: var(--text);
    font-family: var(--font-body);
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    outline: none;
    padding: 2px 2px;
  }

  .persona-select option {
    background: var(--surface);
    color: var(--text);
  }

  .controls {
    display: flex;
    align-items: center;
    gap: var(--sp-2);
    flex-shrink: 0;
  }

  /* Status badge */
  .status-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 5px var(--sp-3);
    border-radius: var(--r-full);
    font-size: 0.72rem;
    font-weight: 600;
    background: var(--surface-2);
    border: 1px solid var(--border);
    color: var(--text-muted);
    transition: var(--theme-transition);
    white-space: nowrap;
  }

  .status-badge.online {
    background: var(--teal-bg);
    border-color: var(--teal);
    color: var(--teal-text);
  }

  .status-badge.offline {
    background: var(--amber-bg);
    border-color: var(--amber);
    color: var(--amber-text);
  }

  .status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
    flex-shrink: 0;
  }

  .status-badge.online .status-dot {
    animation: pulse-dot 2s ease-in-out infinite;
  }

  @keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  /* Icon buttons */
  .icon-btn {
    width: 34px;
    height: 34px;
    border-radius: var(--r-md);
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    display: grid;
    place-items: center;
    transition: all var(--t-fast) ease;
    flex-shrink: 0;
  }

  .icon-btn:hover {
    background: var(--surface-2);
    color: var(--text);
    border-color: var(--border-strong);
  }

  .icon-btn.active {
    background: var(--violet-bg);
    color: var(--violet);
    border-color: var(--violet);
  }

  /* Hide tagline on very small screens */
  @media (max-width: 480px) {
    .tagline { display: none; }
    .status-text { display: none; }
    .status-badge { padding: 5px 8px; }
  }
</style>
