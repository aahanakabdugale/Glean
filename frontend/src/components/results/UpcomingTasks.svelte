<script>
  // UpcomingTasks.svelte — checklist with animated tick
  export let data = [];
  let checked = {};

  function toggle(i) {
    checked = { ...checked, [i]: !checked[i] };
  }
</script>

<div class="renderer" aria-label="Upcoming tasks">
  <h3 class="renderer-title">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
      <polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
    </svg>
    Upcoming Tasks
  </h3>

  {#if !data || data.length === 0}
    <p class="empty">No tasks due — all clear! ✅</p>
  {:else}
    <ul class="task-list" role="list">
      {#each data as task, i}
        <li class="task-item" class:done={checked[i]}>
          <button
            class="check-btn"
            class:ticked={checked[i]}
            on:click={() => toggle(i)}
            aria-label="{checked[i] ? 'Unmark' : 'Mark'} task as done: {task.title}"
            aria-pressed={checked[i]}
          >
            {#if checked[i]}
              <!-- Tick SVG -->
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" aria-hidden="true">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            {/if}
          </button>

          <div class="task-info">
            <span class="task-title">{task.title}</span>
            <span class="task-meta">
              {#if task.member}<span class="task-member">{task.member}</span>{/if}
              <span class="badge {task.overdue ? 'badge-coral' : 'badge-sky'}">{task.statusText}</span>
            </span>
          </div>
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

  .task-list { list-style: none; display: flex; flex-direction: column; gap: var(--sp-2); }

  .task-item {
    display: flex; align-items: flex-start; gap: var(--sp-3);
    padding: var(--sp-3) var(--sp-4);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-md);
    transition: opacity var(--t-base) ease;
  }

  .task-item.done { opacity: 0.45; }

  .check-btn {
    width: 22px; height: 22px; flex-shrink: 0; margin-top: 1px;
    border-radius: 6px;
    border: 2px solid var(--border-strong);
    background: transparent;
    cursor: pointer;
    display: grid; place-items: center;
    transition: all var(--t-base) var(--ease-spring);
  }

  .check-btn.ticked {
    background: var(--green);
    border-color: var(--green);
    color: white;
    transform: scale(1.1);
  }

  .task-info { display: flex; flex-direction: column; gap: 4px; min-width: 0; }

  .task-title { font-size: 0.88rem; font-weight: 500; color: var(--text); }

  .task-meta { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; }

  .task-member {
    font-size: 0.72rem; color: var(--text-muted);
    padding: 1px 6px; border-radius: var(--r-full);
    background: var(--violet-bg); color: var(--violet-text);
  }

  .disclaimer {
    font-size: 0.68rem; color: var(--text-muted); opacity: 0.7;
    border-top: 1px solid var(--border); padding-top: var(--sp-2);
  }
</style>
