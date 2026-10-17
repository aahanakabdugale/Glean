<script>
  import { theme, toggleTheme, connectionStatus, activeView, activePersona, familyMembersList, alexaMicEnabled, toggleAlexaMic, toggleTracePanel, toolCallTraces, settings } from '../lib/store.js';
  import { User, Users, Activity, Mic, MicOff, LayoutGrid, Settings, Sun, Moon, X, CheckCircle2, AlertCircle, RotateCw } from '@lucide/svelte';
  import Logo from './Logo.svelte';
  import { testConnection } from '../lib/mcp.js';

  let showStatusPopover = false;
  let testingConnection = false;
  let testResult = '';

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
    if (e.key === 'Escape' && showStatusPopover) {
      showStatusPopover = false;
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<header class="top-bar">
  <!-- Left: Glean Brand (Orb Icon + Wordmark) -->
  <button class="brand-btn" on:click={() => activeView.set('chat')} aria-label="Go to Glean home">
    <Logo size={32} fontSize={22} fontWeight={500} />
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
    <!-- Server connection status Pill & Popover -->
    <div class="status-pill-wrapper">
      <button
        class="status-pill {$connectionStatus === 'online' ? 'ok' : 'soon'}"
        class:active={showStatusPopover}
        on:click={() => showStatusPopover = !showStatusPopover}
        aria-label="Server status: {$connectionStatus}. Click for connection details."
        aria-expanded={showStatusPopover}
        title="MCP Server Status: {$connectionStatus === 'online' ? 'Live MCP HTTP (Connected)' : 'Demo Mode'} — Click for details"
      >
        <span class="status-dot"></span>
        <span class="status-text">
          {$connectionStatus === 'online' ? 'Live MCP HTTP' : 'Demo Mode'}
        </span>
      </button>

      {#if showStatusPopover}
        <!-- Backdrop to close on click outside -->
        <button
          type="button"
          class="popover-backdrop"
          on:click={() => showStatusPopover = false}
          aria-label="Close connection status"
          tabindex="-1"
        ></button>

        <div class="status-popover" role="dialog" aria-label="MCP Server Connection Details">
          <div class="popover-header">
            <div class="popover-title-row">
              <span class="status-dot {$connectionStatus === 'online' ? 'ok' : 'soon'}"></span>
              <span class="popover-title">MCP Server Connection</span>
            </div>
            <button
              type="button"
              class="popover-close-btn"
              on:click={() => showStatusPopover = false}
              aria-label="Close"
            >
              <X size={14} />
            </button>
          </div>

          <div class="popover-body">
            <div class="popover-badge-row">
              <span class="popover-status-badge {$connectionStatus === 'online' ? 'online' : 'demo'}">
                {$connectionStatus === 'online' ? '● Live Streamable HTTP' : '● Demo Mode (Fallback)'}
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
                  <CheckCircle2 size={13} />
                {:else}
                  <AlertCircle size={13} />
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
              <RotateCw size={13} class={testingConnection ? 'spin' : ''} />
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
              <Settings size={13} />
              <span>Server Settings</span>
            </button>
          </div>
        </div>
      {/if}
    </div>

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
    background: var(--surface);
    border-bottom: 1px solid var(--line-soft);
    position: relative;
    z-index: 40;
    transition: border-color var(--dur-base) var(--ease), background-color var(--dur-base) var(--ease);
  }

  .brand-btn {
    display: inline-flex;
    align-items: center;
    border: none;
    background: transparent;
    cursor: pointer;
    padding: 0;
    text-decoration: none;
    transition: transform var(--dur-fast) var(--ease), opacity var(--dur-fast) var(--ease);
  }
  .brand-btn:hover {
    transform: scale(1.02);
    opacity: 0.95;
  }
  .brand-btn:focus-visible {
    outline: 2px solid var(--logo-core);
    outline-offset: 4px;
    border-radius: 6px;
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
    color-scheme: inherit;
  }

  .persona-select option {
    background-color: var(--surface, #0C1424);
    color: var(--text, #E8F4FF);
    font-family: var(--font-ui);
    font-size: var(--fs-small);
    padding: 6px 12px;
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
  .status-pill.active {
    border-color: var(--accent);
    background: var(--surface-2);
  }

  /* Status Pill Popover */
  .status-pill-wrapper {
    position: relative;
    display: inline-flex;
    align-items: center;
  }

  .popover-backdrop {
    position: fixed;
    inset: 0;
    z-index: 90;
    background: transparent;
    border: none;
    cursor: default;
  }

  .status-popover {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    width: 320px;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--r-card, 12px);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
    z-index: 100;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: popoverFadeIn 140ms ease-out;
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
    border-bottom: 1px solid var(--line-soft);
    background: var(--surface-2);
  }

  .popover-title-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .popover-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
  }

  .popover-close-btn {
    border: none;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px;
    border-radius: 4px;
    transition: color 0.15s ease, background-color 0.15s ease;
  }
  .popover-close-btn:hover {
    color: var(--text);
    background: var(--line-soft);
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
    padding: 2px 8px;
    border-radius: var(--r-pill);
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .popover-status-badge.online {
    background: var(--ok-bg);
    color: var(--ok-text);
    border: 1px solid var(--ok);
  }
  .popover-status-badge.demo {
    background: var(--soon-bg);
    color: var(--soon-text);
    border: 1px solid var(--soon);
  }

  .popover-stat-tag {
    font-size: 11px;
    color: var(--text-muted);
    font-weight: 500;
  }

  .popover-info-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
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
    color: var(--text-muted);
  }

  .info-val {
    font-size: 12px;
    font-weight: 500;
    color: var(--text);
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
    background: var(--soon-bg);
    color: var(--soon-text);
  }
  .test-feedback.ok {
    background: var(--ok-bg);
    color: var(--ok-text);
  }

  .popover-footer {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-top: 1px solid var(--line-soft);
    background: var(--surface-2);
  }

  .popover-action-btn {
    flex: 1;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    height: 30px;
    padding: 0 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    font-family: var(--font-ui);
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .popover-action-btn.secondary {
    border: 1px solid var(--line-soft);
    background: var(--surface);
    color: var(--text);
  }
  .popover-action-btn.secondary:hover {
    border-color: var(--line);
    background: var(--surface-2);
  }
  .popover-action-btn.primary {
    border: 1px solid var(--accent);
    background: var(--accent);
    color: var(--btn-primary-text, #fff);
  }
  .popover-action-btn.primary:hover {
    background: var(--accent-2);
  }

  :global(.spin) {
    animation: spin 1s linear infinite;
  }
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
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
