<script>
  import { ShieldCheck, Calendar, AlertCircle, CheckCircle2, Clock, XCircle, ExternalLink } from '@lucide/svelte';

  export let data = { personName: '', eligible: [], checkNeeded: [], almostEligible: [], notEligible: [] };
</script>

<div class="eligibility-container" role="region" aria-label="Scheme eligibility results for {data.personName}">
  <div class="header-row">
    <ShieldCheck size={16} class="header-icon" />
    <span class="text-label uppercase">Eligibility Overview for {data.personName}</span>
  </div>

  <!-- 1. May be eligible -->
  {#if data.eligible?.length > 0}
    <div class="group-section">
      <div class="group-badge-wrap">
        <span class="vr-badge ok">
          <CheckCircle2 size={12} />
          <span>May be eligible</span>
        </span>
      </div>
      <div class="scheme-rows" role="list">
        {#each data.eligible as s}
          <div class="vr-list-row ok" role="listitem">
            <div class="scheme-info">
              <span class="scheme-name text-body"><strong>{s.text.split(' — ')[0]}</strong></span>
              <span class="scheme-reason text-small">{s.text.split(' — ')[1] ?? ''}</span>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- 2. Verify first (Check needed) -->
  {#if data.checkNeeded?.length > 0}
    <div class="group-section">
      <div class="group-badge-wrap">
        <span class="vr-badge soon">
          <Clock size={12} />
          <span>Verify criteria</span>
        </span>
      </div>
      <div class="scheme-rows" role="list">
        {#each data.checkNeeded as s}
          <div class="vr-list-row soon" role="listitem">
            <div class="scheme-info">
              <span class="scheme-name text-body"><strong>{s.text.split(' — ')[0]}</strong></span>
              <span class="scheme-reason text-small">{s.text.split(' — ')[1] ?? ''}</span>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- 3. Coming up soon (Almost eligible) -->
  {#if data.almostEligible?.length > 0}
    <div class="group-section">
      <div class="group-badge-wrap">
        <span class="vr-badge info">
          <Calendar size={12} />
          <span>Coming up soon (Within 3 yrs)</span>
        </span>
      </div>
      <div class="scheme-rows" role="list">
        {#each data.almostEligible as s}
          <div class="vr-list-row info column-item" role="listitem">
            <div class="scheme-info">
              <div class="scheme-title-line">
                <span class="scheme-name text-body"><strong>{s.text.split(' — ')[0]}</strong></span>
                <span class="vr-badge info">Almost eligible</span>
              </div>
              <span class="scheme-reason text-small">{s.text.split(' — ')[1] ?? ''}</span>
            </div>

            {#if s.suggestedTask}
              <div class="task-suggestion">
                <Calendar size={13} class="calendar-icon" />
                <span class="task-text text-small">Suggested reminder: {s.suggestedTask}</span>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- 4. Not eligible ("Why Not") -->
  {#if data.notEligible?.length > 0}
    <div class="group-section">
      <div class="group-badge-wrap">
        <span class="vr-badge neutral">
          <XCircle size={12} />
          <span>Not eligible today</span>
        </span>
      </div>
      <div class="scheme-rows" role="list">
        {#each data.notEligible as s}
          <div class="vr-list-row not-eligible-row" role="listitem">
            <div class="scheme-info">
              <span class="scheme-name text-body muted"><strong>{s.text.split(' — ')[0]}</strong></span>
              <span class="scheme-reason text-small muted">{s.text.split(' — ')[1] ?? ''}</span>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <p class="disclaimer text-label">
    Guidance only, verify on the official site. "May be eligible" indicates criteria check pass; official verification is required.
  </p>
</div>

<style>
  .eligibility-container {
    display: flex;
    flex-direction: column;
    gap: var(--sp-16);
    width: 100%;
  }

  .header-row {
    display: flex;
    align-items: center;
    gap: var(--sp-8);
    color: var(--text-muted);
  }

  .uppercase {
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .group-section {
    display: flex;
    flex-direction: column;
    gap: var(--sp-8);
  }

  .group-badge-wrap {
    display: flex;
  }

  .scheme-rows {
    display: flex;
    flex-direction: column;
    gap: var(--sp-8);
  }

  .scheme-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
    width: 100%;
  }

  .scheme-title-line {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--sp-8);
  }

  .scheme-name {
    color: var(--text);
  }

  .scheme-reason {
    color: var(--text-soft);
  }

  .column-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--sp-8);
  }

  .task-suggestion {
    display: flex;
    align-items: center;
    gap: var(--sp-6);
    background: var(--surface-2);
    padding: var(--sp-6) var(--sp-12);
    border-radius: var(--r-sm);
    width: 100%;
    color: var(--accent);
  }

  .calendar-icon {
    flex-shrink: 0;
  }

  .not-eligible-row {
    --status-color: var(--line);
    background: var(--surface);
    opacity: 0.85;
  }

  .muted {
    color: var(--text-muted);
  }

  .disclaimer {
    color: var(--text-muted);
  }
</style>
