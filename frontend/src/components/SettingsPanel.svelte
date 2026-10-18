<script>
  import { onMount } from 'svelte';
  import { settings, activeView, familyMembersList } from '../lib/store.js';
  import {
    testConnection,
    callAddFamilyMember,
    callRemoveFamilyMember,
    callResetFamilyRoster,
    callListFamilyMembers
  } from '../lib/mcp.js';
  import {
    X,
    CheckCircle2,
    AlertCircle,
    Server,
    Sliders,
    Info,
    Volume2,
    Terminal,
    Check,
    Users,
    UserPlus,
    Plus,
    Trash2,
    RotateCcw
  } from '@lucide/svelte';

  export let onClose = () => activeView.set('chat');

  let testing = false;
  let testSuccess = null;
  let testMsg = '';

  // Household & Member state
  let showAddForm = false;
  let newName = '';
  let newRelation = 'Daughter';
  let newBirthYear = 2005;
  let newStatus = 'Student';
  let addingMember = false;
  let memberFeedback = '';
  let memberFeedbackType = 'ok';
  let removingName = '';
  let resetting = false;

  const relationOptions = [
    'Daughter',
    'Son',
    'Spouse',
    'Mother',
    'Father',
    'Grandmother',
    'Grandfather',
    'Sister',
    'Brother',
    'Other'
  ];

  const statusOptions = [
    'Student',
    'Employed',
    'Self-Employed',
    'Retired',
    'Homemaker',
    'Family Admin',
    'Infant / Toddler'
  ];

  async function handleAddMember() {
    if (!newName.trim()) {
      memberFeedback = 'Please enter a name.';
      memberFeedbackType = 'error';
      return;
    }
    const year = parseInt(newBirthYear, 10);
    const currYear = new Date().getFullYear();
    if (isNaN(year) || year < 1900 || year > currYear) {
      memberFeedback = `Please enter a valid birth year between 1900 and ${currYear}.`;
      memberFeedbackType = 'error';
      return;
    }

    addingMember = true;
    memberFeedback = '';
    try {
      const res = await callAddFamilyMember(newName.trim(), newRelation, year, newStatus);
      if (res && res.text && (res.text.includes('already have') || res.text.includes('wrong'))) {
        memberFeedback = res.text;
        memberFeedbackType = 'error';
      } else {
        memberFeedback = `Added ${newName.trim()} to household roster.`;
        memberFeedbackType = 'ok';
        newName = '';
        showAddForm = false;
        // Refresh store
        const refreshed = await callListFamilyMembers();
        if (refreshed && refreshed.resultData && Array.isArray(refreshed.resultData)) {
          familyMembersList.set(refreshed.resultData);
        }
      }
    } catch (err) {
      memberFeedback = err.message || 'Failed to add member.';
      memberFeedbackType = 'error';
    } finally {
      addingMember = false;
    }
  }

  async function handleRemoveMember(name) {
    if (!name) return;
    removingName = name;
    memberFeedback = '';
    try {
      await callRemoveFamilyMember(name);
      memberFeedback = `Removed ${name} from household roster.`;
      memberFeedbackType = 'ok';
      // Refresh store
      const refreshed = await callListFamilyMembers();
      if (refreshed && refreshed.resultData && Array.isArray(refreshed.resultData)) {
        familyMembersList.set(refreshed.resultData);
      }
    } catch (err) {
      memberFeedback = err.message || 'Failed to remove member.';
      memberFeedbackType = 'error';
    } finally {
      removingName = '';
    }
  }

  async function handleResetRoster() {
    resetting = true;
    memberFeedback = '';
    try {
      await callResetFamilyRoster();
      memberFeedback = 'Reset household to canonical demo roster (6 members).';
      memberFeedbackType = 'ok';
      const refreshed = await callListFamilyMembers();
      if (refreshed && refreshed.resultData && Array.isArray(refreshed.resultData)) {
        familyMembersList.set(refreshed.resultData);
      }
    } catch (err) {
      memberFeedback = err.message || 'Failed to reset roster.';
      memberFeedbackType = 'error';
    } finally {
      resetting = false;
    }
  }

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

  <!-- 1. Household & Family Profile Section -->
  <section class="household-section" aria-label="Family and household profile">
    <div class="household-header">
      <div class="section-lead">
        <div class="section-icon">
          <Users size={16} />
        </div>
        <div>
          <div class="title-with-pill">
            <h3 class="section-title">Household & Family Profile</h3>
            <span class="count-pill">{$familyMembersList.length} Members</span>
          </div>
          <p class="section-desc">
            Manage registered family members. New members automatically unlock tailored scheme rules and eligibility checks.
          </p>
        </div>
      </div>

      <div class="household-hdr-actions">
        <button
          type="button"
          class="subtle-btn add-btn"
          class:active={showAddForm}
          on:click={() => (showAddForm = !showAddForm)}
          aria-expanded={showAddForm}
        >
          {#if showAddForm}
            <X size={14} />
            <span>Cancel</span>
          {:else}
            <Plus size={14} />
            <span>Add Member</span>
          {/if}
        </button>

        <button
          type="button"
          class="subtle-btn reset-btn"
          on:click={handleResetRoster}
          disabled={resetting}
          title="Reset to 6 canonical demo members"
        >
          <RotateCcw size={13} class={resetting ? 'spin' : ''} />
          <span>{resetting ? 'Resetting…' : 'Reset Demo Roster'}</span>
        </button>
      </div>
    </div>

    <!-- Optional feedback notification -->
    {#if memberFeedback}
      <div class="feedback-banner {memberFeedbackType}" role="status">
        {#if memberFeedbackType === 'ok'}
          <CheckCircle2 size={14} />
        {:else}
          <AlertCircle size={14} />
        {/if}
        <span>{memberFeedback}</span>
      </div>
    {/if}

    <!-- Add Member Inline Drawer/Form -->
    {#if showAddForm}
      <form class="add-member-card" on:submit|preventDefault={handleAddMember}>
        <div class="add-card-header">
          <UserPlus size={15} />
          <span class="add-card-title">New Family Member</span>
        </div>

        <div class="add-fields-grid">
          <div class="field-item">
            <label for="new-member-name" class="field-label">Full Name</label>
            <input
              id="new-member-name"
              type="text"
              bind:value={newName}
              placeholder="e.g. Maya"
              class="clean-input"
              required
            />
          </div>

          <div class="field-item">
            <label for="new-member-rel" class="field-label">Relationship</label>
            <select id="new-member-rel" bind:value={newRelation} class="clean-input clean-select">
              {#each relationOptions as rel}
                <option value={rel}>{rel}</option>
              {/each}
            </select>
          </div>

          <div class="field-item">
            <label for="new-member-year" class="field-label">Birth Year</label>
            <input
              id="new-member-year"
              type="number"
              bind:value={newBirthYear}
              min="1900"
              max={new Date().getFullYear()}
              class="clean-input"
              required
            />
          </div>

          <div class="field-item">
            <label for="new-member-status" class="field-label">Status / Role</label>
            <select id="new-member-status" bind:value={newStatus} class="clean-input clean-select">
              {#each statusOptions as st}
                <option value={st}>{st}</option>
              {/each}
            </select>
          </div>
        </div>

        <div class="add-actions">
          <button type="button" class="btn-cancel" on:click={() => (showAddForm = false)}>
            Cancel
          </button>
          <button type="submit" class="btn-save" disabled={addingMember}>
            {#if addingMember}
              <span class="spinner" aria-hidden="true"></span>
              <span>Saving…</span>
            {:else}
              <Check size={14} />
              <span>Save to Household</span>
            {/if}
          </button>
        </div>
      </form>
    {/if}

    <!-- Current Household Members Grid -->
    <div class="members-roster-grid">
      {#each $familyMembersList as m}
        <div class="member-chip">
          <div class="member-avatar">
            {(m.name || '?').slice(0, 1).toUpperCase()}
          </div>
          <div class="member-meta">
            <div class="member-name-row">
              <span class="member-name">{m.name}</span>
              {#if m.relation}
                <span class="member-rel-tag">{m.relation}</span>
              {/if}
            </div>
            <div class="member-subtext">
              Born {m.birthYear || '—'} · {m.status || 'Active'}
            </div>
          </div>
          <button
            type="button"
            class="member-remove-btn"
            on:click={() => handleRemoveMember(m.name)}
            disabled={removingName === m.name}
            title="Remove {m.name}"
            aria-label="Remove {m.name}"
          >
            <Trash2 size={13} />
          </button>
        </div>
      {/each}
    </div>
  </section>

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

    <!-- Right Section: Assistant Preferences Group -->
    <section class="settings-section">
      <div class="section-header">
        <div class="section-icon">
          <Sliders size={15} />
        </div>
        <h3 class="section-title">Assistant Preferences</h3>
      </div>
      <p class="section-desc">
        Configure audio responses and chat transparency.
      </p>

      <!-- Clean unified group -->
      <div class="pref-group">
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
    max-width: 880px;
    margin: 0 auto;
    background: var(--surface);
    border: 1px solid var(--line-soft);
    border-radius: 18px;
    box-shadow: var(--shadow-pop);
    padding: 24px 28px;
    display: flex;
    flex-direction: column;
    gap: 24px;
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
    font-size: 20px;
    font-weight: 600;
    color: var(--text);
    margin: 0;
    line-height: 1.25;
  }

  .header-subtitle {
    font-size: 14px;
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

  /* Household & Family Section */
  .household-section {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding-bottom: 22px;
    border-bottom: 1px solid var(--line-soft);
  }

  .household-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
  }

  .section-lead {
    display: flex;
    align-items: flex-start;
    gap: 10px;
  }

  .title-with-pill {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .count-pill {
    font-size: 12px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: var(--r-pill);
    background: var(--surface-2);
    color: var(--accent);
    border: 1px solid var(--line-soft);
  }

  .household-hdr-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .subtle-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 34px;
    padding: 0 13px;
    border-radius: 8px;
    border: 1px solid var(--line-soft);
    background: var(--surface-2);
    color: var(--text);
    font-size: 13.5px;
    font-weight: 500;
    cursor: pointer;
    transition: all 150ms ease;
  }

  .subtle-btn:hover:not(:disabled) {
    background: var(--surface-3);
    border-color: var(--line);
    color: var(--accent);
  }

  .subtle-btn.add-btn {
    background: var(--surface-2);
    border-color: var(--line-soft);
  }

  .subtle-btn.add-btn.active {
    background: var(--surface-3);
    border-color: var(--line);
    color: var(--text-muted);
  }

  .subtle-btn.reset-btn {
    color: var(--text-muted);
  }

  .subtle-btn.reset-btn:hover:not(:disabled) {
    color: var(--text);
  }

  .subtle-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  /* Feedback Banner */
  .feedback-banner {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 9px 14px;
    border-radius: 8px;
    font-size: 12.5px;
    font-weight: 500;
    animation: fadeInModal 150ms ease-out;
  }

  .feedback-banner.ok {
    background: var(--ok-bg);
    color: var(--ok);
    border: 1px solid var(--ok);
  }

  .feedback-banner.error {
    background: rgba(239, 68, 68, 0.12);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }

  /* Add Member Inline Drawer/Form */
  .add-member-card {
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
    border-radius: 12px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    animation: fadeInModal 160ms ease-out;
  }

  .add-card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--accent);
    font-size: 14.5px;
    font-weight: 600;
  }

  .add-card-title {
    color: var(--text);
  }

  .add-fields-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
  }

  .clean-select {
    cursor: pointer;
  }

  .add-actions {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 4px;
  }

  .btn-cancel {
    height: 36px;
    padding: 0 15px;
    border-radius: 8px;
    border: 1px solid var(--line-soft);
    background: transparent;
    color: var(--text-muted);
    font-size: 13.5px;
    font-weight: 500;
    cursor: pointer;
    transition: all 150ms ease;
  }

  .btn-cancel:hover {
    color: var(--text);
    background: var(--surface-3);
  }

  .btn-save {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 36px;
    padding: 0 16px;
    border-radius: 8px;
    border: none;
    background: var(--accent);
    color: #ffffff;
    font-size: 13.5px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 150ms ease;
  }

  .btn-save:hover:not(:disabled) {
    opacity: 0.92;
  }

  .btn-save:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  /* Roster Grid */
  .members-roster-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
    gap: 10px;
  }

  .member-chip {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
    border-radius: 10px;
    transition: border-color 150ms ease, background 150ms ease;
  }

  .member-chip:hover {
    border-color: var(--line);
    background: var(--surface-3);
  }

  .member-avatar {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: var(--surface-3);
    border: 1px solid var(--line-soft);
    color: var(--accent);
    font-size: 14px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .member-meta {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
    flex: 1;
  }

  .member-name-row {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .member-name {
    font-size: 15px;
    font-weight: 600;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .member-rel-tag {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-muted);
    background: var(--surface-3);
    padding: 2px 7px;
    border-radius: 4px;
    text-transform: capitalize;
  }

  .member-subtext {
    font-size: 13px;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .member-remove-btn {
    width: 26px;
    height: 26px;
    border-radius: 6px;
    border: none;
    background: transparent;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
    opacity: 0.6;
    transition: all 150ms ease;
  }

  .member-remove-btn:hover:not(:disabled) {
    opacity: 1;
    color: #ef4444;
    background: rgba(239, 68, 68, 0.12);
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
    font-size: 16px;
    font-weight: 600;
    color: var(--text);
    margin: 0;
  }

  .section-desc {
    font-size: 13.5px;
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

  .field-label {
    font-size: 13.5px;
    font-weight: 500;
    color: var(--text-soft);
  }

  .clean-input {
    width: 100%;
    height: 40px;
    padding: 0 13px;
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
    border-radius: 8px;
    color: var(--text);
    font-family: var(--font-ui);
    font-size: 14px;
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
    font-size: 13.5px;
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
    height: 36px;
    padding: 0 15px;
    border-radius: 8px;
    border: 1px solid var(--line);
    background: var(--surface-2);
    color: var(--text);
    font-size: 13.5px;
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
    font-size: 13px;
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
    font-size: 14.5px;
    font-weight: 500;
    color: var(--text);
    line-height: 1.25;
  }

  .pref-hint {
    font-size: 13px;
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
    font-size: 13px;
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
    height: 36px;
    padding: 0 18px;
    border-radius: 8px;
    border: none;
    background: var(--accent);
    color: var(--btn-primary-text);
    font-size: 14px;
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
