<script>
  import { urgencyOf, formatDaysLeft } from '../../lib/urgency.js';
  import { CalendarCheck, Check, AlertCircle, Clock } from '@lucide/svelte';
  import { callCompleteTask } from '../../lib/mcp.js';

  export let data = [];
  let checked = {};

  async function toggle(i, task) {
    if (checked[i]) return;
    checked = { ...checked, [i]: true };
    try {
      await callCompleteTask(task.title, task.member || '');
    } catch (e) {
      console.error('Failed to complete task', e);
    }
  }
  $: validTasks = (Array.isArray(data) ? data : []).filter(t => t && (t.title || t.raw));
</script>

<div class="tasks-container" role="region" aria-label="Upcoming tasks">
  <div class="header-row">
    <CalendarCheck size={16} class="header-icon" />
    <span class="text-label uppercase">Upcoming Tasks</span>
  </div>

  {#if !validTasks || validTasks.length === 0}
    <p class="empty-state text-body">No pending tasks found. All deadlines are clear.</p>
  {:else}
    <div class="task-list" role="list">
      {#each validTasks as task, i}
        {@const level = task.overdue ? 'urgent' : urgencyOf(task.daysLeft)}
        <div class="vr-list-row {level}" class:done={checked[i]} role="listitem">
          <div class="task-left">
            <button
              type="button"
              class="check-circle"
              class:ticked={checked[i]}
              on:click={() => toggle(i, task)}
              aria-label="{checked[i] ? 'Unmark' : 'Mark'} task: {task.title || task.raw}"
              aria-pressed={checked[i]}
            >
              {#if checked[i]}
                <Check size={14} />
              {/if}
            </button>

            <div class="task-details">
              <span class="task-title text-body" class:done={checked[i]}>
                <strong>{task.title || task.raw || 'Pending Task'}</strong>
              </span>
              <div class="task-meta text-small">
                {#if task.dueDate}
                  <span>Due {task.dueDate}</span>
                {/if}
                {#if task.dueDate && task.member}
                  <span>·</span>
                {/if}
                {#if task.member}
                  <span class="task-member">{task.member}</span>
                {/if}
              </div>
            </div>
          </div>

          <div class="task-right">
            {#if checked[i]}
              <span class="vr-badge ok">
                <Check size={12} />
                <span>Done</span>
              </span>
            {:else}
              <span class="vr-badge {level}">
                {#if task.overdue}
                  <AlertCircle size={12} />
                {:else}
                  <Clock size={12} />
                {/if}
                <span>{task.statusText || (task.daysLeft != null ? formatDaysLeft(task.daysLeft) : 'Upcoming')}</span>
              </span>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <p class="disclaimer text-label">Guidance only, verify on the official site.</p>
</div>

<style>
  .tasks-container {
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

  .empty-state {
    color: var(--ok-text);
    padding: var(--sp-12);
  }

  .task-list {
    display: flex;
    flex-direction: column;
    gap: var(--sp-8);
  }

  .task-left {
    display: flex;
    align-items: center;
    gap: var(--sp-12);
  }

  .check-circle {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    border: 2px solid var(--line);
    background: transparent;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
    color: var(--ok);
    transition: all var(--dur-fast) var(--ease);
  }

  .check-circle.ticked {
    border-color: var(--ok);
    background: var(--ok-bg);
  }

  .task-details {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .task-title {
    color: var(--text);
  }

  .task-title.done {
    text-decoration: line-through;
    color: var(--text-muted);
  }

  .task-meta {
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .task-member {
    color: var(--text-muted);
  }

  .disclaimer {
    color: var(--text-muted);
  }
</style>
