<script>
  import { urgencyOf, formatDaysLeft } from '../../lib/urgency.js';
  import { FileText, AlertCircle, Clock } from '@lucide/svelte';

  export let data = []; // array of { member, docType, expiryDate, statusText, daysLeft, urgency }
</script>

<div class="result-container" role="region" aria-label="Expiring documents">
  <div class="result-header">
    <FileText size={16} class="header-icon" />
    <span class="text-label uppercase">Expiring Documents</span>
  </div>

  {#if !data || data.length === 0}
    <p class="empty-state">All documents are currently up to date.</p>
  {:else}
    <div class="doc-list" role="list">
      {#each data as item}
        {@const level = urgencyOf(item.daysLeft)}
        <div class="vr-list-row {level}" role="listitem">
          <div class="doc-left">
            <div class="doc-titles">
              <span class="member-name text-body"><strong>{item.member}</strong></span>
              <span class="doc-type text-small">{item.docType}</span>
            </div>
            <span class="expiry-date text-small">Expires {item.expiryDate}</span>
          </div>

          <div class="doc-right">
            <span class="vr-badge {level}">
              {#if level === 'urgent'}
                <AlertCircle size={12} />
              {:else}
                <Clock size={12} />
              {/if}
              <span>{formatDaysLeft(item.daysLeft) || item.statusText}</span>
            </span>
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <p class="disclaimer text-label">Guidance only, verify on the official site.</p>
</div>

<style>
  .result-container {
    display: flex;
    flex-direction: column;
    gap: var(--sp-12);
    width: 100%;
  }

  .result-header {
    display: flex;
    align-items: center;
    gap: var(--sp-8);
    color: var(--text-muted);
  }

  .uppercase {
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .empty-state {
    color: var(--ok-text);
    padding: var(--sp-12);
  }

  .doc-list {
    display: flex;
    flex-direction: column;
    gap: var(--sp-8);
  }

  .doc-left {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .doc-titles {
    display: flex;
    align-items: center;
    gap: var(--sp-8);
  }

  .member-name {
    color: var(--text);
  }

  .doc-type {
    color: var(--text-soft);
  }

  .expiry-date {
    color: var(--text-muted);
    font-size: var(--fs-label);
  }

  .disclaimer {
    color: var(--text-muted);
    margin-top: var(--sp-4);
  }
</style>
