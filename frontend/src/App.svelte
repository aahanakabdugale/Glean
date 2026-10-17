<script>
  // App.svelte — root component
  // Wires together: Header, VoiceOrb, QuickChips, ChatPane, InputDock,
  // SettingsPanel, and the MCP dispatcher.

  import Header        from './components/Header.svelte';
  import VoiceScreen   from './components/VoiceScreen.svelte';
  import SettingsPanel from './components/SettingsPanel.svelte';
  import DashboardView from './components/DashboardView.svelte';
  import TracePanel    from './components/TracePanel.svelte';

  import { onMount } from 'svelte';
  import { activeView, orbState, settings, addMessage, updateLastMessage, activePersona, familyMembersList, showTracePanel, activeAmbientAlert, pushAmbientAlert, dismissAmbientAlert } from './lib/store.js';
  import * as mcp from './lib/mcp.js';
  import { cleanTextForSpeech } from './lib/speech.js';

  // Ambient audio chime for proactive notifications
  function playAmbientChime() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1174.66, ctx.currentTime + 0.15);
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.6);
    } catch {}
  }

  onMount(async () => {
    try {
      const res = await mcp.callListFamilyMembers();
      if (res && res.resultData && Array.isArray(res.resultData)) {
        familyMembersList.set(res.resultData);
      }
    } catch (e) {
      // Keep default demo members on error
    }

    // Connect to server-sent ambient push stream
    const sse = mcp.initAmbientSSE((alertData) => {
      pushAmbientAlert(alertData);
      playAmbientChime();
      if ($settings.voiceEnabled && alertData.speech) {
        speak(alertData.speech);
      }
    });

    return () => {
      if (sse) sse.close();
    };
  });

  // TTS
  function speak(text) {
    if (!$settings.voiceEnabled) return;
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const clean = cleanTextForSpeech(text);
    if (!clean) {
      orbState.set('idle');
      return;
    }
    // Limit to ~320 chars without cutting off mid-word
    let spokenPhrase = clean;
    if (spokenPhrase.length > 320) {
      spokenPhrase = spokenPhrase.slice(0, 310).replace(/\s+\S*$/, '') + '.';
    }
    const utt = new SpeechSynthesisUtterance(spokenPhrase);
    utt.rate = 1.05;
    utt.onend = utt.onerror = () => orbState.set('idle');
    window.speechSynthesis.speak(utt);
  }

  // Main dispatcher — figures out which MCP tool to call
  async function handleSend(text) {
    const q = text.toLowerCase();

    // Add user message
    addMessage({ role: 'user', text });

    // Add placeholder for assistant (streaming indicator)
    addMessage({ role: 'assistant', text: '', streaming: true });

    orbState.set('thinking');

    let result;

    try {
      if (q.includes('dashboard')) {
        result = await mcp.callGetFamilyDashboard();
        result.toolName = 'get_family_dashboard';
        result.toolArgs = {};
      } else if (q.includes('brief') || q.includes('morning') || q.includes('summary') || q.includes('update')) {
        const persona = $activePersona;
        result = await mcp.callFamilyBrief(persona);
        result.toolName = 'family_brief';
        result.toolArgs = persona && persona !== 'all' ? { member_name: persona } : {};
      } else if (q.includes('orchestrat') || q.includes('retire') || q.includes('transition') || q.includes('milestone') || q.includes('life event')) {
        const person = extractPerson(q) || ($activePersona !== 'all' ? $activePersona : 'Justin');
        let eventType = 'retirement';
        if (q.includes('adult') || q.includes('18') || q.includes('college') || q.includes('graduat') || person === 'Jace' || person === 'Gwen') eventType = 'adulthood';
        else if (q.includes('baby') || q.includes('birth') || q.includes('newborn')) eventType = 'newborn';
        else if (q.includes('mov') || q.includes('relocat') || q.includes('address') || person === 'Riley') eventType = 'relocation';
        result = await mcp.callOrchestrateLifeEvent(person, eventType);
        result.toolName = 'orchestrate_life_event';
        result.toolArgs = { member_name: person, event_type: eventType };
      } else if (q.includes('dependenc') || q.includes('blocker') || q.includes('bottleneck') || (q.includes('ready') && q.includes('apply'))) {
        const person = extractPerson(q) || ($activePersona !== 'all' ? $activePersona : '');
        result = await mcp.callAuditDocumentDependencies(person);
        result.toolName = 'audit_document_dependencies';
        result.toolArgs = person ? { member_name: person } : {};
      } else if (q.includes('conflict') || q.includes('red-tape') || q.includes('red tape') || q.includes('scrutiny') || q.includes('disqualif') || q.includes('exclusiv') || q.includes('cannibaliz')) {
        const person = extractPerson(q) || ($activePersona !== 'all' ? $activePersona : '');
        result = await mcp.callSimulateBureaucraticConflicts(person);
        result.toolName = 'simulate_bureaucratic_conflicts';
        result.toolArgs = person ? { member_name: person } : {};
      } else if (q.includes('proactive') || q.includes('ambient') || q.includes('watcher') || q.includes('sse') || q.includes('push alert') || q.includes('broadcast')) {
        const person = extractPerson(q) || ($activePersona !== 'all' ? $activePersona : '');
        result = await mcp.callTriggerProactiveAmbientAlert(person);
        result.toolName = 'trigger_proactive_ambient_alert';
        result.toolArgs = person ? { member_name: person } : {};
      } else if (q.includes('dialect') || q.includes('generation') || q.includes('explain for') || q.includes('grandparent') || q.includes('student') || q.includes('young adult') || q.includes('persona') || q.includes('sovereign savings') || q.includes('subsidy')) {
        let persona = 'grandparent';
        if (q.includes('student') || q.includes('young') || q.includes('teen') || q.includes('college') || q.includes('jace') || q.includes('gwen')) persona = 'young_adult';
        else if (q.includes('parent') || q.includes('adult') || q.includes('working') || q.includes('tax') || q.includes('riley') || q.includes('justin')) persona = 'parent';
        const scheme = extractScheme(q) || 'scss';
        result = await mcp.callExplainForGeneration(scheme, persona);
        result.toolName = 'explain_for_generation';
        result.toolArgs = { scheme_id: scheme, target_persona: persona };
      } else if (q.includes('expir') || (q.includes('document') && (q.includes('soon') || q.includes('renew')))) {
        result = await mcp.callGetExpiringDocuments(30);
        result.toolName = 'get_expiring_documents';
        result.toolArgs = { days: 30 };
      } else if (q.includes('plan') || (q.includes('apply') && q.includes('for'))) {
        const person = extractPerson(q) || ($activePersona !== 'all' ? $activePersona : 'Suresh');
        const scheme = extractScheme(q) || 'scss';
        result = await mcp.callPlanSchemeApplication(person, scheme, 7);
        result.toolName = 'plan_scheme_application';
        result.toolArgs = { name: person, scheme, days_to_prepare: 7 };
      } else if (q.includes('scheme') || q.includes('qualif') || q.includes('eligible') || q.includes('benefit') || q.includes('why') || q.includes('reason') || q.includes('reject')) {
        const person = extractPerson(q) || ($activePersona !== 'all' ? $activePersona : 'Justin');
        result = await mcp.callCheckSchemeEligibility(person);
        result.toolName = 'check_scheme_eligibility';
        result.toolArgs = { name: person };
      } else if (q.includes('checklist') || (q.includes('document') && q.includes('needed'))) {
        const scheme = extractScheme(q) || 'ayushman_vay_vandana';
        result = await mcp.callGetSchemeChecklist(scheme);
        result.toolName = 'get_scheme_checklist';
        result.toolArgs = { scheme };
      } else if (q.includes('task') || q.includes('deadline') || q.includes('upcoming')) {
        result = await mcp.callListUpcomingTasks(30);
        result.toolName = 'list_upcoming_tasks';
        result.toolArgs = { days: 30 };
      } else if (q.includes('family') || q.includes('member') || q.includes('who') || q.includes('roster') || q.includes('rooster')) {
        result = await mcp.callListFamilyMembers();
        result.toolName = 'list_family_members';
        result.toolArgs = {};
      } else {
        // Default: family brief with active persona
        const persona = $activePersona;
        result = await mcp.callFamilyBrief(persona);
        result.toolName = 'family_brief';
        result.toolArgs = persona && persona !== 'all' ? { member_name: persona } : {};
      }
    } catch (err) {
      result = { text: 'Something went wrong. Please try again.', isLive: false, ms: 0 };
    }

    // Replace the streaming placeholder with the actual message
    updateLastMessage({
      text:        result.text ?? '',
      streaming:   false,
      resultType:  result.resultType,
      resultData:  result.resultData,
      toolCall: {
        name:   result.toolName,
        args:   result.toolArgs ?? {},
        result: result.text ?? '',
        isLive: result.isLive,
        ms:     result.ms ?? 0,
      },
    });

    orbState.set('speaking');
    speak(result.spokenText || (result.text ?? ''));
    // orbState → idle is handled by TTS onend, or fallback here
    if (!$settings.voiceEnabled) setTimeout(() => orbState.set('idle'), 600);
  }

  // Simple keyword extraction for person names and scheme IDs
  function extractPerson(q) {
    if (q.includes('chandler') || q.includes('grandpa')) return 'Chandler';
    if (q.includes('amy') || q.includes('grandma')) return 'Amy';
    if (q.includes('justin') || q.includes('dad') || q.includes('father')) return 'Justin';
    if (q.includes('riley') || q.includes('mom') || q.includes('mother')) return 'Riley';
    if (q.includes('jace') || q.includes('son')) return 'Jace';
    if (q.includes('gwen') || q.includes('daughter')) return 'Gwen';

    const legacyNames = ['ramesh', 'suresh', 'sunita', 'maria'];
    return legacyNames.find(n => q.includes(n))
      ?.replace(/^./, c => c.toUpperCase()) ?? null;
  }

  function extractScheme(q) {
    if (q.includes('ayushman')) return 'ayushman_vay_vandana';
    if (q.includes('scss') || q.includes('saving')) return 'scss';
    if (q.includes('apy') || q.includes('atal')) return 'apy';
    if (q.includes('ignoaps') || q.includes('old age')) return 'ignoaps_mh';
    if (q.includes('pmjjby') || q.includes('jeevan jyoti') || q.includes('life insurance')) return 'pmjjby';
    if (q.includes('pmsby') || q.includes('suraksha') || q.includes('accident')) return 'pmsby';
    if (q.includes('sukanya') || q.includes('ssy') || q.includes('girl child')) return 'ssy';
    if (q.includes('kisan') || q.includes('farmer')) return 'pm_kisan';
    return null;
  }
