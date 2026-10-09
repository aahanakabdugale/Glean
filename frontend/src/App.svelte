<script>
  // App.svelte — root component
  // Wires together: Header, VoiceOrb, QuickChips, ChatPane, InputDock,
  // SettingsPanel, and the MCP dispatcher.

  import Header        from './components/Header.svelte';
  import VoiceOrb      from './components/VoiceOrb.svelte';
  import QuickChips    from './components/QuickChips.svelte';
  import ChatPane      from './components/ChatPane.svelte';
  import InputDock     from './components/InputDock.svelte';
  import SettingsPanel from './components/SettingsPanel.svelte';

  import { onMount } from 'svelte';
  import { activeView, orbState, settings, addMessage, updateLastMessage, activePersona, familyMembersList } from './lib/store.js';
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
      if (q.includes('brief') || q.includes('morning') || q.includes('summary') || q.includes('update')) {
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
      } else if (q.includes('scheme') || q.includes('qualif') || q.includes('eligible') || q.includes('benefit')) {
        const person = extractPerson(q) || ($activePersona !== 'all' ? $activePersona : 'Ramesh');
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
    if (q.includes('apy') || q.includes('pension')) return 'apy';
    if (q.includes('ignoaps') || q.includes('old age')) return 'ignoaps_mh';
    return null;
  }
</script>

<!-- ===================== LAYOUT ===================== -->
<div class="app-layout">

  <!-- Fixed top header -->
  <Header />

  <!-- Main content area changes based on active view -->
  <main class="main-area" aria-label="Glean main content">

    {#if $activeView === 'settings'}
      <!-- Settings panel replaces the chat -->
      <SettingsPanel />

    {:else}
      <!-- Left column: orb + quick chips (hidden on mobile, shown on tablet+) -->
      <aside class="side-col" aria-label="Voice input area">
        <div class="orb-area">
          <VoiceOrb />
        </div>
        <QuickChips onChipClick={handleSend} />
      </aside>

      <!-- Right column: chat + input -->
      <section class="chat-col" aria-label="Chat">
        <ChatPane />

        <!-- Quick chips row on mobile -->
        <div class="mobile-chips">
          <QuickChips onChipClick={handleSend} />
        </div>

        <InputDock onSend={handleSend} />
      </section>
    {/if}

  </main>

  <!-- Footer disclaimer -->
  <footer class="footer">
    <span>Glean gives guidance only. Verify on the official site.</span>
  </footer>
</div>

<style>
  /* Full-height flex column */
  .app-layout {
    min-height: 100dvh;
    max-width: 1200px;
    margin: 0 auto;
    padding: var(--sp-4);
    display: flex;
    flex-direction: column;
    gap: var(--sp-3);
  }

  .main-area {
    flex: 1;
    display: flex;
    gap: var(--sp-4);
    min-height: 0; /* allows children to scroll */
  }

  /* ---- Side column (orb + chips) ---- */
  .side-col {
    width: 200px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--sp-5);
    padding-top: var(--sp-4);
  }

  .orb-area {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  /* Quick chips vertical in side column */
  .side-col :global(.chips-row) {
    flex-direction: column;
    overflow-x: visible;
    overflow-y: auto;
    width: 100%;
    max-height: calc(100dvh - 320px);
  }

  .side-col :global(.chip) {
    width: 100%;
    justify-content: flex-start;
    border-radius: var(--r-md);
  }

  /* ---- Chat column ---- */
  .chat-col {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--sp-3);
    min-width: 0;
  }

  /* Mobile chips (hidden on desktop) */
  .mobile-chips { display: none; }

  /* ---- Footer ---- */
  .footer {
    text-align: center;
    font-size: 0.68rem;
    color: var(--text-muted);
    opacity: 0.6;
    padding-bottom: var(--sp-2);
  }

  /* ---- Responsive breakpoints ---- */

  /* Tablet: collapse side column */
  @media (max-width: 768px) {
    .side-col { display: none; }
    .mobile-chips { display: block; }
    .main-area { flex-direction: column; }
  }

  /* Phone */
  @media (max-width: 480px) {
    .app-layout { padding: var(--sp-2); gap: var(--sp-2); }
  }
</style>
