<script>
  import { orbState, alexaMicEnabled, toggleAlexaMic } from '../lib/store.js';
  import { Mic, Send, Square } from '@lucide/svelte';

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
      recognition.lang = 'en-IN';

      recognition.onstart = () => {
        listening = true;
        orbState.set('listening');
      };
      recognition.onresult = (e) => {
        text = e.results[0][0].transcript;
        handleSend();
      };
      recognition.onend = () => {
        listening = false;
        orbState.set($alexaMicEnabled ? 'idle' : 'error');
      };
      recognition.onerror = () => {
        listening = false;
        orbState.set($alexaMicEnabled ? 'idle' : 'error');
      };
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
    if (!$alexaMicEnabled) {
      alexaMicEnabled.set(true);
    }
    if (!recognition) {
      // Fallback for browsers or environments without WebSpeech API
      if (listening) {
        listening = false;
        orbState.set('idle');
      } else {
        listening = true;
        orbState.set('listening');
        setTimeout(() => {
          if (listening) {
            listening = false;
            orbState.set('idle');
            text = "What documents are expiring soon?";
            handleSend();
          }
        }, 1800);
      }
      return;
    }
    if (listening) {
      recognition.stop();
    } else {
      try {
        recognition.start();
      } catch (err) {
        // Recognition already active
      }
    }
  }
</script>

<div class="ask-bar-wrap" role="search" aria-label="Ask Glean">
  <div class="ask-pill" class:focused={false}>
    <!-- Mic button: 38px circle -->
    <button
      type="button"
      class="mic-btn"
      class:recording={listening}
      on:click={toggleMic}
      aria-label={listening ? 'Stop listening' : 'Start voice input'}
      title={listening ? 'Listening... click to stop' : 'Click to speak'}
    >
      {#if listening}
        <Square size={16} />
      {:else}
        <Mic size={18} />
      {/if}
    </button>

    <!-- Text input -->
    <input
      type="text"
      class="ask-input"
      bind:value={text}
      on:keydown={handleKey}
      placeholder="Ask Glean anything about your family's paperwork..."
      aria-label="Ask Glean anything about your family's paperwork"
    />

    <!-- Send button: 38px circle -->
    <button
      type="button"
      class="send-btn"
      class:active={text.trim().length > 0}
      on:click={handleSend}
      disabled={!text.trim()}
      aria-label="Send query"
      title="Send"
    >
      <Send size={16} />
    </button>
  </div>
</div>

<style>
  .ask-bar-wrap {
    width: 100%;
    max-width: 720px;
    margin: 0 auto;
    padding: var(--sp-8) 0;
  }

  /* 52px pill, --surface-2 fill */
  .ask-pill {
    display: flex;
    align-items: center;
    gap: var(--sp-8);
    height: var(--input-height);
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
    border-radius: var(--r-pill);
    padding: 0 var(--sp-8);
    box-shadow: var(--shadow-card);
    transition: all var(--dur-fast) var(--ease);
  }

  .ask-pill:focus-within {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.15);
    background: var(--surface);
  }
  :global([data-theme="dark"]) .ask-pill:focus-within {
    box-shadow: 0 0 0 3px rgba(0, 202, 255, 0.15);
  }

  /* Mic button: 38px circle */
  .mic-btn {
    width: var(--mic-size);
    height: var(--mic-size);
    border-radius: var(--r-pill);
    border: none;
    background: var(--surface);
    color: var(--accent);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
    transition: all var(--dur-fast) var(--ease);
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }

  .mic-btn:hover {
    transform: scale(1.05);
    background: var(--accent);
    color: var(--btn-primary-text);
  }

  /* Mic recording state turns the button --urgent */
  .mic-btn.recording {
    background: var(--urgent);
    color: var(--btn-primary-text);
    animation: pulse-mic 1.2s infinite alternate;
  }

  @keyframes pulse-mic {
    0% { transform: scale(1); }
    100% { transform: scale(1.1); box-shadow: 0 0 12px var(--urgent); }
  }

  .ask-input {
    flex: 1;
    height: 100%;
    border: none;
    background: transparent;
    font-family: var(--font-ui);
    font-size: var(--fs-body);
    font-weight: 400;
    color: var(--text);
    outline: none;
    padding: 0 var(--sp-4);
  }

  .ask-input::placeholder {
    color: var(--text-muted);
    font-weight: 400;
  }

  /* Send button: 38px circle */
  .send-btn {
    width: var(--mic-size);
    height: var(--mic-size);
    border-radius: var(--r-pill);
    border: none;
    background: transparent;
    color: var(--text-muted);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
    transition: all var(--dur-fast) var(--ease);
  }

  .send-btn.active {
    background: var(--accent);
    color: var(--btn-primary-text);
  }

  .send-btn:disabled {
    cursor: default;
    opacity: 0.4;
  }
</style>
