<script>
  import CenterSheet from './CenterSheet.svelte';
  import { cleanTextForSpeech } from '../../lib/speech.js';
  import { alexaMicEnabled } from '../../lib/store.js';

  export let data = {
    schemeName: 'Senior Citizens Savings Scheme [scss]',
    personaKey: 'grandparent',
    personaLabel: 'Grandparent (Senior Citizen)',
    toneLabel: 'Warm & Reassuring (Zero Bureaucracy)',
    speech: "Dadaji, this is the safest place to rest your lifetime savings. Think of it like a government piggy bank that pays you a handsome reward every three months directly into your bank account. The government guarantees your money will never drop, giving you steady quarterly pocket money to spend freely without depending on anyone.",
    analogy: 'A golden post office piggy-bank that gives you tea and fruit money every three months.',
    jargonIndex: '0%',
    readability: 'Grade 4 (Gentle Conversational)',
    score: 95,
    spokenBrief: ''
  };
  export let onAction = (/** @type {string} */ _text) => {};
  export let onClose = () => {};

  let activePersona = (data.personaKey === 'young_adult' ? 'student' : (data.personaKey || 'grandparent'));
  $: if (data.personaKey) {
    activePersona = (data.personaKey === 'young_adult' ? 'student' : data.personaKey);
  }

  const personaConfigs = {
    grandparent: {
      key: 'grandparent',
      name: 'Grandparent',
      headline: 'Dadaji, this is a safe savings plan. You earn 8.2%, paid every quarter.',
      accentWord: '8.2%',
      jargon: '5%',
      grade: 'Grade 4',
      speech: data.speech || "Dadaji, this is the safest place to rest your lifetime savings. Think of it like a government piggy bank that pays you a handsome reward every three months directly into your bank account. The government guarantees your money will never drop, giving you steady quarterly pocket money to spend freely without depending on anyone."
    },
    student: {
      key: 'student',
      name: 'Student',
      headline: 'SCSS explained as a sovereign high-yield savings engine with 8.2% alpha.',
      accentWord: '8.2%',
      jargon: '5%',
      grade: 'Grade 8',
      speech: "Hey! SCSS is essentially an ultra-safe 8.2% fixed-yield instrument backed by the sovereign treasury. If you help your grandparents set this up via NetBanking or Post Office digital portal, it locks in peak quarterly payouts with zero market drawdowns. It's essentially risk-free alpha."
    },
    parent: {
      key: 'parent',
      name: 'Parent',
      headline: 'SCSS explained as an 8.2% sovereign risk hedge with Section 80C deductions.',
      accentWord: '8.2%',
      jargon: '20%',
      grade: 'Grade 10',
      speech: "For elderly parent portfolio planning, SCSS offers an 8.2% sovereign-backed yield with Section 80C tax deductions up to ₹1.5 Lakhs annually. Deposit cap is ₹30 Lakhs per individual senior, delivering predictable quarterly cash flow to insulate the family budget from market volatility."
    }
  };

  $: currentCfg = personaConfigs[activePersona] || personaConfigs.grandparent;

  $: schemeTitle = data.schemeName ? data.schemeName.split(' [')[0] : 'SCSS';
  $: query = `Explain ${schemeTitle} for ${currentCfg.name.toLowerCase()}`;
  $: headline = currentCfg.headline;
  $: accentWord = currentCfg.accentWord;

  $: chips = [
    { label: `Empathetic fit ${data.score || 95}/100`, color: 'violet' }
  ];

  $: stages = [
    {
      label: 'Source',
      connectorColor: 'cyan',
      nodes: [
        {
          title: 'G.S.R. 850(E)',
          subtitle: 'Statutory text',
          color: 'cyan'
        }
      ]
    },
    {
      label: 'Engine',
      connectorColor: 'cyan',
      nodes: [
        {
          title: 'Dialect engine',
          subtitle: `Jargon ${currentCfg.jargon}`,
          color: 'violet'
        }
      ]
    },
    {
      label: 'Persona',
      nodes: [
        {
          title: currentCfg.name,
          subtitle: currentCfg.grade,
          color: 'green'
        }
      ]
    }
  ];

  $: detailsText = `"${currentCfg.speech}"\n\nReadability ${currentCfg.grade} · Jargon ${currentCfg.jargon}`;

  function selectPersona(key) {
    activePersona = key;
  }

  function handlePlayAudio() {
    if (!$alexaMicEnabled) return;
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utt = new SpeechSynthesisUtterance(cleanTextForSpeech(currentCfg.speech));
      utt.rate = 1.02;
      window.speechSynthesis.speak(utt);
    }
  }
</script>

<CenterSheet
  {query}
  {headline}
  {accentWord}
  accentColor="violet"
  {chips}
  {stages}
  primaryAction="Play in persona"
  details={detailsText}
  onPrimary={handlePlayAudio}
  {onClose}
>
  <div slot="extra" class="persona-pills-row">
    <button
      type="button"
      class="persona-pill"
      class:selected={activePersona === 'grandparent'}
      on:click={() => selectPersona('grandparent')}
    >
      <span class="persona-emoji">👴</span>
      <span>Grandparent</span>
    </button>

    <button
      type="button"
      class="persona-pill"
      class:selected={activePersona === 'student'}
      on:click={() => selectPersona('student')}
    >
      <span class="persona-emoji">🎓</span>
      <span>Student</span>
    </button>

    <button
      type="button"
      class="persona-pill"
      class:selected={activePersona === 'parent'}
      on:click={() => selectPersona('parent')}
    >
      <span class="persona-emoji">🧑‍🤝‍🧑</span>
      <span>Parent</span>
    </button>
  </div>
</CenterSheet>

<style>
  .persona-pills-row {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 8px;
    margin: 2px 0;
  }

  .persona-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--cs-pill);
    border: 1px solid var(--cs-pill-border);
    border-radius: 999px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 500;
    color: var(--cs-ink);
    cursor: pointer;
    font-family: inherit;
    transition: all 180ms ease;
  }

  .persona-pill:hover {
    background: var(--cs-pill-border);
  }

  .persona-pill.selected {
    box-shadow: 0 0 0 2px var(--cs-accent);
    border-color: var(--cs-accent);
    color: var(--cs-ink);
    font-weight: 600;
  }

  .persona-emoji {
    font-size: 14px;
    line-height: 1;
  }
</style>
