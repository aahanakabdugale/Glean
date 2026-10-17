<script>
  /**
   * Reusable Glean Logo Component (Orb Icon + Wordmark)
   *
   * @prop {number} size - Icon dimensions in pixels (default: 32)
   * @prop {boolean} showWordmark - Toggle wordmark visibility (default: true)
   * @prop {number} fontSize - Wordmark font size in pixels (default: 22)
   * @prop {number} fontWeight - Wordmark font weight (default: 500, range 400-500)
   * @prop {boolean} glow - Enable soft glow on core circle (default: true)
   * @prop {string} class - Additional CSS classes
   */
  export let size = 32;
  export let showWordmark = true;
  export let fontSize = 22;
  export let fontWeight = 500;
  export let glow = true;
  let customClass = '';
  export { customClass as class };

  // Unique filter ID instance safety
  const filterId = `glean-core-glow-${Math.random().toString(36).substring(2, 8)}`;
</script>

<div
  class="glean-logo {customClass}"
  style="--logo-size: {size}px; --logo-fs: {fontSize}px; --logo-fw: {fontWeight};"
>
  <svg
    class="glean-logo-icon"
    width={size}
    height={size}
    viewBox="0 0 48 48"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    shape-rendering="geometricPrecision"
    aria-hidden="true"
  >
    {#if glow}
      <defs>
        <filter id={filterId} x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="1.8" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
    {/if}

    <!-- Concentric circles centered at (24, 24) -->
    <!-- 1. Outer halo: r=24 -->
    <circle class="glean-halo" cx="24" cy="24" r="24" fill="var(--logo-halo)" />

    <!-- 2. Middle ring: r=18 -->
    <circle class="glean-ring" cx="24" cy="24" r="18" fill="var(--logo-ring)" />

    <!-- 3. Core: r=12, solid brand blue with soft glow -->
    <circle
      class="glean-core"
      cx="24"
      cy="24"
      r="12"
      fill="var(--logo-core)"
      filter={glow ? `url(#${filterId})` : undefined}
    />

    <!-- Small glossy highlight on core: ellipse cx=20.5 cy=19 rx=5 ry=3, white, 60% opacity -->
    <ellipse
      class="glean-shine"
      cx="20.5"
      cy="19"
      rx="5"
      ry="3"
      fill="var(--logo-shine)"
      opacity="0.6"
    />
  </svg>

  {#if showWordmark}
    <span class="glean-wordmark">glean</span>
  {/if}
</div>

<style>
  .glean-logo {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    vertical-align: middle;
    user-select: none;
    line-height: 1;
  }

  .glean-logo-icon {
    display: block;
    flex-shrink: 0;
    width: var(--logo-size, 32px);
    height: var(--logo-size, 32px);
  }

  /* Transition smoothly on theme toggle */
  .glean-halo,
  .glean-ring,
  .glean-core,
  .glean-shine {
    transition: fill var(--dur-base, 180ms) var(--ease, ease);
  }

  .glean-wordmark {
    font-family: var(--font-ui, 'Outfit Variable', system-ui, -apple-system, sans-serif);
    font-size: var(--logo-fs, 22px);
    font-weight: var(--logo-fw, 500);
    letter-spacing: -0.01em;
    color: var(--logo-text);
    text-transform: lowercase;
    transition: color var(--dur-base, 180ms) var(--ease, ease);
  }
</style>
