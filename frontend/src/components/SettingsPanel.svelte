<script>
  import { onMount } from 'svelte';
  import { settings, activeView, theme, toggleTheme, alexaMicEnabled, toggleAlexaMic } from '../lib/store.js';
  import { testConnection } from '../lib/mcp.js';
  import {
    X,
    CheckCircle2,
    AlertCircle,
    Server,
    Sliders,
    Info,
    Mic,
    Volume2,
    Terminal,
    Moon,
    Sun,
    Check
  } from '@lucide/svelte';

  export let onClose = () => activeView.set('chat');

  let testing = false;
  let testSuccess = null;
  let testMsg = '';

  async function handleTest() {
    testing = true;
    testSuccess = null;
    testMsg = '';
    const ok = await testConnection();
    testSuccess = ok;
    testMsg = ok ? 'Connected successfully' : 'Could not reach server';
    testing = false;
  }

  function handleKeydown(e) {
    if (e.key === 'Escape') {
      onClose();
    }
  }

  onMount(() => {
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  });
</script>

<div class="settings-modal" role="region" aria-label="Glean settings">
  <!-- Header -->
  <header class="modal-header">
    <div class="header-info">
      <div class="header-icon">
        <Sliders size={18} />
      </div>
      <div>
        <h2 class="header-title">Settings</h2>
        <p class="header-subtitle">Server connection and assistant preferences</p>
      </div>
    </div>
    <button
      type="button"
      class="close-btn"
      on:click={onClose}
      aria-label="Close settings"
      title="Close (Esc)"
    >
      <X size={18} />
    </button>
  </header>

  <!-- Content: 2 clean, spacious sections -->
  <div class="modal-body">
    <!-- Left Section: MCP Server -->
    <section class="settings-section">
      <div class="section-header">
        <div class="section-icon">
          <Server size={15} />
        </div>
        <h3 class="section-title">MCP Server</h3>
      </div>
      <p class="section-desc">
        Connect to your local or remote FastMCP server for live tool data.
      </p>

      <div class="fields-stack">
        <div class="field-item">
          <label for="settings-server-url" class="field-label">Server URL</label>
          <input
            id="settings-server-url"
            type="url"
            bind:value={$settings.serverUrl}
            placeholder="http://localhost:8000/mcp"
            class="clean-input font-mono"
            autocomplete="off"
            spellcheck="false"
          />
        </div>

        <div class="field-item">
          <div class="field-label-row">
            <label for="settings-server-token" class="field-label">Access Token</label>
            <span class="field-hint">Optional in dev mode</span>
          </div>
          <input
            id="settings-server-token"
            type="password"
            bind:value={$settings.serverToken}
            placeholder="Leave empty if server has no token"
            class="clean-input"
            autocomplete="off"
          />
        </div>

        <div class="test-action-row">
          <button
            type="button"
            class="test-btn"
            on:click={handleTest}
            disabled={testing}
            aria-busy={testing}
          >
            {#if testing}
              <span class="spinner" aria-hidden="true"></span>
              <span>Testing...</span>
            {:else}
              <span>Test Connection</span>
            {/if}
          </button>

          {#if testMsg}
            <div class="test-status {testSuccess ? 'ok' : 'error'}" role="status">
              {#if testSuccess}
                <CheckCircle2 size={14} />
              {:else}
                <AlertCircle size={14} />
              {/if}
              <span>{testMsg}</span>
            </div>
          {/if}
        </div>
      </div>
    </section>

    <!-- Right Section: Preferences Group -->
    <section class="settings-section">
      <div class="section-header">
        <div class="section-icon">
          <Sliders size={15} />
        </div>
        <h3 class="section-title">Voice & Display</h3>
      </div>
      <p class="section-desc">
        Configure voice recognition, audio speech, and visual appearance.
      </p>

      <!-- Clean unified group -->
      <div class="pref-group">
        <!-- Alexa Mic -->
        <div class="pref-row">
          <div class="pref-lead">
            <div class="pref-icon-wrap" class:active={$alexaMicEnabled}>
              <Mic size={15} />
            </div>
            <div class="pref-text">
              <span class="pref-label">Alexa Microphone</span>
              <span class="pref-hint">Voice listening on / off</span>
            </div>
          </div>
          <button
            type="button"
            class="clean-toggle"
            class:active={$alexaMicEnabled}
            on:click={toggleAlexaMic}
            role="switch"
            aria-checked={$alexaMicEnabled}
            aria-label="Toggle Alexa microphone"
          >
            <span class="toggle-circle"></span>
          </button>
        </div>

        <!-- TTS Voice Responses -->
        <div class="pref-row">
          <div class="pref-lead">
            <div class="pref-icon-wrap" class:active={$settings.voiceEnabled}>
              <Volume2 size={15} />
            </div>
            <div class="pref-text">
              <span class="pref-label">Voice Responses</span>
              <span class="pref-hint">Speak replies aloud with TTS</span>
            </div>
          </div>
          <button
            type="button"
            class="clean-toggle"
            class:active={$settings.voiceEnabled}
            on:click={() => settings.update(s => ({ ...s, voiceEnabled: !s.voiceEnabled }))}
            role="switch"
            aria-checked={$settings.voiceEnabled}
            aria-label="Toggle voice responses"
          >
            <span class="toggle-circle"></span>
          </button>
        </div>

        <!-- Show MCP Tool Calls -->
        <div class="pref-row">
          <div class="pref-lead">
            <div class="pref-icon-wrap" class:active={$settings.showToolCalls}>
              <Terminal size={15} />
            </div>
            <div class="pref-text">
              <span class="pref-label">Tool Call Traces</span>
              <span class="pref-hint">Show execution chips in chat</span>
            </div>
          </div>
          <button
            type="button"
            class="clean-toggle"
            class:active={$settings.showToolCalls}
            on:click={() => settings.update(s => ({ ...s, showToolCalls: !s.showToolCalls }))}
            role="switch"
            aria-checked={$settings.showToolCalls}
            aria-label="Toggle tool call traces"
          >
            <span class="toggle-circle"></span>
          </button>
        </div>

        <!-- Dark Theme -->
        <div class="pref-row">
          <div class="pref-lead">
            <div class="pref-icon-wrap" class:active={$theme === 'dark'}>
              {#if $theme === 'dark'}
                <Moon size={15} />
              {:else}
                <Sun size={15} />
              {/if}
            </div>
            <div class="pref-text">
              <span class="pref-label">Dark Theme</span>
              <span class="pref-hint">Switch dark and light theme</span>
            </div>
          </div>
          <button
            type="button"
            class="clean-toggle"
            class:active={$theme === 'dark'}
            on:click={toggleTheme}
            role="switch"
            aria-checked={$theme === 'dark'}
            aria-label="Toggle dark theme"
          >
            <span class="toggle-circle"></span>
          </button>
        </div>
      </div>
    </section>
  </div>

  <!-- Footer -->
  <footer class="modal-footer">
    <div class="footer-disclaimer">
      <Info size={14} class="disclaimer-icon" />
      <span>Glean provides guidance only. Always verify scheme eligibility on the official portal.</span>
    </div>
    <button type="button" class="done-btn" on:click={onClose}>
      <Check size={14} />
      <span>Done</span>
    </button>
  </footer>
</div>

<style>
  .settings-modal {
    width: 100%;
    max-width: 820px;
    margin: 0 auto;
    background: var(--surface);
    border: 1px solid var(--line-soft);
    border-radius: 18px;
    box-shadow: var(--shadow-pop);
    padding: 24px 28px;
    display: flex;
    flex-direction: column;
    gap: 22px;
    animation: fadeInModal 180ms ease-out;
  }

  @keyframes fadeInModal {
    from {
      opacity: 0;
      transform: translateY(6px) scale(0.99);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  /* Header */
  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--line-soft);
  }

  .header-info {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .header-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: var(--surface-2);
    color: var(--accent);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .header-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--text);
    margin: 0;
    line-height: 1.25;
  }

  .header-subtitle {
    font-size: 13px;
    color: var(--text-muted);
    margin: 2px 0 0 0;
  }

  .close-btn {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: none;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 150ms ease, color 150ms ease;
  }

  .close-btn:hover {
    background: var(--surface-2);
    color: var(--text);
  }

  /* Body: 2 balanced columns */
  .modal-body {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 32px;
    align-items: start;
  }

  .settings-section {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
  }

  .section-icon {
    color: var(--accent);
    display: flex;
    align-items: center;
  }

  .section-title {
    font-size: 14.5px;
    font-weight: 600;
    color: var(--text);
    margin: 0;
  }

  .section-desc {
    font-size: 12.5px;
    line-height: 1.45;
    color: var(--text-muted);
    margin: 0 0 16px 0;
  }

  /* Fields stack */
  .fields-stack {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .field-item {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .field-label-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .field-label {
    font-size: 12.5px;
    font-weight: 500;
    color: var(--text-soft);
  }

  .field-hint {
    font-size: 11.5px;
    color: var(--text-muted);
  }

  .clean-input {
    width: 100%;
    height: 38px;
    padding: 0 12px;
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
    border-radius: 8px;
    color: var(--text);
    font-family: var(--font-ui);
    font-size: 13px;
    outline: none;
    transition: border-color 150ms ease, background 150ms ease, box-shadow 150ms ease;
  }

  .clean-input:focus {
    border-color: var(--accent);
    background: var(--surface);
    box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.12);
  }

  :global([data-theme="dark"]) .clean-input:focus {
    box-shadow: 0 0 0 3px rgba(0, 202, 255, 0.15);
  }

  .font-mono {
    font-family: var(--font-mono);
    font-size: 12.5px;
  }

  /* Test row */
  .test-action-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 4px;
    flex-wrap: wrap;
  }

  .test-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 34px;
    padding: 0 14px;
    border-radius: 8px;
    border: 1px solid var(--line);
    background: var(--surface-2);
    color: var(--text);
    font-size: 12.5px;
    font-weight: 500;
    cursor: pointer;
    transition: all 150ms ease;
  }

  .test-btn:hover:not(:disabled) {
    border-color: var(--accent);
    color: var(--accent);
    background: var(--surface);
  }

  .test-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .spinner {
    width: 12px;
    height: 12px;
    border: 2px solid currentColor;
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 700ms linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .test-status {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
    font-weight: 500;
  }

  .test-status.ok {
    color: var(--ok-text);
  }

  .test-status.error {
    color: var(--urgent-text);
  }

  /* Grouped Preference Rows */
  .pref-group {
    display: flex;
    flex-direction: column;
    border: 1px solid var(--line-soft);
    border-radius: 12px;
    background: var(--surface);
    overflow: hidden;
  }

  .pref-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    gap: 12px;
    transition: background 150ms ease;
  }

  .pref-row:not(:last-child) {
    border-bottom: 1px solid var(--line-soft);
  }

  .pref-row:hover {
    background: var(--surface-2);
  }

  .pref-lead {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
  }

  .pref-icon-wrap {
    width: 28px;
    height: 28px;
    border-radius: 7px;
    background: var(--surface-2);
    color: var(--text-muted);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: background 150ms ease, color 150ms ease;
  }

  .pref-icon-wrap.active {
    background: rgba(66, 133, 244, 0.12);
    color: var(--accent);
  }

  :global([data-theme="dark"]) .pref-icon-wrap.active {
    background: rgba(0, 202, 255, 0.14);
    color: var(--accent);
  }

  .pref-text {
    display: flex;
    flex-direction: column;
    gap: 1px;
    min-width: 0;
  }

  .pref-label {
    font-size: 13px;
    font-weight: 500;
    color: var(--text);
    line-height: 1.25;
  }

  .pref-hint {
    font-size: 11.5px;
    color: var(--text-muted);
    line-height: 1.2;
  }

  /* Sleek modern toggle */
  .clean-toggle {
    width: 38px;
    height: 22px;
    border-radius: 999px;
    background: var(--line);
    border: none;
    padding: 2px;
    cursor: pointer;
    position: relative;
    flex-shrink: 0;
    transition: background-color 180ms ease;
  }

  .clean-toggle.active {
    background: var(--accent);
  }

  .toggle-circle {
    display: block;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #FFFFFF;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.22);
    transition: transform 180ms cubic-bezier(0.2, 0.8, 0.2, 1);
  }

  .clean-toggle.active .toggle-circle {
    transform: translateX(16px);
  }

  /* Footer */
  .modal-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--line-soft);
  }

  .footer-disclaimer {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 11.5px;
    color: var(--text-muted);
    line-height: 1.35;
    min-width: 0;
  }

  :global(.disclaimer-icon) {
    color: var(--accent);
    flex-shrink: 0;
  }

  .done-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 34px;
    padding: 0 16px;
    border-radius: 8px;
    border: none;
    background: var(--accent);
    color: var(--btn-primary-text);
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    flex-shrink: 0;
    transition: opacity 150ms ease, transform 150ms ease;
  }

  .done-btn:hover {
    opacity: 0.92;
    transform: translateY(-1px);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .settings-modal {
      padding: 18px 20px;
      gap: 18px;
    }

    .modal-body {
      grid-template-columns: 1fr;
      gap: 22px;
    }

    .modal-footer {
      flex-direction: column;
      align-items: stretch;
      gap: 12px;
    }

    .done-btn {
      justify-content: center;
    }
  }
</style>
