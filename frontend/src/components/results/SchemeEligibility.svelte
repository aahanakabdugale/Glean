<script>
  // SchemeEligibility.svelte — eligibility "tickets" with coloured badges
  export let data = { personName: '', eligible: [], checkNeeded: [], notEligible: [] };
</script>

<div class="renderer" aria-label="Scheme eligibility results for {data.personName}">
  <h3 class="renderer-title">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
      <path d="M20 12V22H4V12"/><path d="M22 7H2v5h20V7z"/><path d="M12 22V7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/>
    </svg>
    Eligibility for {data.personName}
  </h3>

  {#if data.eligible?.length > 0}
    <section>
      <span class="section-head badge badge-teal">May be eligible</span>
      <ul class="scheme-list" role="list">
        {#each data.eligible as s}
          <li class="ticket ticket-teal">
            <span class="ticket-name">{s.text.split(' — ')[0]}</span>
            <span class="ticket-reason">{s.text.split(' — ')[1] ?? ''}</span>
          </li>
        {/each}
      </ul>
    </section>
  {/if}

  {#if data.checkNeeded?.length > 0}
    <section>
      <span class="section-head badge badge-amber">Verify first</span>
      <ul class="scheme-list" role="list">
        {#each data.checkNeeded as s}
          <li class="ticket ticket-amber">
            <span class="ticket-name">{s.text.split(' — ')[0]}</span>
            <span class="ticket-reason">{s.text.split(' — ')[1] ?? ''}</span>
          </li>
        {/each}
      </ul>
    </section>
  {/if}

  {#if data.notEligible?.length > 0}
    <section>
      <span class="section-head badge badge-coral">Not eligible</span>
      <ul class="scheme-list" role="list">
        {#each data.notEligible as s}
          <li class="ticket ticket-muted">
            <span class="ticket-name">{s.text.split(' — ')[0]}</span>
            <span class="ticket-reason">{s.text.split(' — ')[1] ?? ''}</span>
          </li>
        {/each}
      </ul>
    </section>
  {/if}

  <p class="disclaimer">Guidance only — "may be eligible" means the age rule fits. Verify income, category and other criteria on the official portal before applying.</p>
</div>

<style>
  .renderer { display: flex; flex-direction: column; gap: var(--sp-3); }

  .renderer-title {
    display: flex; align-items: center; gap: var(--sp-2);
    font-size: 0.82rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.05em;
    color: var(--text-muted);
  }

  section { display: flex; flex-direction: column; gap: var(--sp-2); }

  .section-head { align-self: flex-start; margin-bottom: 2px; }

  .scheme-list { list-style: none; display: flex; flex-direction: column; gap: var(--sp-2); }

  .ticket {
    display: flex; flex-direction: column; gap: 3px;
    padding: var(--sp-3) var(--sp-4);
    border-radius: var(--r-md);
    border-left: 4px solid transparent;
  }

  .ticket-teal  { background: var(--teal-bg);   border-left-color: var(--teal); }
  .ticket-amber { background: var(--amber-bg);  border-left-color: var(--amber); }
  .ticket-muted { background: var(--surface-2); border-left-color: var(--border-strong); opacity: 0.7; }

  .ticket-name {
    font-weight: 600; font-size: 0.88rem; color: var(--text);
  }

  .ticket-reason {
    font-size: 0.75rem; color: var(--text-muted);
  }

  .disclaimer {
    font-size: 0.68rem; color: var(--text-muted); opacity: 0.7;
    border-top: 1px solid var(--border); padding-top: var(--sp-2);
  }
</style>
