<script>
  import { onMount } from 'svelte';
  import {
    theme,
    toggleTheme,
    connectionStatus,
    activeView,
    activePersona,
    activeJurisdiction,
    familyMembersList,
    toolCallTraces,
    alexaMicEnabled,
    toggleAlexaMic,
    settings
  } from '../lib/store.js';
  import {
    LayoutGrid,
    ClipboardCheck,
    Activity,
    SlidersHorizontal,
    Mic,
    MicOff,
    User,
    ChevronDown,
    Radio,
    Sun,
    Moon,
    X,
    CheckCircle2,
    AlertCircle,
    RotateCw,
    Globe
  } from '@lucide/svelte';
  import { testConnection } from '../lib/mcp.js';

  let showUserMenu = false;
  let showRegionMenu = false;
  let showStatusPopover = false;
  let testingConnection = false;
  let testResult = '';

  const regionLabels = {
    all: 'All Regions',
    IN: 'India',
    US: 'United States'
  };

  $: activeRegionLabel = regionLabels[$activeJurisdiction] || 'All Regions';

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

  function handleVoiceClick() {
    if ($activeView !== 'chat') {
      activeView.set('chat');
    }
    toggleAlexaMic();
  }

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

  let isScrolled = false;

  function updateScroll() {
    const winScroll = typeof window !== 'undefined' ? (window.scrollY || document.documentElement.scrollTop || 0) : 0;
    const appEl = typeof document !== 'undefined' ? document.querySelector('.app-layout') : null;
    const appScroll = appEl ? appEl.scrollTop : 0;
    isScrolled = winScroll > 6 || appScroll > 6;
  }

  onMount(() => {
    updateScroll();
    window.addEventListener('scroll', updateScroll, { passive: true });
    const appEl = document.querySelector('.app-layout');
    if (appEl) {
      appEl.addEventListener('scroll', updateScroll, { passive: true });
    }
    return () => {
      window.removeEventListener('scroll', updateScroll);
      if (appEl) {
        appEl.removeEventListener('scroll', updateScroll);
      }
    };
  });

  $: if ($activeView) {
    setTimeout(updateScroll, 50);
  }

  function handleKeydown(e) {
    if (e.key === 'Escape') {
      if (showUserMenu) showUserMenu = false;
      if (showRegionMenu) showRegionMenu = false;
      if (showStatusPopover) showStatusPopover = false;
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<header
  class="top-strip"
  class:scrolled={isScrolled}
  class:data-view={$activeView !== 'chat'}
  aria-label="Glean simulator top navigation"
>
  <!-- LEFT: Brand Orb + Wordmark -->
  <div class="col-left">
    <a
      class="glean-logo"
      href="/"
      on:click|preventDefault={() => activeView.set('chat')}
      aria-label="Glean home"
    >
      <svg width="32" height="32" viewBox="0 0 48 48" aria-hidden="true">
        <circle cx="24" cy="24" r="24" fill="var(--logo-halo)"/>
        <circle cx="24" cy="24" r="18" fill="var(--logo-ring)"/>
        <circle cx="24" cy="24" r="12" fill="var(--logo-core)"/>
        <ellipse cx="20.5" cy="19" rx="5" ry="3" fill="#fff" opacity="0.6" transform="rotate(-20 20.5 19)"/>
      </svg>
      <span class="glean-logo-text">glean</span>
    </a>
  </div>

  <!-- CENTER: Top Navigation Dock -->
  <nav class="col-center" aria-label="Main application sections">
    <div class="nav-dock" role="toolbar" aria-label="Application navigation dock">
      <!-- 1. Dashboard -->
      <button
        type="button"
        class="dock-item"
        class:active={$activeView === 'dashboard'}
        on:click={() => activeView.update(v => v === 'dashboard' ? 'chat' : 'dashboard')}
        aria-label={$activeView === 'dashboard' ? 'Close Dashboard' : 'Open Dashboard'}
        aria-pressed={$activeView === 'dashboard'}
      >
        <span class="dock-icon-wrap" aria-hidden="true">
          <LayoutGrid size={16} strokeWidth={1.75} />
        </span>
        <span class="dock-label">Dashboard</span>
      </button>

      <!-- 2. Document Tracker -->
      <button
        type="button"
        class="dock-item"
        class:active={$activeView === 'tracker'}
        on:click={() => activeView.update(v => v === 'tracker' ? 'chat' : 'tracker')}
        aria-label={$activeView === 'tracker' ? 'Close Document Tracker' : 'Open Document Tracker'}
        aria-pressed={$activeView === 'tracker'}
      >
        <span class="dock-icon-wrap" aria-hidden="true">
          <ClipboardCheck size={16} strokeWidth={1.75} />
        </span>
        <span class="dock-label">Tracker</span>
      </button>

      <!-- 3. Traces -->
      <button
        type="button"
        class="dock-item"
        class:active={$activeView === 'traces'}
        on:click={() => activeView.update(v => v === 'traces' ? 'chat' : 'traces')}
        aria-label={$activeView === 'traces' ? 'Close Protocol Traces' : ($toolCallTraces.length > 0 ? `Open Protocol Traces (${$toolCallTraces.length} recorded)` : 'Open Protocol Traces')}
        aria-pressed={$activeView === 'traces'}
      >
        <span class="dock-icon-wrap" aria-hidden="true">
          <Activity size={16} strokeWidth={1.75} />
        </span>
        <span class="dock-label">Traces{#if $toolCallTraces.length > 0}<span class="dock-count">({$toolCallTraces.length})</span>{/if}</span>
      </button>

      <!-- 3. Settings -->
      <button
        type="button"
        class="dock-item"
        class:active={$activeView === 'settings'}
        on:click={() => activeView.update(v => v === 'settings' ? 'chat' : 'settings')}
        aria-label={$activeView === 'settings' ? 'Close Settings' : 'Open Settings'}
        aria-pressed={$activeView === 'settings'}
      >
        <span class="dock-icon-wrap" aria-hidden="true">
          <SlidersHorizontal size={16} strokeWidth={1.75} />
        </span>
        <span class="dock-label">Settings</span>
      </button>

      <!-- 4. Voice -->
      <button
        type="button"
        class="dock-item"
        class:muted={!$alexaMicEnabled}
        on:click={handleVoiceClick}
        aria-label={$alexaMicEnabled ? 'Mute microphone' : 'Unmute microphone'}
        aria-pressed={!$alexaMicEnabled}
      >
        <span class="dock-icon-wrap" aria-hidden="true">
          {#if !$alexaMicEnabled}
            <MicOff size={16} strokeWidth={1.75} />
          {:else}
            <Mic size={16} strokeWidth={1.75} />
          {/if}
        </span>
        <span class="dock-label">Voice</span>
      </button>

      <!-- 5. Region / Jurisdiction Filter -->
      <div class="dock-divider" aria-hidden="true"></div>

      <div class="region-switcher-wrap">
        <button
          type="button"
          class="dock-item dock-region-btn"
          class:menu-open={showRegionMenu}
          on:click={() => {
            showRegionMenu = !showRegionMenu;
            if (showUserMenu) showUserMenu = false;
            if (showStatusPopover) showStatusPopover = false;
          }}
          aria-haspopup="listbox"
          aria-expanded={showRegionMenu}
          aria-label="Filter policies by region: current {activeRegionLabel}"
        >
          <span class="dock-icon-wrap" aria-hidden="true">
            <Globe size={15} strokeWidth={1.75} />
          </span>
          <span class="dock-label">{activeRegionLabel}</span>
          <span class="chevron-wrap" class:open={showRegionMenu} aria-hidden="true">
            <ChevronDown size={13} strokeWidth={1.75} />
          </span>
        </button>

        {#if showRegionMenu}
          <button
            type="button"
            class="dropdown-backdrop"
            on:click={() => showRegionMenu = false}
            aria-label="Close regions menu"
            tabindex="-1"
          ></button>

          <ul class="region-dropdown-menu" role="listbox" aria-label="Available policy regions">
            <li role="presentation">
              <button
                type="button"
                class="region-option-btn"
                class:selected={$activeJurisdiction === 'all'}
                role="option"
                aria-selected={$activeJurisdiction === 'all'}
                on:click={() => { $activeJurisdiction = 'all'; showRegionMenu = false; }}
              >
                <span class="opt-name">All Regions</span>
                <span class="opt-role">All Policies</span>
              </button>
            </li>
            <li role="presentation">
              <button
                type="button"
                class="region-option-btn"
                class:selected={$activeJurisdiction === 'IN'}
                role="option"
                aria-selected={$activeJurisdiction === 'IN'}
                on:click={() => { $activeJurisdiction = 'IN'; showRegionMenu = false; }}
              >
                <span class="opt-name">India</span>
                <span class="opt-role">Central & State</span>
              </button>
            </li>
            <li role="presentation">
              <button
                type="button"
                class="region-option-btn"
                class:selected={$activeJurisdiction === 'US'}
                role="option"
                aria-selected={$activeJurisdiction === 'US'}
                on:click={() => { $activeJurisdiction = 'US'; showRegionMenu = false; }}
              >
                <span class="opt-name">United States</span>
                <span class="opt-role">Federal & State</span>
              </button>
            </li>
          </ul>
        {/if}
      </div>
    </div>
  </nav>

  <!-- RIGHT: Live Status Pill, User Switcher Pill, Theme Toggle -->
  <div class="col-right">
    <!-- 1. Live Status Indicator & Popover Trigger -->
    <div class="live-status-wrap">
      <button
        type="button"
        class="live-status-btn status-{$connectionStatus === 'online' ? 'connected' : ($connectionStatus === 'connecting' ? 'connecting' : 'disconnected')}"
        class:popover-open={showStatusPopover}
        on:click={() => {
          showStatusPopover = !showStatusPopover;
          if (showUserMenu) showUserMenu = false;
          if (showRegionMenu) showRegionMenu = false;
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
                <span class="info-val">16 Tools (Family, Schemes, Vault, Dialects)</span>
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

    <!-- 3. User Switcher Pill ("Jace · Son / Admin" with chevron) -->
    <div class="user-switcher-wrap">
      <button
        type="button"
        class="user-switcher-btn"
        class:menu-open={showUserMenu}
        on:click={() => {
          showUserMenu = !showUserMenu;
          if (showRegionMenu) showRegionMenu = false;
          if (showStatusPopover) showStatusPopover = false;
        }}
        aria-haspopup="listbox"
        aria-expanded={showUserMenu}
        aria-label="Switch active family perspective: current user {currentFirstName}, role {currentRole}"
      >
        <span class="user-icon-wrap" aria-hidden="true">
          <User size={15} strokeWidth={1.75} />
        </span>
        <span class="user-name">{currentFirstName}</span>
        <span class="user-sep">·</span>
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

    <!-- 3. Theme Toggle (Round Icon Button) -->
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
  /* ================= TOP STRIP (Sticky Header with Opaque/Frosted Scroll Protection) ================= */
  .top-strip {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    width: 100%;
    padding: 12px 20px;
    background: transparent;
    border-bottom: 1px solid transparent;
    box-shadow: none;
    display: flex;
    align-items: center;
    justify-content: space-between;
    z-index: 60;
    box-sizing: border-box;
    font-family: 'Outfit', 'Outfit Variable', system-ui, -apple-system, sans-serif;
    font-size: 13px;
    font-weight: 500;
    color: var(--bar-text, var(--text));
    pointer-events: auto;
    transition: background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, padding 0.2s ease;
  }

  /* Scrolled or inside Data Views (Dashboard, Traces, Settings) */
  .top-strip.scrolled,
  .top-strip.data-view {
    background: var(--top-bar-bg, rgba(255, 255, 255, 0.98));
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--dock-border);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
    padding: 10px 20px;
  }

  :global([data-theme="dark"]) .top-strip.scrolled,
  :global([data-theme="dark"]) .top-strip.data-view {
    background: var(--top-bar-bg, rgba(8, 14, 24, 0.98));
    border-bottom: 1px solid var(--dock-border);
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.45);
  }

  @media (prefers-reduced-motion: reduce) {
    .top-strip,
    .top-strip * {
      transition: none !important;
      animation: none !important;
    }
  }

  /* ---------------- COLUMN LEFT: Brand Orb + Wordmark ---------------- */
  .col-left {
    pointer-events: auto;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-shrink: 0;
  }

  .glean-logo {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    border-radius: 8px;
    transition: opacity 150ms ease, transform 150ms ease;
  }
  .glean-logo:hover {
    opacity: 0.92;
    transform: translateY(-0.5px);
  }
  .glean-logo:focus-visible {
    outline: 2px solid var(--focus);
    outline-offset: 2px;
  }

  .glean-logo-text {
    font-family: inherit;
    font-size: 24px;
    font-weight: 400;
    letter-spacing: -0.01em;
    color: var(--logo-text);
    line-height: 1;
  }

  /* ---------------- COLUMN CENTER: Floating Navigation Dock ---------------- */
  .col-center {
    pointer-events: auto;
    position: absolute;
    top: 50%;
    left: calc(50% - 75px);
    transform: translate(-50%, -50%);
    display: flex;
    align-items: center;
    justify-content: center;
    width: max-content;
    z-index: 10;
  }

  .nav-dock {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 3px;
    gap: 3px;
    border: 1px solid var(--dock-border);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    background: var(--dock-bg);
    transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
  }

  :global([data-theme="dark"]) .nav-dock {
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
  }

  .dock-item {
    height: 34px;
    padding: 0 14px;
    border-radius: 999px;
    border: none;
    background: transparent;
    color: var(--dock-text);
    display: inline-flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    font-family: inherit;
    font-size: 13.5px;
    font-weight: 500;
    line-height: 1;
    position: relative;
    white-space: nowrap;
    text-decoration: none;
    transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
  }

  .dock-item:hover {
    color: var(--bar-text, var(--text));
    transform: translateY(-1px);
    background: rgba(255, 255, 255, 0.12);
  }

  :global([data-theme="light"]) .dock-item:hover {
    background: rgba(0, 0, 0, 0.04);
  }

  .dock-item:focus-visible {
    outline: 2px solid var(--dock-active-text);
    outline-offset: 2px;
  }

  .dock-item.active {
    background: var(--dock-active-bg);
    color: var(--dock-active-text);
    font-weight: 600;
  }

  /* Red when mic is muted */
  .dock-item.muted {
    color: #ef4444;
    background: rgba(239, 68, 68, 0.08);
  }

  .dock-item.muted:hover {
    color: #dc2626;
    background: rgba(239, 68, 68, 0.16);
  }

  .dock-icon-wrap {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    position: relative;
  }

  .dock-label {
    line-height: 1;
  }

  /* Traces Count Beside Label */
  .dock-count {
    margin-left: 2px;
    font-size: 11.5px;
    font-weight: 700;
    color: var(--dock-active-text, #19c3ff);
    letter-spacing: -0.2px;
  }

  :global([data-theme="light"]) .dock-count {
    color: var(--dock-active-text, #1d4ed8);
  }

  .dock-item.active .dock-count {
    color: var(--dock-active-text);
  }

  /* ---------------- COLUMN RIGHT: Live Status, User Switcher, Theme Toggle ---------------- */
  .col-right {
    pointer-events: auto;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
    flex-shrink: 0;
  }

  /* Live Status Pill */
  .live-status-wrap {
    position: relative;
    display: inline-flex;
  }

  .live-status-btn {
    height: 38px;
    padding: 0 14px;
    border-radius: 999px;
    border: 1px solid var(--dock-border);
    background: var(--dock-bg);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    display: inline-flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-family: inherit;
    font-size: 14px;
    font-weight: 500;
    line-height: 1;
    transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
  }
  .live-status-btn:hover {
    transform: translateY(-1px);
    background: var(--dock-active-bg);
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

  /* Region / Jurisdiction Inside Dock */
  .dock-divider {
    width: 1px;
    height: 18px;
    background: var(--dock-border);
    margin: 0 4px;
    flex-shrink: 0;
  }

  .region-switcher-wrap {
    position: relative;
    display: inline-flex;
    align-items: center;
  }

  .dock-region-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 0 12px;
  }

  .dock-region-btn.menu-open {
    background: var(--dock-active-bg);
    color: var(--dock-active-text);
  }

  /* Region Dropdown Menu - Exact same design as Family/User Dropdown Menu */
  .region-dropdown-menu {
    position: absolute;
    top: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%);
    min-width: 240px;
    background: #ffffff;
    border: 1px solid var(--dock-border);
    border-radius: 16px;
    box-shadow: 0 14px 40px rgba(11, 18, 32, 0.18), 0 2px 8px rgba(11, 18, 32, 0.08);
    z-index: 100;
    padding: 6px;
    margin: 0;
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  :global([data-theme="dark"]) .region-dropdown-menu {
    background: #0c1424;
    border: 1px solid var(--dock-border);
    box-shadow: 0 16px 44px rgba(0, 0, 0, 0.75);
  }

  .region-option-btn {
    width: 100%;
    border: none;
    background: transparent;
    border-radius: 10px;
    padding: 8px 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    cursor: pointer;
    font-family: inherit;
    font-size: 14px;
    color: var(--bar-text, var(--text));
    text-align: left;
    transition: background-color 150ms ease;
  }

  .region-option-btn:hover {
    background: var(--dock-active-bg);
    color: var(--dock-active-text);
  }

  .region-option-btn.selected {
    background: var(--dock-active-bg);
    color: var(--dock-active-text);
    font-weight: 600;
  }

  .region-option-btn.selected .opt-role {
    color: var(--dock-active-text);
    opacity: 0.85;
  }

  /* User Switcher Pill */
  .user-switcher-wrap {
    position: relative;
    display: inline-flex;
  }

  .user-switcher-btn {
    height: 38px;
    padding: 0 14px;
    border-radius: 999px;
    border: 1px solid var(--dock-border);
    background: var(--dock-bg);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    color: var(--dock-text);
    display: inline-flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    font-family: inherit;
    font-size: 14px;
    font-weight: 500;
    line-height: 1;
    transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
    white-space: nowrap;
  }
  .user-switcher-btn:hover {
    transform: translateY(-1px);
    background: var(--dock-active-bg);
  }
  .user-switcher-btn:focus-visible {
    outline: 2px solid var(--focus);
    outline-offset: 2px;
  }

  .user-icon-wrap {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: var(--dock-text);
  }

  .user-name {
    color: var(--bar-text, var(--text));
    font-weight: 600;
  }

  .user-sep {
    color: var(--muted);
    font-size: 14px;
    margin: 0 1px;
  }

  .user-role {
    color: var(--dock-text);
    font-size: 13px;
    font-weight: 400;
  }

  .chevron-wrap {
    display: inline-flex;
    align-items: center;
    color: var(--dock-text);
    transition: transform 150ms ease;
  }
  .chevron-wrap.open {
    transform: rotate(180deg);
  }

  /* Theme Toggle (Round Icon Button) */
  .icon-ctrl-btn.theme-btn {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    border: 1px solid var(--dock-border);
    background: var(--dock-bg);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    color: var(--dock-text);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    padding: 0;
    transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
  }
  .icon-ctrl-btn.theme-btn:hover {
    transform: translateY(-1px);
    color: var(--dock-active-text);
    background: var(--dock-active-bg);
  }
  .icon-ctrl-btn.theme-btn:focus-visible {
    outline: 2px solid var(--focus);
    outline-offset: 2px;
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

  /* User Dropdown Menu - 100% OPAQUE to prevent background chips bleed-through */
  .user-dropdown-menu {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    min-width: 230px;
    background: #ffffff;
    border: 1px solid var(--dock-border);
    border-radius: 16px;
    box-shadow: 0 14px 40px rgba(11, 18, 32, 0.18), 0 2px 8px rgba(11, 18, 32, 0.08);
    z-index: 100;
    padding: 6px;
    margin: 0;
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  :global([data-theme="dark"]) .user-dropdown-menu {
    background: #0c1424;
    border: 1px solid var(--dock-border);
    box-shadow: 0 16px 44px rgba(0, 0, 0, 0.75);
  }

  .user-option-btn {
    width: 100%;
    border: none;
    background: transparent;
    border-radius: 10px;
    padding: 8px 12px;
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
    background: var(--dock-active-bg);
    color: var(--dock-active-text);
  }
  .user-option-btn.selected {
    background: var(--dock-active-bg);
    color: var(--dock-active-text);
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
    color: var(--dock-active-text);
    opacity: 0.85;
  }

  /* ---------------- STATUS POPOVER - 100% OPAQUE ---------------- */
  .status-popover {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    width: 320px;
    background: #ffffff;
    border: 1px solid var(--dock-border);
    border-radius: 16px;
    box-shadow: 0 14px 40px rgba(11, 18, 32, 0.18), 0 2px 8px rgba(11, 18, 32, 0.08);
    z-index: 100;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: popoverFadeIn 140ms ease-out;
  }

  :global([data-theme="dark"]) .status-popover {
    background: #0c1424;
    border: 1px solid var(--dock-border);
    box-shadow: 0 16px 44px rgba(0, 0, 0, 0.75);
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
    border-bottom: 1px solid var(--dock-border);
    background: rgba(0, 0, 0, 0.04);
  }

  :global([data-theme="dark"]) .popover-header {
    background: rgba(255, 255, 255, 0.04);
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
    color: var(--dock-text);
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
    background: rgba(0, 0, 0, 0.08);
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
    color: var(--muted);
    font-weight: 500;
  }

  .popover-info-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: rgba(0, 0, 0, 0.03);
    border: 1px solid var(--dock-border);
    border-radius: 10px;
    padding: 10px 12px;
  }

  :global([data-theme="dark"]) .popover-info-grid {
    background: rgba(255, 255, 255, 0.03);
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
    color: var(--muted);
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
    border-top: 1px solid var(--dock-border);
    background: rgba(0, 0, 0, 0.04);
  }

  :global([data-theme="dark"]) .popover-footer {
    background: rgba(255, 255, 255, 0.04);
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
    border: 1px solid var(--dock-border);
    background: #ffffff;
    color: var(--dock-text);
  }
  :global([data-theme="dark"]) .popover-action-btn.secondary {
    background: #0c1424;
  }
  .popover-action-btn.secondary:hover {
    background: var(--dock-active-bg);
  }
  .popover-action-btn.primary {
    border: 1px solid var(--dock-active-text);
    background: var(--dock-active-text);
    color: var(--dock-active-bg);
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

  /* ---------------- RESPONSIVE BREAKPOINT ---------------- */
  @media (max-width: 960px) {
    .col-center {
      left: calc(50% - 35px);
    }
    .user-role,
    .user-sep {
      display: none;
    }
  }

  @media (max-width: 820px) {
    .col-center {
      left: 50%;
    }
    .dock-label {
      display: none;
    }
    .dock-item {
      padding: 0 10px;
    }
    .live-label {
      display: none;
    }
  }

  @media (max-width: 600px) {
    .top-strip {
      padding: 10px 12px;
    }
    .glean-logo .glean-logo-text {
      display: none;
    }
    .user-name {
      display: none;
    }
    .user-switcher-btn {
      padding: 0 10px;
    }
  }
</style>
