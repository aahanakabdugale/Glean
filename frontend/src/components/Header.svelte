<script>
  import {
    theme,
    toggleTheme,
    connectionStatus,
    activeView,
    activePersona,
    familyMembersList,
    alexaMicEnabled,
    toggleAlexaMic,
    toggleTracePanel,
    toolCallTraces,
    settings
  } from '../lib/store.js';
  import {
    User,
    ChevronDown,
    Activity,
    LayoutGrid,
    SlidersHorizontal,
    Radio,
    Mic,
    MicOff,
    Sun,
    Moon,
    X,
    CheckCircle2,
    AlertCircle,
    RotateCw
  } from '@lucide/svelte';
  import { testConnection } from '../lib/mcp.js';

  let showUserMenu = false;
  let showStatusPopover = false;
  let testingConnection = false;
  let testResult = '';

  // Persona helper data mapping
  const personaRoles = {
    all: 'Whole Family',
    Chandler: 'Grandfather',
    Amy: 'Grandmother',
    Justin: 'Father',
    Riley: 'Mother',
    Jace: 'Son / Admin',
    Gwen: 'Daughter / Admin'
  };

  $: currentRole = personaRoles[$activePersona] || (
    $familyMembersList.find(m => m.name.toLowerCase() === ($activePersona || '').toLowerCase())?.relation || 'Member'
  );

  $: currentFirstName = $activePersona === 'all' ? 'All' : ($activePersona || 'User');

  async function runPingTest() {
    testingConnection = true;
    testResult = '';
    try {
      const ok = await testConnection();
      testResult = ok ? 'Connected successfully (200 OK)' : 'Could not reach server';
    } catch (e) {
      testResult = 'Connection test failed';
    } finally {
      testingConnection = false;
    }
  }

  function handleKeydown(e) {
    if (e.key === 'Escape') {
      if (showUserMenu) showUserMenu = false;
      if (showStatusPopover) showStatusPopover = false;
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<header class="top-bar">
  <!-- LEFT COLUMN: Brand Orb + Wordmark + User Switcher -->
  <div class="col-left">
    <button
      class="brand-btn"
      on:click={() => activeView.set('chat')}
      aria-label="Glean home"
    >
      <div class="logo-orb" aria-hidden="true"></div>
      <span class="logo-wordmark">glean</span>
    </button>

    <!-- User Switcher Dropdown Button -->
    <div class="user-switcher-wrap">
      <button
        type="button"
        class="user-switcher-btn"
        class:menu-open={showUserMenu}
        on:click={() => {
          showUserMenu = !showUserMenu;
          if (showStatusPopover) showStatusPopover = false;
        }}
        aria-haspopup="listbox"
        aria-expanded={showUserMenu}
        aria-label="Switch active family perspective: current user {currentFirstName}, role {currentRole}"
      >
        <span class="user-icon-wrap" aria-hidden="true">
          <User size={16} strokeWidth={1.75} />
        </span>
        <span class="user-name">{currentFirstName}</span>
        <span class="user-role">{currentRole}</span>
        <span class="chevron-wrap" class:open={showUserMenu} aria-hidden="true">
          <ChevronDown size={14} strokeWidth={1.75} />
        </span>
      </button>

      {#if showUserMenu}
        <button
          type="button"
          class="dropdown-backdrop"
          on:click={() => showUserMenu = false}
          aria-label="Close user menu"
          tabindex="-1"
        ></button>

        <ul class="user-dropdown-menu" role="listbox" aria-label="Family members">
          <li role="presentation">
            <button
              type="button"
              class="user-option-btn"
              class:selected={$activePersona === 'all'}
              role="option"
              aria-selected={$activePersona === 'all'}
              on:click={() => { $activePersona = 'all'; showUserMenu = false; }}
            >
              <span class="opt-name">Whole Family</span>
              <span class="opt-role">Overview</span>
            </button>
          </li>
          <li role="presentation">
            <button
              type="button"
              class="user-option-btn"
              class:selected={$activePersona === 'Jace'}
              role="option"
              aria-selected={$activePersona === 'Jace'}
              on:click={() => { $activePersona = 'Jace'; showUserMenu = false; }}
            >
              <span class="opt-name">Jace</span>
              <span class="opt-role">Son / Admin</span>
            </button>
          </li>
          <li role="presentation">
            <button
              type="button"
              class="user-option-btn"
              class:selected={$activePersona === 'Gwen'}
              role="option"
              aria-selected={$activePersona === 'Gwen'}
              on:click={() => { $activePersona = 'Gwen'; showUserMenu = false; }}
            >
              <span class="opt-name">Gwen</span>
              <span class="opt-role">Daughter / Admin</span>
            </button>
          </li>
          <li role="presentation">
            <button
              type="button"
              class="user-option-btn"
              class:selected={$activePersona === 'Chandler'}
              role="option"
              aria-selected={$activePersona === 'Chandler'}
              on:click={() => { $activePersona = 'Chandler'; showUserMenu = false; }}
            >
              <span class="opt-name">Chandler</span>
              <span class="opt-role">Grandfather (70+)</span>
            </button>
          </li>
          <li role="presentation">
            <button
              type="button"
              class="user-option-btn"
              class:selected={$activePersona === 'Amy'}
              role="option"
              aria-selected={$activePersona === 'Amy'}
              on:click={() => { $activePersona = 'Amy'; showUserMenu = false; }}
            >
              <span class="opt-name">Amy</span>
              <span class="opt-role">Grandmother (70+)</span>
            </button>
          </li>
          <li role="presentation">
            <button
              type="button"
              class="user-option-btn"
              class:selected={$activePersona === 'Justin'}
              role="option"
              aria-selected={$activePersona === 'Justin'}
              on:click={() => { $activePersona = 'Justin'; showUserMenu = false; }}
            >
              <span class="opt-name">Justin</span>
              <span class="opt-role">Father (50s)</span>
            </button>
          </li>
          <li role="presentation">
            <button
              type="button"
              class="user-option-btn"
              class:selected={$activePersona === 'Riley'}
              role="option"
              aria-selected={$activePersona === 'Riley'}
              on:click={() => { $activePersona = 'Riley'; showUserMenu = false; }}
            >
              <span class="opt-name">Riley</span>
              <span class="opt-role">Mother (50s)</span>
            </button>
          </li>
          {#each $familyMembersList as m}
            {#if !['chandler', 'amy', 'justin', 'riley', 'jace', 'gwen'].includes(m.name.toLowerCase())}
              <li role="presentation">
                <button
                  type="button"
                  class="user-option-btn"
                  class:selected={$activePersona === m.name}
                  role="option"
                  aria-selected={$activePersona === m.name}
                  on:click={() => { $activePersona = m.name; showUserMenu = false; }}
                >
                  <span class="opt-name">{m.name}</span>
                  <span class="opt-role">{m.relation || 'Member'}</span>
                </button>
              </li>
            {/if}
          {/each}
        </ul>
      {/if}
    </div>
  </div>

  <!-- CENTER COLUMN: Segmented Navigation Control -->
  <nav class="col-center" aria-label="Main application sections">
    <div class="segmented-nav" role="tablist">
      <!-- 1. Dashboard -->
      <button
        type="button"
        class="seg-item"
        class:active={$activeView === 'dashboard'}
        role="tab"
        aria-selected={$activeView === 'dashboard'}
        aria-current={$activeView === 'dashboard' ? 'page' : undefined}
        on:click={() => activeView.update(v => v === 'dashboard' ? 'chat' : 'dashboard')}
      >
        <span class="seg-icon" aria-hidden="true">
          <LayoutGrid size={16} strokeWidth={1.75} />
        </span>
        <span class="seg-label">Dashboard</span>
      </button>

      <!-- 2. Traces -->
      <button
        type="button"
        class="seg-item"
        aria-label="Open Live MCP protocol traces drawer ({$toolCallTraces.length} recorded)"
        on:click={toggleTracePanel}
      >
        <span class="seg-icon" aria-hidden="true">
          <Activity size={16} strokeWidth={1.75} />
        </span>
        <span class="seg-label">Traces</span>
        {#if $toolCallTraces.length > 0}
          <span class="trace-badge" aria-label="{$toolCallTraces.length} traces">
            {$toolCallTraces.length}
          </span>
        {/if}
      </button>

      <!-- 3. Settings -->
      <button
        type="button"
        class="seg-item"
        class:active={$activeView === 'settings'}
        role="tab"
        aria-selected={$activeView === 'settings'}
        aria-current={$activeView === 'settings' ? 'page' : undefined}
        on:click={() => activeView.update(v => v === 'settings' ? 'chat' : 'settings')}
      >
        <span class="seg-icon" aria-hidden="true">
          <SlidersHorizontal size={16} strokeWidth={1.75} />
        </span>
        <span class="seg-label">Settings</span>
      </button>
    </div>
  </nav>

  <!-- RIGHT COLUMN: Live Status + Mic Toggle + Theme Toggle -->
  <div class="col-right">
    <!-- Live Status Indicator & Popover Trigger -->
    <div class="live-status-wrap">
      <button
        type="button"
        class="live-status-btn status-{$connectionStatus === 'online' ? 'connected' : ($connectionStatus === 'connecting' ? 'connecting' : 'disconnected')}"
        class:popover-open={showStatusPopover}
        on:click={() => {
          showStatusPopover = !showStatusPopover;
          if (showUserMenu) showUserMenu = false;
        }}
        aria-label="Server status: {$connectionStatus === 'online' ? 'Live Connected' : ($connectionStatus === 'connecting' ? 'Connecting' : 'Disconnected')}. Click for connection details."
        aria-expanded={showStatusPopover}
      >
        <span class="status-icon-wrap" aria-hidden="true">
          <Radio size={16} strokeWidth={1.75} />
        </span>
        <span class="live-label">Live</span>
      </button>

      {#if showStatusPopover}
        <button
          type="button"
          class="dropdown-backdrop"
          on:click={() => showStatusPopover = false}
          aria-label="Close server status details"
          tabindex="-1"
        ></button>

        <div class="status-popover" role="dialog" aria-label="MCP Server Connection Details">
          <div class="popover-header">
            <div class="popover-title-row">
              <span class="status-dot-indicator status-{$connectionStatus === 'online' ? 'connected' : ($connectionStatus === 'connecting' ? 'connecting' : 'disconnected')}" aria-hidden="true"></span>
              <span class="popover-title">MCP Server Connection</span>
            </div>
            <button
              type="button"
              class="popover-close-btn"
              on:click={() => showStatusPopover = false}
              aria-label="Close"
            >
              <X size={14} strokeWidth={1.75} />
            </button>
          </div>

          <div class="popover-body">
            <div class="popover-badge-row">
              <span class="popover-status-badge status-{$connectionStatus === 'online' ? 'connected' : ($connectionStatus === 'connecting' ? 'connecting' : 'disconnected')}">
                {$connectionStatus === 'online' ? '● Live Streamable HTTP' : ($connectionStatus === 'connecting' ? '● Connecting...' : '● Disconnected / Demo Mode')}
              </span>
              {#if $connectionStatus === 'online'}
                <span class="popover-stat-tag">Active</span>
              {/if}
            </div>

            <div class="popover-info-grid">
              <div class="info-item">
                <span class="info-label">Endpoint URL</span>
                <span class="info-val mono" title={$settings.serverUrl}>
                  {$settings.serverUrl || 'http://127.0.0.1:8000/mcp'}
                </span>
              </div>
              <div class="info-item">
                <span class="info-label">Transport</span>
                <span class="info-val">Streamable HTTP (JSON-RPC 2.0)</span>
              </div>
              <div class="info-item">
                <span class="info-label">MCP Protocol</span>
                <span class="info-val">2024-11-05 Specification</span>
              </div>
              <div class="info-item">
                <span class="info-label">Registered Tools</span>
                <span class="info-val">11 Tools (Family, Schemes, Vault)</span>
              </div>
              <div class="info-item">
                <span class="info-label">SSE Push Broker</span>
                <span class="info-val">/api/ambient/events (Live)</span>
              </div>
            </div>

            {#if testResult}
              <div class="test-feedback" class:ok={testResult.includes('success')}>
                {#if testResult.includes('success')}
                  <CheckCircle2 size={14} strokeWidth={1.75} />
                {:else}
                  <AlertCircle size={14} strokeWidth={1.75} />
                {/if}
                <span>{testResult}</span>
              </div>
            {/if}
          </div>

          <div class="popover-footer">
            <button
              type="button"
              class="popover-action-btn secondary"
              on:click={runPingTest}
              disabled={testingConnection}
            >
              <RotateCw size={13} strokeWidth={1.75} class={testingConnection ? 'spin' : ''} />
              <span>{testingConnection ? 'Pinging…' : 'Ping Server'}</span>
            </button>

            <button
              type="button"
              class="popover-action-btn primary"
              on:click={() => {
                showStatusPopover = false;
                activeView.set('settings');
              }}
            >
              <SlidersHorizontal size={13} strokeWidth={1.75} />
              <span>Server Settings</span>
            </button>
          </div>
        </div>
      {/if}
    </div>

    <!-- Mute / Unmute Button (38x38) -->
    <button
      type="button"
      class="icon-ctrl-btn mute-btn"
      class:muted={!$alexaMicEnabled}
      on:click={toggleAlexaMic}
      aria-label={$alexaMicEnabled ? 'Mute' : 'Unmute'}
      title={$alexaMicEnabled ? 'Microphone is active. Click to mute.' : 'Microphone is muted. Click to unmute.'}
    >
      {#if $alexaMicEnabled}
        <Mic size={18} strokeWidth={1.75} aria-hidden="true" />
      {:else}
        <MicOff size={18} strokeWidth={1.75} aria-hidden="true" />
      {/if}
    </button>

    <!-- Theme Toggle (38x38) -->
    <button
      type="button"
      class="icon-ctrl-btn theme-btn"
      on:click={toggleTheme}
      aria-label={$theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
      title={$theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
    >
      {#if $theme === 'dark'}
        <Sun size={18} strokeWidth={1.75} aria-hidden="true" />
      {:else}
        <Moon size={18} strokeWidth={1.75} aria-hidden="true" />
      {/if}
    </button>
  </div>
</header>

<style>
  /* ================= TOP NAVIGATION BAR ================= */
  .top-bar {
    width: 100%;
    height: 72px;
    background: var(--bar-bg);
    border-bottom: 1px solid var(--bar-border);
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    padding: 0 20px;
    position: relative;
    z-index: 40;
    box-sizing: border-box;
    font-family: 'Outfit', 'Outfit Variable', system-ui, -apple-system, sans-serif;
    font-size: 13px;
    font-weight: 500;
    color: var(--bar-text, var(--text));
    transition: background-color 150ms ease, border-color 150ms ease, color 150ms ease;
  }

  @media (prefers-reduced-motion: reduce) {
    .top-bar,
    .top-bar * {
      transition: none !important;
      animation: none !important;
    }
  }

  /* ---------------- COLUMN 1: LEFT ---------------- */
  .col-left {
    display: flex;
    align-items: center;
    gap: 16px;
    min-width: 0;
  }

  /* Brand Orb + Wordmark */
  .brand-btn {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    border: none;
    background: transparent;
    cursor: pointer;
    padding: 4px 6px;
    border-radius: 8px;
    text-decoration: none;
    flex-shrink: 0;
    transition: opacity 150ms ease, transform 150ms ease;
  }
  .brand-btn:hover {
    opacity: 0.92;
    transform: translateY(-0.5px);
  }
  .brand-btn:focus-visible {
    outline: 2px solid var(--focus);
    outline-offset: 2px;
  }

  /* 28px Circle Logo Orb */
  .logo-orb {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 30%, #9fd0ff 0%, #3b6ff5 50%, #1a2f8a 100%);
    box-shadow: 0 0 0 4px var(--logo-glow);
    flex-shrink: 0;
  }

  .logo-wordmark {
    font-family: 'Outfit', 'Outfit Variable', system-ui, -apple-system, sans-serif;
    font-size: 20px;
    font-weight: 600;
    color: var(--bar-text, var(--text));
    letter-spacing: -0.01em;
    line-height: 1;
  }

  /* User Switcher */
  .user-switcher-wrap {
    position: relative;
    display: inline-flex;
  }

  .user-switcher-btn {
    height: 38px;
    min-width: 38px;
    padding: 0 12px;
    border-radius: 12px;
    border: 1px solid var(--ctrl-border);
    background: transparent;
    color: var(--ctrl-text);
    display: inline-flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-family: inherit;
    font-size: 13px;
    font-weight: 500;
    line-height: 1;
    transition: background-color 150ms ease, border-color 150ms ease, color 150ms ease;
    white-space: nowrap;
  }
  .user-switcher-btn:hover {
    background: var(--ctrl-hover-bg);
  }
  .user-switcher-btn:active {
    filter: brightness(0.92);
  }
  .user-switcher-btn:focus-visible {
    outline: 2px solid var(--focus);
    outline-offset: 2px;
  }

  .user-icon-wrap {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: var(--ctrl-text);
  }

  .user-name {
    color: var(--bar-text, var(--text));
    font-weight: 500;
  }

  .user-role {
    color: var(--bar-text-muted, var(--text-muted));
    font-size: 12px;
    font-weight: 400;
  }

  .chevron-wrap {
    display: inline-flex;
    align-items: center;
    color: var(--bar-text-muted, var(--text-muted));
    transition: transform 150ms ease;
  }
  .chevron-wrap.open {
    transform: rotate(180deg);
  }

  /* Dropdown Popover Backdrop */
  .dropdown-backdrop {
    position: fixed;
    inset: 0;
    z-index: 85;
    background: transparent;
    border: none;
    cursor: default;
    padding: 0;
    margin: 0;
  }

  .user-dropdown-menu {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    min-width: 200px;
    background: var(--bar-bg);
    border: 1px solid var(--bar-border);
    border-radius: 14px;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
    z-index: 90;
    padding: 6px;
    margin: 0;
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  :global([data-theme="light"]) .user-dropdown-menu {
    box-shadow: 0 8px 24px rgba(11, 18, 32, 0.12);
  }

  .user-option-btn {
    width: 100%;
    border: none;
    background: transparent;
    border-radius: 8px;
    padding: 8px 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    cursor: pointer;
    font-family: inherit;
    font-size: 13px;
    color: var(--bar-text, var(--text));
    text-align: left;
    transition: background-color 150ms ease;
  }
  .user-option-btn:hover {
    background: var(--ctrl-hover-bg);
  }
  .user-option-btn.selected {
    background: var(--seg-active-bg);
    color: var(--seg-active-text);
    font-weight: 600;
  }
  .opt-name {
    font-weight: 500;
  }
  .opt-role {
    font-size: 11px;
    color: var(--bar-text-muted, var(--text-muted));
  }
  .user-option-btn.selected .opt-role {
    color: var(--seg-active-text);
    opacity: 0.8;
  }

  /* ---------------- COLUMN 2: CENTER (SEGMENTED NAV) ---------------- */
  .col-center {
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .segmented-nav {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 4px;
    border-radius: 14px;
    background: var(--seg-bg);
    border: 1px solid var(--seg-border);
    box-sizing: border-box;
    transition: background-color 150ms ease, border-color 150ms ease;
  }

  .seg-item {
    height: 34px;
    padding: 0 16px;
    border-radius: 10px;
    border: none;
    background: transparent;
    color: var(--nav-text);
    display: inline-flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-family: inherit;
    font-size: 13px;
    font-weight: 500;
    line-height: 1;
    position: relative;
    white-space: nowrap;
    text-decoration: none;
    transition: background-color 150ms ease, color 150ms ease, box-shadow 150ms ease;
  }
  .seg-item:hover {
    color: var(--bar-text, var(--text));
    background: var(--ctrl-hover-bg);
  }
  .seg-item:active {
    filter: brightness(0.92);
  }
  .seg-item:focus-visible {
    outline: 2px solid var(--focus);
    outline-offset: 2px;
  }

  .seg-item.active {
    background: var(--seg-active-bg);
    color: var(--seg-active-text);
    box-shadow: inset 0 0 0 1px var(--seg-active-ring);
  }

  :global([data-theme="light"]) .seg-item.active {
    box-shadow: inset 0 0 0 1px var(--seg-active-ring), 0 1px 2px rgba(11, 18, 32, 0.12);
  }

  .seg-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .seg-label {
    line-height: 1;
  }

  /* Traces Count Badge */
  .trace-badge {
    min-width: 18px;
    height: 18px;
    padding: 0 5px;
    border-radius: 999px;
    background: var(--badge-bg);
    color: var(--badge-text);
    font-size: 11px;
    font-weight: 700;
    line-height: 1;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    letter-spacing: -0.02em;
    margin-left: -2px;
  }

  /* ---------------- COLUMN 3: RIGHT CLUSTER ---------------- */
  .col-right {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 12px;
  }

  /* Live Status Button */
  .live-status-wrap {
    position: relative;
    display: inline-flex;
  }

  .live-status-btn {
    height: 38px;
    padding: 0 12px;
    border-radius: 12px;
    border: 1px solid var(--ctrl-border);
    background: transparent;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-family: inherit;
    font-size: 13px;
    font-weight: 500;
    line-height: 1;
    transition: background-color 150ms ease, border-color 150ms ease, color 150ms ease;
  }
  .live-status-btn:hover {
    background: var(--ctrl-hover-bg);
  }
  .live-status-btn:focus-visible {
    outline: 2px solid var(--focus);
    outline-offset: 2px;
  }

  .live-status-btn.status-connected {
    color: var(--live);
  }
  .live-status-btn.status-connecting {
    color: var(--warn);
  }
  .live-status-btn.status-disconnected {
    color: var(--danger);
  }

  .status-icon-wrap {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .live-label {
    font-weight: 600;
  }

  /* Icon-Only Buttons (38x38) */
  .icon-ctrl-btn {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    border: 1px solid var(--ctrl-border);
    background: transparent;
    color: var(--ctrl-text);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
    padding: 0;
    transition: background-color 150ms ease, border-color 150ms ease, color 150ms ease;
  }
  .icon-ctrl-btn:hover {
    background: var(--ctrl-hover-bg);
    color: var(--bar-text, var(--text));
  }
  .icon-ctrl-btn:active {
    filter: brightness(0.92);
  }
  .icon-ctrl-btn:focus-visible {
    outline: 2px solid var(--focus);
    outline-offset: 2px;
  }

  /* Mute Active State (Danger tokens) */
  .mute-btn.muted {
    background: var(--danger-bg);
    border-color: var(--danger-border);
    color: var(--danger);
  }
  .mute-btn.muted:hover {
    background: var(--danger-bg);
    filter: brightness(1.12);
  }

  /* ---------------- STATUS POPOVER ---------------- */
  .status-popover {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    width: 320px;
    background: var(--bar-bg);
    border: 1px solid var(--bar-border);
    border-radius: 14px;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45);
    z-index: 100;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: popoverFadeIn 140ms ease-out;
  }

  :global([data-theme="light"]) .status-popover {
    box-shadow: 0 10px 28px rgba(11, 18, 32, 0.12);
  }

  @keyframes popoverFadeIn {
    from {
      opacity: 0;
      transform: translateY(-6px) scale(0.98);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  .popover-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 14px;
    border-bottom: 1px solid var(--bar-border);
    background: var(--seg-bg);
  }

  .popover-title-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .status-dot-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
  .status-dot-indicator.status-connected {
    background: var(--live);
    box-shadow: 0 0 6px var(--live);
  }
  .status-dot-indicator.status-connecting {
    background: var(--warn);
    box-shadow: 0 0 6px var(--warn);
  }
  .status-dot-indicator.status-disconnected {
    background: var(--danger);
    box-shadow: 0 0 6px var(--danger);
  }

  .popover-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--bar-text, var(--text));
  }

  .popover-close-btn {
    border: none;
    background: transparent;
    color: var(--bar-text-muted, var(--text-muted));
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px;
    border-radius: 4px;
    transition: color 150ms ease, background-color 150ms ease;
  }
  .popover-close-btn:hover {
    color: var(--bar-text, var(--text));
    background: var(--ctrl-hover-bg);
  }

  .popover-body {
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .popover-badge-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .popover-status-badge {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .popover-status-badge.status-connected {
    background: rgba(110, 231, 183, 0.14);
    color: var(--live);
    border: 1px solid var(--live);
  }
  .popover-status-badge.status-connecting {
    background: rgba(251, 191, 36, 0.14);
    color: var(--warn);
    border: 1px solid var(--warn);
  }
  .popover-status-badge.status-disconnected {
    background: var(--danger-bg);
    color: var(--danger);
    border: 1px solid var(--danger-border);
  }

  .popover-stat-tag {
    font-size: 11px;
    color: var(--bar-text-muted, var(--text-muted));
    font-weight: 500;
  }

  .popover-info-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: var(--seg-bg);
    border: 1px solid var(--bar-border);
    border-radius: 8px;
    padding: 10px 12px;
  }

  .info-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .info-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--bar-text-muted, var(--text-muted));
  }

  .info-val {
    font-size: 12px;
    font-weight: 500;
    color: var(--bar-text, var(--text));
  }
  .info-val.mono {
    font-family: var(--font-mono);
    font-size: 11px;
    word-break: break-all;
  }

  .test-feedback {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 500;
    padding: 6px 10px;
    border-radius: 6px;
    background: rgba(251, 191, 36, 0.14);
    color: var(--warn);
  }
  .test-feedback.ok {
    background: rgba(110, 231, 183, 0.14);
    color: var(--live);
  }

  .popover-footer {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-top: 1px solid var(--bar-border);
    background: var(--seg-bg);
  }

  .popover-action-btn {
    flex: 1;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    height: 32px;
    padding: 0 10px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
    font-family: inherit;
    cursor: pointer;
    transition: all 150ms ease;
  }
  .popover-action-btn.secondary {
    border: 1px solid var(--ctrl-border);
    background: var(--bar-bg);
    color: var(--ctrl-text);
  }
  .popover-action-btn.secondary:hover {
    background: var(--ctrl-hover-bg);
  }
  .popover-action-btn.primary {
    border: 1px solid var(--seg-active-ring);
    background: var(--seg-active-ring);
    color: #ffffff;
  }
  .popover-action-btn.primary:hover {
    filter: brightness(1.1);
  }

  :global(.spin) {
    animation: spin 1s linear infinite;
  }
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  /* ---------------- RESPONSIVE BREAKPOINT (<900px) ---------------- */
  @media (max-width: 900px) {
    .user-role {
      display: none;
    }
    .seg-label {
      display: none;
    }
    .seg-item {
      padding: 0 10px;
    }
    .live-label {
      display: none;
    }
  }

  @media (max-width: 600px) {
    .top-bar {
      padding: 0 12px;
    }
    .user-name {
      display: none;
    }
    .user-switcher-btn {
      padding: 0 8px;
    }
    .brand-btn .logo-wordmark {
      display: none;
    }
  }
</style>
