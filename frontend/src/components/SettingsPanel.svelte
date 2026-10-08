<script>
  import { settings, activeView, theme, toggleTheme } from '../lib/store.js';
  import { testConnection } from '../lib/mcp.js';

  let testing = false;
  let testResult = '';

  async function handleTest() {
    testing = true;
    testResult = '';
    const ok = await testConnection();
    testResult = ok ? '✅ Connected to Glean MCP server.' : '❌ Could not reach server. Check the URL and token.';
    testing = false;
  }

  function close() {
    activeView.set('chat');
  }
</script>

<div class="panel card" role="region" aria-label="Glean settings">
  <div class="panel-header">
    <h2 class="panel-title">Settings</h2>
    <button class="close-btn" on:click={close} aria-label="Close settings">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>
  </div>

  <!-- Server connection -->
  <section class="section">
    <h3 class="section-title">MCP Server Connection</h3>
    <p class="section-hint">Glean connects to your real MCP server over Streamable HTTP. Set these to point at your running <code>server.py</code>.</p>

    <label class="field">
      <span class="field-label">Server URL</span>
      <input
        type="url"
        bind:value={$settings.serverUrl}
        placeholder="http://localhost:8000/mcp"
        class="field-input"
        autocomplete="off"
        spellcheck="false"
      />
    </label>

    <label class="field">
      <span class="field-label">Bearer Token <span class="field-hint">(GLEAN_ACCESS_TOKEN — leave empty for dev mode)</span></span>
      <input
        type="password"
        bind:value={$settings.serverToken}
        placeholder="Leave empty if server has no token set"
        class="field-input"
        autocomplete="off"
      />
    </label>

    <div class="test-row">
      <button class="test-btn" on:click={handleTest} disabled={testing} aria-busy={testing}>
        {testing ? 'Testing…' : 'Test Connection'}
      </button>
      {#if testResult}
        <span class="test-result" class:ok={testResult.startsWith('✅')}>{testResult}</span>
      {/if}
    </div>
  </section>

  <!-- Voice & display -->
  <section class="section">
    <h3 class="section-title">Voice & Display</h3>

    <div class="toggle-row">
      <div>
        <span class="toggle-label">Voice responses (TTS)</span>
        <span class="toggle-hint">Speak Glean's replies aloud using browser speech synthesis.</span>
      </div>
      <button
        class="toggle"
        class:on={$settings.voiceEnabled}
        on:click={() => settings.update(s => ({ ...s, voiceEnabled: !s.voiceEnabled }))}
        role="switch"
        aria-checked={$settings.voiceEnabled}
        aria-label="Voice responses"
      >
        <span class="toggle-thumb"></span>
      </button>
    </div>

    <div class="toggle-row">
      <div>
        <span class="toggle-label">Show MCP tool calls</span>
        <span class="toggle-hint">Display expandable tool call chips under each reply.</span>
      </div>
      <button
        class="toggle"
        class:on={$settings.showToolCalls}
        on:click={() => settings.update(s => ({ ...s, showToolCalls: !s.showToolCalls }))}
        role="switch"
        aria-checked={$settings.showToolCalls}
        aria-label="Show MCP tool calls"
      >
        <span class="toggle-thumb"></span>
      </button>
    </div>

    <div class="toggle-row">
      <div>
        <span class="toggle-label">Dark theme</span>
        <span class="toggle-hint">Switch between light and dark appearance.</span>
      </div>
      <button
        class="toggle"
        class:on={$theme === 'dark'}
        on:click={toggleTheme}
        role="switch"
        aria-checked={$theme === 'dark'}
        aria-label="Dark theme"
      >
        <span class="toggle-thumb"></span>
      </button>
    </div>
  </section>

  <!-- Disclaimer -->
  <footer class="disclaimer">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
    Glean gives guidance only. Always verify eligibility on the official government portal before applying.
  </footer>
</div>

<style>
  .panel {
    padding: var(--sp-5);
    display: flex;
    flex-direction: column;
    gap: var(--sp-5);
    max-height: calc(100dvh - 200px);
    overflow-y: auto;
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .panel-title {
    font-size: 1.1rem;
    font-weight: 700;
  }

  .close-btn {
    width: 30px; height: 30px;
    border-radius: var(--r-md);
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    display: grid; place-items: center;
    transition: all var(--t-fast) ease;
  }
  .close-btn:hover { background: var(--coral-bg); color: var(--coral); border-color: var(--coral); }

  .section {
    display: flex;
    flex-direction: column;
    gap: var(--sp-3);
    padding-bottom: var(--sp-5);
    border-bottom: 1px solid var(--border);
  }

  .section:last-of-type { border-bottom: none; padding-bottom: 0; }

  .section-title {
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-muted);
  }

  .section-hint {
    font-size: 0.82rem;
    color: var(--text-muted);
    line-height: 1.5;
  }

  code { font-family: var(--font-mono); font-size: 0.8em; }

  .field { display: flex; flex-direction: column; gap: 5px; }

  .field-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-2);
  }

  .field-hint {
    font-size: 0.72rem;
    font-weight: 400;
    color: var(--text-muted);
  }

  .field-input {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: var(--r-md);
    padding: 8px var(--sp-3);
    color: var(--text);
    font-family: var(--font-mono);
    font-size: 0.8rem;
    transition: border-color var(--t-fast) ease;
    width: 100%;
  }

  .field-input:focus { outline: none; border-color: var(--violet); }

  .test-row { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }

  .test-btn {
    padding: 8px var(--sp-4);
    border-radius: var(--r-md);
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text);
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--t-fast) ease;
  }
  .test-btn:hover:not(:disabled) { background: var(--violet-bg); color: var(--violet-text); border-color: var(--violet); }
  .test-btn:disabled { opacity: 0.5; cursor: default; }

  .test-result { font-size: 0.82rem; }
  .test-result.ok { color: var(--teal-text); }

  /* Toggle switch */
  .toggle-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--sp-4);
  }

  .toggle-label {
    display: block;
    font-size: 0.88rem;
    font-weight: 500;
    color: var(--text);
  }

  .toggle-hint {
    display: block;
    font-size: 0.74rem;
    color: var(--text-muted);
    margin-top: 2px;
  }

  .toggle {
    flex-shrink: 0;
    width: 44px; height: 24px;
    border-radius: var(--r-full);
    border: 1px solid var(--border);
    background: var(--surface-3);
    cursor: pointer;
    position: relative;
    transition: background var(--t-base) ease, border-color var(--t-base) ease;
    padding: 0;
  }

  .toggle.on {
    background: var(--violet);
    border-color: var(--violet);
  }

  .toggle-thumb {
    position: absolute;
    top: 2px; left: 2px;
    width: 18px; height: 18px;
    border-radius: 50%;
    background: white;
    transition: transform var(--t-base) var(--ease-spring);
    box-shadow: 0 1px 4px rgba(0,0,0,0.2);
  }

  .toggle.on .toggle-thumb {
    transform: translateX(20px);
  }

  .disclaimer {
    display: flex;
    align-items: flex-start;
    gap: var(--sp-2);
    font-size: 0.75rem;
    color: var(--text-muted);
    line-height: 1.5;
    padding: var(--sp-3);
    background: var(--amber-bg);
    border-radius: var(--r-md);
    border: 1px solid var(--amber);
  }
</style>
