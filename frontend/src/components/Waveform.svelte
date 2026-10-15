<script>
  export let state = 'idle'; // 'idle' | 'listening' | 'thinking' | 'speaking' | 'error'

  // 11 bars with baseline heights
  const bars = [8, 12, 18, 22, 26, 24, 20, 16, 12, 10, 8];
</script>

<div class="waveform {state}" aria-hidden="true">
  {#each bars as baseH, i}
    <div
      class="bar bar-{i}"
      style="--base-h: {baseH}px; --delay: {i * 0.08}s;"
    ></div>
  {/each}
</div>

<style>
  .waveform {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    height: 32px;
  }

  .bar {
    width: 4px;
    height: var(--base-h);
    background: var(--accent);
    border-radius: var(--r-pill);
    transition: height var(--dur-fast) var(--ease), opacity var(--dur-base) var(--ease);
  }

  /* Idle: low resting bars */
  .waveform.idle .bar {
    height: 6px;
    opacity: 0.35;
  }

  /* Listening: responsive wave */
  .waveform.listening .bar {
    opacity: 1;
    animation: wave-active 0.8s ease-in-out infinite alternate;
    animation-delay: var(--delay);
  }

  /* Thinking: travelling wave */
  .waveform.thinking .bar {
    opacity: 0.75;
    animation: wave-think 1.2s ease-in-out infinite;
    animation-delay: var(--delay);
  }

  /* Speaking: energetic vocal pulses */
  .waveform.speaking .bar {
    opacity: 1;
    animation: wave-speak 0.6s ease-in-out infinite alternate;
    animation-delay: var(--delay);
  }

  /* Error / Muted: flatline low red */
  .waveform.error .bar {
    height: 4px;
    background: var(--urgent);
    opacity: 0.5;
  }

  @keyframes wave-active {
    0% { height: 6px; }
    100% { height: 26px; }
  }

  @keyframes wave-think {
    0%, 100% { height: 8px; opacity: 0.4; }
    50% { height: 20px; opacity: 0.9; }
  }

  @keyframes wave-speak {
    0% { height: 8px; }
    50% { height: 26px; }
    100% { height: 14px; }
  }
</style>
