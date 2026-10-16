<script>
  import { Compass, ExternalLink, FileText, CheckCircle2 } from '@lucide/svelte';

  export let data = { schemeName: '', status: '', tasks: [], portal: '', docs: [] };
</script>

<div class="plan-container" role="region" aria-label="Application plan for {data.schemeName}">
  <div class="header-row">
    <Compass size={16} class="header-icon" />
    <span class="text-label uppercase">Application Roadmap</span>
  </div>

  {#if data.schemeName}
    <div class="scheme-title-box">
      <span class="text-h2"><strong>{data.schemeName}</strong></span>
      {#if data.status}
        <span class="vr-badge ok">{data.status}</span>
      {/if}
    </div>
  {/if}

  <!-- Stepped Action Timeline -->
  {#if data.tasks?.length > 0}
    <div class="timeline" role="list" aria-label="Application steps">
      {#each data.tasks as task, i}
        <div class="step-row" role="listitem">
          <div class="step-num text-label">{i + 1}</div>
          <div class="step-content">
            <span class="step-text text-body">{task}</span>
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <!-- Documents needed -->
  {#if data.docs?.length > 0}
    <div class="docs-box">
      <div class="docs-header">
        <FileText size={14} />
        <span class="text-label uppercase">Checklist to Prepare</span>
      </div>
      <div class="docs-grid">
        {#each data.docs as doc}
          <div class="doc-item text-small">
            <CheckCircle2 size={13} class="check-icon" />
            <span>{doc}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  {#if data.portal}
    <div class="action-footer">
      <a href={data.portal} target="_blank" rel="noopener noreferrer" class="vr-btn vr-btn-primary">
        <span>Go to official portal</span>
        <ExternalLink size={14} />
      </a>
    </div>
  {/if}

  <p class="disclaimer text-label">Guidance only, verify on the official site.</p>
</div>

<style>
  .plan-container {
    display: flex;
    flex-direction: column;
    gap: var(--sp-12);
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

  .scheme-title-box {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: var(--sp-8);
  }

  .timeline {
    display: flex;
    flex-direction: column;
    gap: var(--sp-8);
  }

  .step-row {
    display: flex;
    align-items: flex-start;
    gap: var(--sp-12);
    padding: var(--sp-12);
    border: 1px solid var(--line-soft);
    border-radius: var(--r-sm);
    background: var(--surface);
  }

  .step-num {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--accent);
    color: var(--btn-primary-text);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    flex-shrink: 0;
  }

  .step-content {
    flex: 1;
  }

  .step-text {
    color: var(--text);
  }

  .docs-box {
    background: var(--surface-2);
    padding: var(--sp-12);
    border-radius: var(--r-card);
    border: 1px solid var(--line-soft);
    display: flex;
    flex-direction: column;
    gap: var(--sp-8);
  }

  .docs-header {
    display: flex;
    align-items: center;
    gap: var(--sp-6);
    color: var(--text-muted);
  }

  .docs-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: var(--sp-8);
  }

  .doc-item {
    display: flex;
    align-items: center;
    gap: var(--sp-6);
    color: var(--text-soft);
  }

  .check-icon {
    color: var(--ok);
    flex-shrink: 0;
  }

  .action-footer {
    display: flex;
  }

  .disclaimer {
    color: var(--text-muted);
  }
</style>
