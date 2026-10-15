<script>
  export let state = 'idle'; // 'idle' | 'listening' | 'thinking' | 'speaking' | 'error'
  export let size = 'hero';  // 'hero' (140px) | 'mini' (36px)
  export let onClick = () => {};
</script>

<button
  type="button"
  class="orb-btn {size} {state}"
  on:click={onClick}
  aria-label="Voice orb state: {state}"
>
  <div class="orb-core">
    <!-- Light-theme white highlight cap -->
    <div class="highlight-cap" aria-hidden="true"></div>

    <!-- Thinking light sweep -->
    {#if state === 'thinking'}
      <div class="thinking-sweep" aria-hidden="true"></div>
    {/if}
  </div>

  <!-- Animated pulsating rings -->
  <div class="ring ring-1" aria-hidden="true"></div>
  <div class="ring ring-2" aria-hidden="true"></div>
  <div class="ring ring-3" aria-hidden="true"></div>
</button>

<style>
  .orb-btn {
    position: relative;
    border: none;
    background: transparent;
    padding: 0;
    cursor: pointer;
    display: inline-grid;
    place-items: center;
    border-radius: var(--r-pill);
    flex-shrink: 0;
    transition: transform var(--dur-fast) var(--ease);
  }

  .orb-btn:hover {
    transform: scale(1.04);
  }

  /* Size variations */
  .orb-btn.hero {
    width: 140px;
    height: 140px;
  }
  .orb-btn.mini {
    width: 36px;
    height: 36px;
  }

  /* The core circle */
  .orb-core {
    position: relative;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    background: var(--orb);
    box-shadow: var(--orb-rings);
    overflow: hidden;
    transition: box-shadow var(--dur-base) var(--ease);
  }

  /* Light theme top gloss highlight cap */
  .highlight-cap {
    position: absolute;
    top: 5%;
    left: 15%;
    width: 70%;
    height: 45%;
    border-radius: 50%;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.45) 0%, rgba(255, 255, 255, 0) 100%);
    pointer-events: none;
  }
  :global([data-theme="dark"]) .highlight-cap {
    opacity: 0.15;
  }

  /* Subtle ring elements */
  .ring {
    position: absolute;
    inset: -14px;
    border-radius: 50%;
    pointer-events: none;
    opacity: 0;
    border: 1px solid var(--accent);
    transition: opacity var(--dur-base) var(--ease);
  }
  .ring-2 {
    inset: -32px;
  }
  .ring-3 {
    inset: -54px;
  }

  .mini .ring {
    display: none;
  }

  /* --- STATE 1: IDLE --- */
  /* Slow breathing, scale 1 to 1.03 over 4s */
  .orb-btn.idle .orb-core {
    animation: breathe 4s ease-in-out infinite;
  }
  @keyframes breathe {
    0%, 100% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.03);
    }
  }

  /* --- STATE 2: LISTENING --- */
  /* Rings pulse outward, staggered */
  .orb-btn.listening .ring {
    opacity: 0.6;
    animation: pulse-out 2s cubic-bezier(0, 0.2, 0.8, 1) infinite;
  }
  .orb-btn.listening .ring-2 {
    animation-delay: 0.5s;
  }
  .orb-btn.listening .ring-3 {
    animation-delay: 1s;
  }
  @keyframes pulse-out {
    0% {
      transform: scale(0.92);
      opacity: 0.8;
    }
    100% {
      transform: scale(1.15);
      opacity: 0;
    }
  }

  /* --- STATE 3: THINKING --- */
  /* A soft light sweep rotates inside, 1.6s */
  .thinking-sweep {
    position: absolute;
    inset: -50%;
    background: conic-gradient(from 0deg, transparent 0%, rgba(255, 255, 255, 0.6) 25%, transparent 50%);
    animation: sweep-rotate 1.6s linear infinite;
  }
  @keyframes sweep-rotate {
    100% {
      transform: rotate(360deg);
    }
  }

  /* --- STATE 4: SPEAKING --- */
  /* Gentle ripple pulse */
  .orb-btn.speaking .orb-core {
    animation: speak-pulse 1.2s ease-in-out infinite alternate;
  }
  .orb-btn.speaking .ring {
    opacity: 0.4;
    animation: pulse-out 1.6s ease-out infinite;
  }
  @keyframes speak-pulse {
    0% {
      transform: scale(0.98);
    }
    100% {
      transform: scale(1.05);
    }
  }

  /* --- STATE 5: ERROR / MUTED --- */
  /* Rings turn --urgent at low opacity, short shake */
  .orb-btn.error .orb-core {
    box-shadow: 0 0 0 14px var(--urgent-bg), 0 0 40px var(--urgent);
    animation: shake 0.4s ease-in-out 1;
  }
  .orb-btn.muted .orb-core {
    opacity: 0.75;
    filter: saturate(0.5);
    box-shadow: 0 0 0 10px rgba(234, 67, 53, 0.15), 0 0 25px rgba(234, 67, 53, 0.25);
  }
  .orb-btn.muted:hover .orb-core {
    opacity: 0.9;
    filter: saturate(0.8);
  }
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-4px); }
    75% { transform: translateX(4px); }
  }
</style>
