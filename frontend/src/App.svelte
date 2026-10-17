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
  import { activeView, orbState, settings, addMessage, updateLastMessage, activePersona, familyMembersList, showTracePanel, activeAmbientAlert, pushAmbientAlert, dismissAmbientAlert, alexaMicEnabled } from './lib/store.js';
  import * as mcp from './lib/mcp.js';
  import { cleanTextForSpeech } from './lib/speech.js';

  // Pending speech queue: if an ambient alert arrives while muted, speak it when unmuted
  let pendingAmbientSpeech = null;

  $: if ($alexaMicEnabled && pendingAmbientSpeech && $activeAmbientAlert) {
    const textToSpeak = pendingAmbientSpeech;
    pendingAmbientSpeech = null;
    playAmbientChime();
    speak(textToSpeak);
  } else if (!$alexaMicEnabled) {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }

  // Ambient audio chime for proactive notifications
  function playAmbientChime() {
    if (!$alexaMicEnabled) return;
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
      if ($alexaMicEnabled) {
        playAmbientChime();
        if ($settings.voiceEnabled && alertData.speech) {
          speak(alertData.speech);
        }
      } else {
        // Retain alert speech so when the user un-mutes, it speaks
        if (alertData.speech) {
          pendingAmbientSpeech = alertData.speech;
        }
      }
    });

    return () => {
      if (sse) sse.close();
    };
  });

  // TTS
  function speak(text) {
    if (!$alexaMicEnabled || !$settings.voiceEnabled) return;
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

  <!-- Live Ambient Proactive Push Card (Bottom-Right Floating Box) -->
  {#if $activeAmbientAlert}
    <aside class="ambient-push-card" role="alert" aria-live="assertive">
      <div class="ambient-push-header">
        <span class="ambient-push-badge">⚡ URGENT ALERT</span>
        <button
          type="button"
          class="ambient-dismiss-btn"
          on:click={dismissAmbientAlert}
          aria-label="Dismiss alert"
        >
          ✕
        </button>
      </div>

      <div class="ambient-push-body">
        <strong class="ambient-push-title">{$activeAmbientAlert.display || 'Urgent Deadline Detected'}</strong>
        {#if $activeAmbientAlert.speech}
          <p class="ambient-push-desc">{$activeAmbientAlert.speech}</p>
        {/if}
      </div>

      <div class="ambient-push-footer">
        <button
          type="button"
          class="ambient-action-btn"
          on:click={() => {
            const prompt = $activeAmbientAlert.suggested_action || 'What documents are expiring soon?';
            dismissAmbientAlert();
            handleSend(prompt);
          }}
        >
          Fix Now →
        </button>
      </div>
    </aside>
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
    padding: var(--sp-24) var(--sp-24) 0 var(--sp-24);
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

  /* Ambient Proactive Push Card (Bottom-Right Floating Square Box) */
  .ambient-push-card {
    position: fixed;
    right: 24px;
    bottom: 24px;
    width: 310px;
    background: var(--surface, #ffffff);
    background: linear-gradient(160deg, rgba(239, 68, 68, 0.08) 0%, var(--surface, #ffffff) 55%);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1.5px solid rgba(239, 68, 68, 0.45);
    box-shadow: 0 12px 36px rgba(239, 68, 68, 0.22), 0 2px 10px rgba(0, 0, 0, 0.1);
    border-radius: 18px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    animation: ambient-pop-up 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    z-index: 999;
  }

  :global([data-theme="dark"]) .ambient-push-card {
    background: linear-gradient(160deg, rgba(239, 68, 68, 0.16) 0%, rgba(20, 10, 15, 0.95) 60%);
    border: 1.5px solid rgba(239, 68, 68, 0.55);
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6), 0 0 24px rgba(239, 68, 68, 0.25);
  }

  @keyframes ambient-pop-up {
    from {
      opacity: 0;
      transform: translateY(16px) scale(0.96);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  .ambient-push-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .ambient-push-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(239, 68, 68, 0.16);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.35);
    padding: 3px 8px;
    border-radius: 999px;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  .ambient-dismiss-btn {
    background: transparent;
    color: var(--text-muted);
    border: 1px solid var(--line-soft, rgba(0, 0, 0, 0.08));
    width: 24px;
    height: 24px;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    transition: background-color 0.15s ease, color 0.15s ease, border-color 0.15s ease;
  }
  .ambient-dismiss-btn:hover {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
    border-color: rgba(239, 68, 68, 0.3);
  }

  .ambient-push-body {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .ambient-push-title {
    font-size: 14.5px;
    font-weight: 600;
    color: var(--text, #111827);
    line-height: 1.35;
  }

  .ambient-push-desc {
    font-size: 12.5px;
    line-height: 1.5;
    color: var(--text-muted, #64748b);
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .ambient-push-footer {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    margin-top: 4px;
  }

  .ambient-action-btn {
    background: #ef4444;
    color: #ffffff;
    font-size: 12px;
    font-weight: 600;
    padding: 7px 16px;
    border-radius: 999px;
    border: none;
    cursor: pointer;
    box-shadow: 0 4px 14px rgba(239, 68, 68, 0.35);
    transition: transform 0.15s ease, filter 0.15s ease, box-shadow 0.15s ease;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .ambient-action-btn:hover {
    filter: brightness(1.08);
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(239, 68, 68, 0.45);
  }
  .ambient-action-btn:active {
    transform: translateY(0);
  }

  @media (max-width: 720px) {
    .ambient-push-card {
      right: 16px;
      bottom: 16px;
      width: calc(100% - 32px);
      max-width: 340px;
    }
    .main-content {
      padding: var(--sp-12) var(--sp-12) 0 var(--sp-12);
    }
  }
</style>
