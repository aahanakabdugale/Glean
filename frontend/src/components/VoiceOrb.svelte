<script>
  import { orbState, orbLabel } from '../lib/store.js';
</script>

<!-- Voice orb stage — organic blob background + central orb -->
<div class="orb-stage" aria-hidden="true">
  <!-- Soft blob shape behind the orb (CSS clip-path) -->
  <div class="blob" class:active={$orbState !== 'idle'}></div>

  <!-- The orb itself -->
  <div
    class="orb"
    class:idle={$orbState === 'idle'}
    class:listening={$orbState === 'listening'}
    class:thinking={$orbState === 'thinking'}
    class:speaking={$orbState === 'speaking'}
    aria-label={$orbLabel}
    role="status"
  >
    <!-- Inner glow core -->
    <div class="orb-core"></div>

    <!-- Ripple rings (visible in listening + speaking states) -->
    <div class="ring ring-1"></div>
    <div class="ring ring-2"></div>
    <div class="ring ring-3"></div>
  </div>
</div>

<!-- Status label below the orb -->
<p class="orb-label" aria-live="polite">{$orbLabel}</p>

<style>
  .orb-stage {
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    width: 120px;
    height: 120px;
    flex-shrink: 0;
  }

  /* Organic blob behind the orb */
  .blob {
    position: absolute;
    inset: -12px;
    border-radius: 60% 40% 55% 45% / 45% 55% 40% 60%;
    background: var(--violet-bg);
    transition: background var(--t-slow) ease, transform var(--t-slow) var(--ease-out);
  }

  .blob.active {
    transform: scale(1.08);
    border-radius: 50% 60% 40% 55% / 55% 45% 60% 40%;
  }

  /* The orb circle */
  .orb {
    width: 72px;
    height: 72px;
    border-radius: 50%;
    position: relative;
    display: grid;
    place-items: center;
    cursor: default;
    /* Default: idle state colour */
    background: radial-gradient(circle at 35% 35%, color-mix(in srgb, var(--orb-idle) 30%, white), var(--orb-idle) 70%);
    box-shadow: 0 0 24px color-mix(in srgb, var(--orb-idle) 40%, transparent);
    transition: background var(--t-slow) ease, box-shadow var(--t-slow) ease, transform var(--t-base) var(--ease-spring);
  }

  /* ---- Idle: slow breathing ---- */
  .orb.idle {
    animation: breathe 3s ease-in-out infinite;
  }

  @keyframes breathe {
    0%, 100% { transform: scale(1); }
    50%       { transform: scale(1.06); }
  }

  /* ---- Listening: coral, ripple rings ---- */
  .orb.listening {
    background: radial-gradient(circle at 35% 35%, color-mix(in srgb, var(--orb-listen) 30%, white), var(--orb-listen) 70%);
    box-shadow: 0 0 32px color-mix(in srgb, var(--orb-listen) 50%, transparent);
    animation: none;
  }

  /* ---- Thinking: violet, spinning halo ---- */
  .orb.thinking {
    background: radial-gradient(circle at 35% 35%, color-mix(in srgb, var(--orb-think) 30%, white), var(--orb-think) 70%);
    box-shadow: 0 0 32px color-mix(in srgb, var(--orb-think) 50%, transparent);
    animation: think-spin 2s linear infinite;
  }

  @keyframes think-spin {
    0%   { filter: hue-rotate(0deg)   brightness(1); }
    50%  { filter: hue-rotate(30deg)  brightness(1.15); }
    100% { filter: hue-rotate(0deg)   brightness(1); }
  }

  /* ---- Speaking: teal, wave pulse ---- */
  .orb.speaking {
    background: radial-gradient(circle at 35% 35%, color-mix(in srgb, var(--orb-speak) 30%, white), var(--orb-speak) 70%);
    box-shadow: 0 0 32px color-mix(in srgb, var(--orb-speak) 50%, transparent);
    animation: speak-wave 0.9s ease-in-out infinite alternate;
  }

  @keyframes speak-wave {
    from { transform: scale(1);    box-shadow: 0 0 20px color-mix(in srgb, var(--orb-speak) 40%, transparent); }
    to   { transform: scale(1.1);  box-shadow: 0 0 44px color-mix(in srgb, var(--orb-speak) 60%, transparent); }
  }

  /* Inner glow core */
  .orb-core {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.55);
    filter: blur(6px);
  }

  /* Ripple rings */
  .ring {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 2px solid currentColor;
    opacity: 0;
    pointer-events: none;
  }

  .orb.listening .ring,
  .orb.speaking .ring {
    color: inherit;
    animation: ripple-out 1.8s ease-out infinite;
  }

  .orb.listening .ring { color: var(--orb-listen); }
  .orb.speaking  .ring { color: var(--orb-speak); }

  .ring-1 { animation-delay: 0s;    }
  .ring-2 { animation-delay: 0.6s;  }
  .ring-3 { animation-delay: 1.2s;  }

  @keyframes ripple-out {
    0%   { transform: scale(1);   opacity: 0.5; }
    100% { transform: scale(2.2); opacity: 0; }
  }

  /* Spinning halo for thinking state */
  .orb.thinking::before {
    content: '';
    position: absolute;
    inset: -4px;
    border-radius: 50%;
    border: 2px solid transparent;
    border-top-color: var(--orb-think);
    border-right-color: color-mix(in srgb, var(--orb-think) 50%, transparent);
    animation: halo-spin 1s linear infinite;
  }

  @keyframes halo-spin {
    to { transform: rotate(360deg); }
  }

  /* Status label */
  .orb-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-muted);
    text-align: center;
    margin-top: var(--sp-2);
    transition: color var(--t-base) ease;
  }
</style>
