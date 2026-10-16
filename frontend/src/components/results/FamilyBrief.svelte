<script>
  import { Home, AlertTriangle, CheckCircle2 } from '@lucide/svelte';

  export let data = { raw: '', expiringCount: 0, tasksCount: 0 };
</script>

<div class="brief-container" role="region" aria-label="Family briefing summary">
  <div class="brief-header">
    <Home size={16} class="header-icon" />
    <span class="text-label uppercase">Family Briefing</span>
  </div>

  <!-- Summary metric status cards -->
  <div class="metrics-row">
    <div class="vr-status-card {data.expiringCount > 0 ? 'urgent' : 'ok'} metric-box">
      <span class="text-number count">{data.expiringCount}</span>
      <span class="text-small label">Documents expiring</span>
    </div>
    <div class="vr-status-card {data.tasksCount > 0 ? 'soon' : 'ok'} metric-box">
      <span class="text-number count">{data.tasksCount}</span>
      <span class="text-small label">Tasks due soon</span>
    </div>
  </div>

  <!-- Parsed brief narrative -->
  {#if data.raw}
    <div class="narrative-box">
      <pre class="narrative-text text-body">{data.raw}</pre>
    </div>
  {/if}

  <p class="disclaimer text-label">Guidance only, verify on the official site.</p>
</div>

<style>
  .brief-container {
    display: flex;
    flex-direction: column;
    gap: var(--sp-12);
    width: 100%;
  }

  .brief-header {
    display: flex;
    align-items: center;
    gap: var(--sp-8);
    color: var(--text-muted);
  }

  .uppercase {
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .metrics-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--sp-12);
  }

  .metric-box {
    padding: var(--sp-16);
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: var(--sp-4);
  }

  .count {
    color: var(--text);
  }

  .label {
    color: var(--text-muted);
  }

  .narrative-box {
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
    border-radius: var(--r-card);
    padding: var(--sp-16);
  }

  .narrative-text {
    font-family: var(--font-ui);
    color: var(--text);
    white-space: pre-wrap;
    line-height: var(--lh-body);
  }

  .disclaimer {
    color: var(--text-muted);
  }
</style>