</script>

<!-- ===================== LAYOUT ===================== -->
<div class="app-layout" class:data-view={$activeView !== 'chat'} class:settings-view={$activeView === 'settings'}>
  <!-- Top bar on every page -->
  <Header />

  <!-- Live Ambient Proactive Push Banner -->
  {#if $activeAmbientAlert}
    <div class="ambient-push-banner" role="alert" aria-live="assertive">
      <div class="ambient-push-content">
        <span class="ambient-push-badge">⚡ PROACTIVE AMBIENT PUSH</span>
        <div class="ambient-push-message">
          <strong class="ambient-push-title">{$activeAmbientAlert.display || 'Urgent Deadline Detected'}</strong>
          <span class="ambient-push-sub">{$activeAmbientAlert.speech || ''}</span>
        </div>
      </div>
      <div class="ambient-push-actions">
        <button
          type="button"
          class="ambient-action-btn"
          on:click={() => {
            const prompt = $activeAmbientAlert.suggested_action || 'What documents are expiring soon?';
            dismissAmbientAlert();
            handleSend(prompt);
          }}
        >
          Fix Now
        </button>
        <button
          type="button"
          class="ambient-dismiss-btn"
          on:click={dismissAmbientAlert}
          aria-label="Dismiss alert"
        >
          ✕
        </button>
      </div>
    </div>
  {/if}

  <!-- Main content area -->
  <main class="main-content" aria-label="Glean main content">
    {#if $activeView === 'settings'}
      <SettingsPanel />
    {:else if $activeView === 'dashboard'}
      <DashboardView onAction={(prompt) => { activeView.set('chat'); handleSend(prompt); }} />
    {:else}
      <VoiceScreen onSend={handleSend} />
    {/if}
  </main>

  <!-- Footer: small muted 12px text (hidden in settings view to keep 1-page fit) -->
  {#if $activeView !== 'settings'}
    <footer class="app-footer">
      <p class="text-label footer-disclaimer">Glean gives guidance only. Verify on the official site.</p>
    </footer>
  {/if}

  <!-- Live MCP Protocol Trace Drawer -->
  {#if $showTracePanel}
    <TracePanel />
  {/if}
</div>

<style>
  .app-layout {
    min-height: 100dvh;
    display: flex;
    flex-direction: column;
    width: 100%;
    margin: 0 auto;
    transition: background-color var(--dur-base) var(--ease);
  }

  .app-layout.settings-view {
    min-height: 100dvh;
  }

  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    max-width: 1400px;
    margin: 0 auto;
    padding: var(--sp-16) var(--sp-24) 0 var(--sp-24);
  }

  .settings-view .main-content {
    justify-content: center;
    padding: var(--sp-16) var(--sp-24);
    min-height: 0;
  }

  .data-view .main-content {
    max-width: 1200px;
  }

  .app-footer {
    text-align: center;
    padding: var(--sp-12) var(--sp-16) var(--sp-16) var(--sp-16);
    margin-top: var(--sp-16);
  }

  .footer-disclaimer {
    color: var(--text-muted);
    font-size: var(--fs-label);
  }

  /* Ambient Proactive Push Banner */
  .ambient-push-banner {
    width: calc(100% - 32px);
    max-width: 1200px;
    margin: var(--sp-12) auto 0 auto;
    padding: var(--sp-12) var(--sp-16);
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(6, 182, 212, 0.08));
    border: 1px solid rgba(245, 158, 11, 0.4);
    box-shadow: 0 4px 20px rgba(245, 158, 11, 0.15), 0 0 15px rgba(245, 158, 11, 0.1);
    border-radius: var(--rad-base);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--sp-16);
    animation: ambient-slide-down 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    z-index: 10;
  }

  @keyframes ambient-slide-down {
    from {
      opacity: 0;
      transform: translateY(-12px) scale(0.98);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  .ambient-push-content {
    display: flex;
    align-items: center;
    gap: var(--sp-12);
    min-width: 0;
  }

  .ambient-push-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(245, 158, 11, 0.25);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.5);
    padding: 3px 8px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.04em;
    white-space: nowrap;
    text-transform: uppercase;
  }

  .ambient-push-message {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  .ambient-push-title {
    font-size: var(--fs-small);
    color: var(--text-base);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .ambient-push-sub {
    font-size: 12px;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .ambient-push-actions {
    display: flex;
    align-items: center;
    gap: var(--sp-8);
    flex-shrink: 0;
  }

  .ambient-action-btn {
    background: #f59e0b;
    color: #0f172a;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 999px;
    border: none;
    cursor: pointer;
    transition: transform 0.15s ease, filter 0.15s ease;
  }
  .ambient-action-btn:hover {
    filter: brightness(1.1);
    transform: translateY(-1px);
  }

  .ambient-dismiss-btn {
    background: transparent;
    color: var(--text-muted);
    border: 1px solid rgba(255, 255, 255, 0.12);
    width: 26px;
    height: 26px;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    transition: background-color 0.15s ease, color 0.15s ease;
  }
  .ambient-dismiss-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-base);
  }

  @media (max-width: 720px) {
    .ambient-push-banner {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--sp-10);
    }
    .ambient-push-actions {
      align-self: flex-end;
    }
    .main-content {
      padding: var(--sp-12) var(--sp-12) 0 var(--sp-12);
    }
  }
</style>
