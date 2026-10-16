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
  import { activeView, orbState, settings, addMessage, updateLastMessage, activePersona, familyMembersList, showTracePanel } from './lib/store.js';
  import * as mcp from './lib/mcp.js';

  onMount(async () => {
    try {
      const res = await mcp.callListFamilyMembers();
      if (res && res.resultData && Array.isArray(res.resultData)) {
        familyMembersList.set(res.resultData);
      }
    } catch (e) {
      // Keep default demo members on error
    }
  });

  // TTS
  function speak(text) {
    if (!$settings.voiceEnabled) return;
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(
      text.replace(/https?:\/\/\S+/g, 'on the official website').slice(0, 300)
    );
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
      } else if (q.includes('family') || q.includes('member') || q.includes('who')) {
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
    speak(result.text ?? '');
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
    padding: var(--sp-16) var(--sp-16) var(--sp-24) var(--sp-16);
    margin-top: auto;
  }

  .footer-disclaimer {
    color: var(--text-muted);
    font-size: var(--fs-label);
  }

  @media (max-width: 720px) {
    .main-content {
      padding: var(--sp-12) var(--sp-12) 0 var(--sp-12);
    }
  }
</style>
