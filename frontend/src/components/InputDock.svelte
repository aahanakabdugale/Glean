<script>
  // InputDock.svelte
  // The bottom input bar: mic button (STT), text field, send button.

  import { orbState } from '../lib/store.js';

  export let onSend = (/** @type {string} */ _text) => {};

  let text = '';
  let recognition = null;
  let listening = false;

  // Set up Web Speech API if available
  if (typeof window !== 'undefined') {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SR) {
      recognition = new SR();
      recognition.continuous = false;
      recognition.lang = 'en-IN'; // Indian English, falls back gracefully

      recognition.onstart  = () => { listening = true;  orbState.set('listening'); };
      recognition.onresult = (e) => {
        text = e.results[0][0].transcript;
        handleSend();
      };
      recognition.onend   = () => { listening = false; orbState.set('idle'); };
      recognition.onerror = () => { listening = false; orbState.set('idle'); };
    }
  }

  function handleSend() {
    const trimmed = text.trim();
    if (!trimmed) return;
    text = '';
    onSend(trimmed);
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function toggleMic() {
    if (!recognition) {
      alert('Speech recognition is not supported in this browser. Try Chrome or Edge.');
      return;
    }
    if (listening) {
      recognition.stop();
    } else {
      recognition.start();
    }
  }
</script>

<div class="dock card">
  <!-- Mic button -->
  <button
    class="mic-btn"
    class:listening
    on:click={toggleMic}
    aria-label={listening ? 'Stop listening' : 'Speak your query (voice input)'}
    title={listening ? 'Tap to stop' : 'Voice input'}
  >
    {#if listening}
      <!-- Stop icon -->
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <rect x="6" y="6" width="12" height="12" rx="2"/>
      </svg>
    {:else}
      <!-- Mic icon -->
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
      </svg>
    {/if}
  </button>

  <!-- Text input -->
  <input
    type="text"
    bind:value={text}
    on:keydown={handleKey}
    placeholder="Ask Glean anything about your family's paperwork…"
    class="text-input"
    aria-label="Type your message"
    autocomplete="off"
    spellcheck="false"
  />

  <!-- Send button -->
  <button
    class="send-btn"
    on:click={handleSend}
    disabled={!text.trim()}
    aria-label="Send message"
    title="Send"
  >
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
    </svg>
  </button>
</div>

<!-- Simulated Alexa+ label, no logos -->
<p class="alexa-label">Simulated Alexa+ voice session</p>

<style>
  .dock {
    display: flex;
    align-items: center;
    gap: var(--sp-2);
    padding: var(--sp-2) var(--sp-3);
    border-radius: var(--r-xl);
    flex-shrink: 0;
  }

  /* Mic button */
  .mic-btn {
    width: 44px; height: 44px;
    border-radius: 50%;
    border: none;
    background: var(--brand-grad);
    color: white;
    display: grid; place-items: center;
    cursor: pointer;
    flex-shrink: 0;
    box-shadow: 0 0 14px color-mix(in srgb, var(--violet) 35%, transparent);
    transition: all var(--t-base) var(--ease-spring);
  }

  .mic-btn:hover {
    transform: scale(1.07);
    box-shadow: 0 0 20px color-mix(in srgb, var(--violet) 50%, transparent);
  }

  .mic-btn.listening {
    background: var(--brand-grad-2); /* coral/amber */
    box-shadow: 0 0 20px color-mix(in srgb, var(--coral) 50%, transparent);
    animation: mic-pulse 1s ease-in-out infinite alternate;
  }

  @keyframes mic-pulse {
    from { transform: scale(1); }
    to   { transform: scale(1.08); }
  }

  /* Text input */
  .text-input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text);
    font-family: var(--font-body);
    font-size: 0.95rem;
    padding: var(--sp-2) var(--sp-2);
    min-width: 0;
  }

  .text-input::placeholder { color: var(--text-muted); }

  /* Send button */
  .send-btn {
    width: 38px; height: 38px;
    border-radius: var(--r-md);
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text-muted);
    display: grid; place-items: center;
    cursor: pointer;
    flex-shrink: 0;
    transition: all var(--t-fast) ease;
  }

  .send-btn:hover:not(:disabled) {
    background: var(--violet);
    color: white;
    border-color: var(--violet);
    box-shadow: 0 0 12px color-mix(in srgb, var(--violet) 40%, transparent);
  }

  .send-btn:disabled { opacity: 0.35; cursor: default; }

  /* Alexa+ label — plain text only, no logo */
  .alexa-label {
    text-align: center;
    font-size: 0.68rem;
    color: var(--text-muted);
    opacity: 0.7;
    flex-shrink: 0;
    letter-spacing: 0.02em;
  }
</style>
