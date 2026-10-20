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

function getDefaultServerUrl() {
  if (typeof window !== 'undefined' && window.location.origin) {
    // If running in Vite dev server (port 5173), target the backend at port 8000
    if (window.location.port === '5173') {
      return `${window.location.protocol}//${window.location.hostname}:8000/mcp`;
    }
    // If running on any deployed host (e.g. *.onrender.com) or directly served by the backend
    return `${window.location.origin}/mcp`;
  }
  return 'http://localhost:8000/mcp';
}

function loadSettings() {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      // Auto-heal: If visiting on a remote origin (like Render) and stored serverUrl still points to localhost,
      // update it automatically to current origin so users aren't stuck disconnected.
      if (typeof window !== 'undefined' && window.location.origin) {
        const isRemote = !window.location.hostname.includes('localhost') && !window.location.hostname.includes('127.0.0.1');
        if (isRemote && parsed.serverUrl && (parsed.serverUrl.includes('localhost') || parsed.serverUrl.includes('127.0.0.1'))) {
          parsed.serverUrl = `${window.location.origin}/mcp`;
        }
      }
      return { ...defaultSettings(), ...parsed };
    }
  } catch {}
  return defaultSettings();
}

function defaultSettings() {
  return {
    serverUrl: getDefaultServerUrl(),
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
function initAlexaMic() {
  if (typeof localStorage !== 'undefined') {
    const saved = localStorage.getItem('glean-alexa-mic');
    return saved !== null ? saved === 'true' : true;
  }
  return true;
}

// 'idle' | 'listening' | 'thinking' | 'speaking' | 'muted'
export const orbState = writable(initAlexaMic() ? 'idle' : 'muted');

// Human-readable label shown under the orb
export const orbLabel = derived(orbState, s => ({
  idle:      'Ready',
  listening: 'Listening…',
  thinking:  'Thinking…',
  speaking:  'Speaking…',
  muted:     'Alexa Mic OFF',
}[s] ?? 'Ready'));

// ---------- ALEXA MIC (ON / OFF SWITCH) ----------------------
export const alexaMicEnabled = writable(initAlexaMic());

alexaMicEnabled.subscribe(enabled => {
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('glean-alexa-mic', String(enabled));
  }
  if (!enabled) {
    orbState.set('muted');
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  } else {
    orbState.update(s => (s === 'muted' ? 'idle' : s));
  }
});

export function toggleAlexaMic() {
  alexaMicEnabled.update(m => !m);
}

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

// ---------- ACTIVE PERSONA ("Who am I?") ----------------------
// 'all' | member name / persona label (e.g. 'Aman', 'Grandma', 'Dad', 'Ramesh')
function initPersona() {
  const saved = localStorage.getItem('glean-active-persona');
  return saved || 'all';
}

export const activePersona = writable(initPersona());

activePersona.subscribe(p => {
  localStorage.setItem('glean-active-persona', p);
});

// ---------- ACTIVE JURISDICTION ("Global / IN / US") ----------
function initJurisdiction() {
  const saved = localStorage.getItem('glean-jurisdiction');
  return saved || 'all'; // 'all' | 'IN' | 'US'
}

export const activeJurisdiction = writable(initJurisdiction());

activeJurisdiction.subscribe(j => {
  localStorage.setItem('glean-jurisdiction', j);
});


// Cache of registered family members used to populate the persona dropdown
export const familyMembersList = writable([
  { name: 'Chandler', relation: 'grandfather', birthYear: 1950, status: 'retired' },
  { name: 'Amy',      relation: 'grandmother', birthYear: 1953, status: 'retired' },
  { name: 'Justin',   relation: 'father',      birthYear: 1968, status: 'employed' },
  { name: 'Riley',    relation: 'mother',      birthYear: 1972, status: 'employed' },
  { name: 'Jace',     relation: 'son',         birthYear: 2000, status: 'family admin' },
  { name: 'Gwen',     relation: 'daughter',    birthYear: 2003, status: 'family admin' },
]);

// ---------- LIVE MCP TOOL-CALL TRACES -------------------------
export const toolCallTraces = writable([]);
export const showTracePanel = writable(false);

export function addToolTrace(trace) {
  toolCallTraces.update(list => [
    {
      id: crypto.randomUUID(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      ...trace,
    },
    ...list,
  ].slice(0, 50)); // Keep latest 50 traces
}

export function clearToolTraces() {
  toolCallTraces.set([]);
}

export function toggleTracePanel() {
  activeView.update(v => v === 'traces' ? 'chat' : 'traces');
}

// ---------- PROACTIVE AMBIENT PUSH ALERTS (SSE) -------------
export const activeAmbientAlert = writable(null);
export const ambientAlertHistory = writable([]);

export function dismissAmbientAlert() {
  activeAmbientAlert.set(null);
}

export function pushAmbientAlert(alert) {
  activeAmbientAlert.set(alert);
  ambientAlertHistory.update(list => [alert, ...list].slice(0, 20));
}

// ---------- SUGGESTED ACTIONS SIDE DRAWER -------------------
export const showSuggestedActions = writable(false);

