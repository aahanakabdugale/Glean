<script>
  // ExpiringDocs.svelte
  // Shows documents as a colour-graded timeline: expired (coral),
  // urgent (amber), soon (amber-light), safe (teal).

  export let data = []; // array of { member, docType, expiryDate, statusText, daysLeft, urgency }

  const colours = {
    expired: { badge: 'badge-coral',  bar: 'var(--coral)' },
    urgent:  { badge: 'badge-amber',  bar: 'var(--amber)' },
    soon:    { badge: 'badge-sky',    bar: 'var(--sky)' },
    safe:    { badge: 'badge-teal',   bar: 'var(--teal)' },
  };

  // Bar width: 100% = expired, shrinks as days increase
  function barWidth(item) {
    if (item.urgency === 'expired') return 100;
    const pct = Math.max(5, 100 - Math.min(item.daysLeft, 90));
    return pct;
  }
</script>

<div class="renderer" aria-label="Expiring documents">
  <h3 class="renderer-title">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
    Expiring Documents
  </h3>

  {#if !data || data.length === 0}
    <p class="empty">All documents are up to date. ✅</p>
  {:else}
    <ul class="doc-list" role="list">
      {#each data as item}
        <li class="doc-item">
          <div class="doc-header">
            <div class="doc-info">
              <span class="member-name">{item.member}</span>
              <span class="doc-type">{item.docType}</span>
            </div>
            <span class="badge {colours[item.urgency]?.badge ?? 'badge-teal'}">
              {item.statusText}
            </span>
          </div>

          <!-- Urgency bar -->
          <div class="bar-track" aria-hidden="true">
            <div
              class="bar-fill"
              style="width: {barWidth(item)}%; background: {colours[item.urgency]?.bar ?? 'var(--teal)'};"
            ></div>
          </div>

          <span class="expiry-date">Expires {item.expiryDate}</span>
        </li>
      {/each}
    </ul>
  {/if}

  <p class="disclaimer">Guidance only. Verify on the official site.</p>
</div>

<style>
  .renderer { display: flex; flex-direction: column; gap: var(--sp-3); }

  .renderer-title {
    display: flex; align-items: center; gap: var(--sp-2);
    font-size: 0.82rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.05em;
    color: var(--text-muted);
  }

  .empty { font-size: 0.88rem; color: var(--teal-text); }

  .doc-list { list-style: none; display: flex; flex-direction: column; gap: var(--sp-3); }

  .doc-item {
    display: flex; flex-direction: column; gap: 6px;
    padding: var(--sp-3) var(--sp-4);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-md);
    box-shadow: var(--shadow);
  }

  .doc-header { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-2); }

  .doc-info { display: flex; flex-direction: column; gap: 1px; }

  .member-name { font-weight: 700; font-size: 0.9rem; color: var(--text); }

  .doc-type { font-size: 0.78rem; color: var(--text-muted); }

  .bar-track {
    height: 5px; border-radius: var(--r-full);
    background: var(--surface-3); overflow: hidden;
  }

  .bar-fill {
    height: 100%; border-radius: var(--r-full);
    transition: width 0.6s var(--ease-out);
  }

  .expiry-date { font-size: 0.72rem; color: var(--text-muted); }

  .disclaimer {
    font-size: 0.68rem; color: var(--text-muted); opacity: 0.7;
    border-top: 1px solid var(--border); padding-top: var(--sp-2);
  }
</style>
