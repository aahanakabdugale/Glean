// ============================================================
// store.js — Glean shared state
//
// Svelte stores are like little signal boxes. Any component
// can read or write them. Changes broadcast to all subscribers
// automatically — no prop drilling needed.
// ============================================================

import { writable, derived } from 'svelte/store';

// ---------- THEME -------------------------------------------
// Reads from localStorage first, then prefers-color-scheme,
// then defaults to 'light'.
function initTheme() {
  const saved = localStorage.getItem('glean-theme');
  if (saved === 'light' || saved === 'dark') return saved;
  // No saved choice: respect the OS preference
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
  return 'light';
}

export const theme = writable(initTheme());

// Whenever theme changes: update the <html> data-theme attribute
// and save the user's explicit choice to localStorage.
theme.subscribe(t => {
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('glean-theme', t);
});

export function toggleTheme() {
  theme.update(t => (t === 'light' ? 'dark' : 'light'));
}

// ---------- SETTINGS ----------------------------------------
// Persisted to localStorage so they survive page refresh.
const SETTINGS_KEY = 'glean-settings';

function loadSettings() {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) return { ...defaultSettings(), ...JSON.parse(raw) };
  } catch {}
  return defaultSettings();
}

function defaultSettings() {
  return {
    serverUrl: 'http://localhost:8000/mcp',
    serverToken: '',
    voiceEnabled: true,
    showToolCalls: true,
  };
}

export const settings = writable(loadSettings());

settings.subscribe(s => {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(s));
});

// ---------- CONNECTION STATUS --------------------------------
// 'unknown' | 'online' | 'offline'
export const connectionStatus = writable('unknown');

// ---------- ORB STATE ----------------------------------------
// 'idle' | 'listening' | 'thinking' | 'speaking'
export const orbState = writable('idle');

// Human-readable label shown under the orb
export const orbLabel = derived(orbState, s => ({
  idle:      'Ready',
  listening: 'Listening…',
  thinking:  'Thinking…',
  speaking:  'Speaking…',
}[s] ?? 'Ready'));

// ---------- MESSAGES ----------------------------------------
// Each message object shape:
// {
//   id:        string (unique),
//   role:      'user' | 'assistant',
//   text:      string,
//   toolCall?: { name: string, args: object, result: string,
//                isLive: boolean, ms: number },
//   resultType?: string,   // e.g. 'expiring_docs', 'family_brief'
//   resultData?: object,   // parsed structured data for rich renderers
//   streaming?: boolean,   // true while text is still appearing
// }
export const messages = writable([]);

export function addMessage(msg) {
  messages.update(list => [...list, { id: crypto.randomUUID(), ...msg }]);
}

export function updateLastMessage(patch) {
  messages.update(list => {
    if (!list.length) return list;
    const copy = [...list];
    copy[copy.length - 1] = { ...copy[copy.length - 1], ...patch };
    return copy;
  });
}

export function clearMessages() {
  messages.set([]);
}

// ---------- VIEW --------------------------------------------
// 'chat' | 'dashboard' | 'settings'
export const activeView = writable('chat');
