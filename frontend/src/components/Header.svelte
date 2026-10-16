<script>
  import { theme, toggleTheme, connectionStatus, activeView, activePersona, familyMembersList, alexaMicEnabled, toggleAlexaMic, toggleTracePanel, toolCallTraces } from '../lib/store.js';
  import { User, Users, Activity, Mic, MicOff, LayoutGrid, Settings, Sun, Moon } from '@lucide/svelte';
</script>

<header class="top-bar">
  <!-- Left: Glean Brand (Logomark + Wordmark) -->
  <button class="brand-btn" on:click={() => activeView.set('chat')} aria-label="Go to Glean home">
    <div class="logo-icon-wrap" aria-hidden="true">
      <svg class="glean-mark" width="34" height="34" viewBox="0 0 34 34" fill="none">
        <defs>
          <linearGradient id="glean-grad-light" x1="2" y1="2" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#4285F4" />
            <stop offset="100%" stop-color="#1A73E8" />
          </linearGradient>
          <linearGradient id="glean-grad-dark" x1="2" y1="2" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#00CAFF" />
            <stop offset="100%" stop-color="#2A6CFF" />
          </linearGradient>
        </defs>
        <!-- Rounded Squircle Badge -->
        <rect width="34" height="34" rx="10" class="tile-bg" />
        <!-- Layered Paperwork Sheets -->
        <rect x="8" y="7" width="13" height="17" rx="2.5" fill="white" opacity="0.45" />
        <rect x="12" y="10" width="14" height="17" rx="2.5" fill="white" />
        <!-- Document Content Lines -->
        <path d="M15 14.5H22.5" stroke="#1A73E8" class="doc-line" stroke-width="1.8" stroke-linecap="round" />
        <path d="M15 18H20.5" stroke="#1A73E8" class="doc-line" stroke-width="1.8" stroke-linecap="round" />
        <!-- Accent Sparkle -->
        <path d="M9 20C10.5 20 11.5 19 11.5 17.5C11.5 19 12.5 20 14 20C12.5 20 11.5 21 11.5 22.5C11.5 21 10.5 20 9 20Z" fill="white" opacity="0.9" />
      </svg>
    </div>
    <span class="logo-wordmark">GLEAN</span>
  </button>

  <!-- Center: Member / Persona Switcher -->
  <div class="center-group">
    <div class="persona-pill" title="Filter perspective by family member">
      {#if $activePersona === 'all'}
        <Users size={16} class="persona-icon" aria-hidden="true" />
      {:else}
        <User size={16} class="persona-icon" aria-hidden="true" />
      {/if}
      <label for="persona-select" class="persona-label">Who:</label>
      <select
        id="persona-select"
        class="persona-select"
        bind:value={$activePersona}
        aria-label="Active family member"
      >
        <option value="all">Whole Family</option>
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
  </div>

  <!-- Right: Status pills & Labeled Controls -->
  <div class="right-group">
    <!-- Server connection status -->
    <button
      class="status-pill {$connectionStatus === 'online' ? 'ok' : 'soon'}"
      on:click={toggleTracePanel}
      aria-label="Server status: {$connectionStatus}. Click for trace panel."
      title="Click to view MCP Traces"
    >
      <span class="status-dot"></span>
      <span class="status-text">
        {$connectionStatus === 'online' ? 'Live MCP HTTP' : 'Demo Mode'}
      </span>
    </button>

    <!-- Trace drawer toggle -->
    <button
      class="nav-btn"
      on:click={toggleTracePanel}
      aria-label="Open Live MCP protocol traces"
      title="Live MCP Protocol Trace Panel"
    >
      <Activity size={15} />
      <span class="nav-text">Traces</span>
      {#if $toolCallTraces.length > 0}
        <span class="trace-counter">{$toolCallTraces.length}</span>
      {/if}
    </button>

    <!-- Alexa Mic hardware toggle -->
    <button
      class="nav-btn mic-btn"
      class:muted={!$alexaMicEnabled}
      class:active-mic={$alexaMicEnabled}
      on:click={toggleAlexaMic}
      aria-label={$alexaMicEnabled ? 'Mute Alexa microphone' : 'Unmute Alexa microphone'}
      title={$alexaMicEnabled ? 'Alexa Mic is ON. Click to mute.' : 'Alexa Mic is MUTED. Click to unmute.'}
    >
      {#if $alexaMicEnabled}
        <Mic size={15} />
        <span class="nav-text">Mic ON</span>
      {:else}
        <MicOff size={15} />
        <span class="nav-text">Muted</span>
      {/if}
    </button>

    <!-- Dashboard View toggle -->
    <button
      class="nav-btn"
      class:active={$activeView === 'dashboard'}
      on:click={() => activeView.update(v => v === 'dashboard' ? 'chat' : 'dashboard')}
      aria-label="Toggle family dashboard"
      title="Family Admin Dashboard"
    >
      <LayoutGrid size={15} />
      <span class="nav-text">Dashboard</span>
    </button>

    <!-- Settings modal toggle -->
    <button
      class="nav-btn"
      class:active={$activeView === 'settings'}
      on:click={() => activeView.update(v => v === 'settings' ? 'chat' : 'settings')}
      aria-label="Settings"
      title="System Settings"
    >
      <Settings size={15} />
      <span class="nav-text">Settings</span>
    </button>

    <!-- Theme toggle (Dark / Light) -->
    <button
      class="icon-btn theme-toggle"
      on:click={toggleTheme}
      aria-label="Toggle theme between light and dark"
      title="Toggle Theme"
    >
      {#if $theme === 'dark'}
        <Sun size={16} />
      {:else}
        <Moon size={16} />
      {/if}
    </button>
  </div>
</header>

<style>
  .top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 60px;
    padding: 0 var(--sp-16);
    background: transparent;
    border-bottom: 1px solid var(--line-soft);
    position: sticky;
    top: 0;
    z-index: 40;
    backdrop-filter: blur(12px);
    transition: border-color var(--dur-base) var(--ease);
  }

  .brand-btn {
    display: flex;
    align-items: center;
    gap: var(--sp-12);
    border: none;
    background: transparent;
    cursor: pointer;
    padding: 0;
    text-decoration: none;
    transition: transform var(--dur-fast) var(--ease);
  }
  .brand-btn:hover {
    transform: scale(1.03);
  }

  .logo-icon-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(66, 133, 244, 0.25);
    flex-shrink: 0;
  }
  :global([data-theme="dark"]) .logo-icon-wrap {
    box-shadow: 0 2px 12px rgba(0, 202, 255, 0.25);
  }

  /* Logomark background per theme */
  .tile-bg {
    fill: url(#glean-grad-light);
  }
  :global([data-theme="dark"]) .tile-bg {
    fill: url(#glean-grad-dark);
  }

  :global([data-theme="dark"]) .doc-line {
    stroke: #2A6CFF;
  }

  /* Wordmark: 16px, weight 600, letter-spacing .2em */
  .logo-wordmark {
    font-family: var(--font-ui);
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 0.2em;
    transition: color var(--dur-base) var(--ease);
  }

  /* Light theme: Blue */
  :global([data-theme="light"]) .logo-wordmark {
    color: var(--accent);
  }

  /* Dark theme: White */
  :global([data-theme="dark"]) .logo-wordmark {
    color: #FFFFFF;
  }

  .center-group {
    display: flex;
    align-items: center;
  }

  .persona-pill {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-8);
    height: var(--btn-height);
    padding: 0 var(--sp-16);
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--r-pill);
    box-shadow: var(--shadow-card);
  }

  :global(.persona-icon) {
    color: var(--text-muted);
    flex-shrink: 0;
  }

  .persona-label {
    font-size: var(--fs-label);
    font-weight: 500;
    color: var(--text-muted);
  }

  .persona-select {
    border: none;
    background: transparent;
    font-family: var(--font-ui);
    font-size: var(--fs-small);
    font-weight: 500;
    color: var(--text);
    cursor: pointer;
    outline: none;
  }

  .right-group {
    display: flex;
    align-items: center;
    gap: var(--sp-8);
  }

  /* Status Pill */
  .status-pill {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-8);
    height: 32px;
    padding: 0 var(--sp-12);
    border-radius: var(--r-pill);
    border: 1px solid var(--line-soft);
    background: var(--surface);
    font-size: var(--fs-label);
    font-weight: 500;
    cursor: pointer;
    color: var(--text-soft);
    transition: all var(--dur-fast) var(--ease);
  }
  .status-pill:hover {
    border-color: var(--line);
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
  .status-pill.ok .status-dot {
    background: var(--ok);
  }
  .status-pill.soon .status-dot {
    background: var(--soon);
  }

  @media (max-width: 720px) {
    .status-text {
      display: none;
    }
    .status-pill {
      padding: 0 var(--sp-8);
    }
  }

  /* Navigation Labeled Buttons */
  .nav-btn {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-6);
    height: 34px;
    padding: 0 var(--sp-12);
    border-radius: var(--r-pill);
    border: 1px solid var(--line-soft);
    background: var(--surface);
    color: var(--text-soft);
    font-family: var(--font-ui);
    font-size: var(--fs-small);
    font-weight: 500;
    cursor: pointer;
    position: relative;
    transition: all var(--dur-fast) var(--ease);
    white-space: nowrap;
    text-decoration: none;
  }
  .nav-btn:hover {
    background: var(--surface-2);
    color: var(--text);
    border-color: var(--line);
  }
  .nav-btn.active {
    background: var(--surface-2);
    color: var(--accent);
    border-color: var(--accent);
    font-weight: 600;
  }
  .nav-btn.mic-btn.muted {
    background: var(--urgent-bg);
    color: var(--urgent-text);
    border-color: var(--urgent);
  }
  .nav-btn.mic-btn.active-mic {
    background: var(--ok-bg);
    color: var(--ok-text);
    border-color: var(--ok);
  }
  .nav-text {
    font-size: 13px;
    line-height: 1;
  }

  /* Theme Toggle Icon Button */
  .icon-btn {
    width: 34px;
    height: 34px;
    border-radius: var(--r-pill);
    border: 1px solid var(--line-soft);
    background: var(--surface);
    color: var(--text-muted);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all var(--dur-fast) var(--ease);
    flex-shrink: 0;
  }
  .icon-btn:hover {
    background: var(--surface-2);
    color: var(--text);
    border-color: var(--line);
  }

  .trace-counter {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 16px;
    height: 16px;
    padding: 0 4px;
    border-radius: var(--r-pill);
    background: var(--accent);
    color: var(--btn-primary-text);
    font-size: 10px;
    font-weight: 600;
    line-height: 1;
  }

  @media (max-width: 1024px) {
    .nav-text {
      display: none;
    }
    .nav-btn {
      padding: 0 var(--sp-8);
      width: 34px;
      justify-content: center;
    }
  }
</style>
