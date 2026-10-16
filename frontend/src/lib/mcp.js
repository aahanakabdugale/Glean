// ============================================================
// mcp.js — Glean MCP client
//
// Every function here calls a single MCP tool over Streamable
// HTTP (POST to /mcp with a JSON-RPC 2.0 payload).
// If the server is unreachable, it falls back to demo data
// and marks the result as isLive: false.
// ============================================================

import { get } from 'svelte/store';
import { settings, connectionStatus, addToolTrace } from './store.js';

// ---------- Low-level transport ---------------------------

let sessionId = null;

async function ensureSession() {
  if (sessionId) return sessionId;
  let { serverUrl, serverToken } = get(settings);
  if (typeof window !== 'undefined' && window.location.origin) {
    if (serverUrl.includes('localhost:8000') && window.location.origin.includes('127.0.0.1')) {
      serverUrl = `${window.location.origin}/mcp`;
    } else if (serverUrl.includes('127.0.0.1:8000') && window.location.origin.includes('localhost')) {
      serverUrl = `${window.location.origin}/mcp`;
    }
  }
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/event-stream',
  };
  if (serverToken) headers['Authorization'] = `Bearer ${serverToken}`;

  const payload = {
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'Glean-WebUI', version: '1.0' },
    },
  };

  try {
    const res = await fetch(serverUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(6000),
    });

    if (res.ok) {
      sessionId = res.headers.get('mcp-session-id');
      return sessionId;
    }
  } catch (e) {
    // Session initialization failed
  }
  return null;
}

async function callTool(toolName, toolArgs = {}) {
  let { serverUrl, serverToken } = get(settings);
  if (typeof window !== 'undefined' && window.location.origin) {
    if (serverUrl.includes('localhost:8000') && window.location.origin.includes('127.0.0.1')) {
      serverUrl = `${window.location.origin}/mcp`;
    } else if (serverUrl.includes('127.0.0.1:8000') && window.location.origin.includes('localhost')) {
      serverUrl = `${window.location.origin}/mcp`;
    }
  }
  const start = performance.now();
  let payload = null;
  let sid = null;

  try {
    sid = await ensureSession();
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/event-stream',
    };
    if (serverToken) headers['Authorization'] = `Bearer ${serverToken}`;
    if (sid) headers['mcp-session-id'] = sid;

    payload = {
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'tools/call',
      params: { name: toolName, arguments: toolArgs },
    };

    const res = await fetch(serverUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(8000),
    });

    if (!res.ok) {
      // If session expired or invalid, reset sessionId so next request re-negotiates
      if (res.status === 404 || res.status === 400 || res.status === 406) {
        sessionId = null;
      }
      throw new Error(`HTTP ${res.status}`);
    }

    const rawText = await res.text();
    let json;
    if (rawText.startsWith('event:') || rawText.includes('data:')) {
      const match = rawText.match(/data:\s*({.+})/);
      if (match) json = JSON.parse(match[1]);
      else json = JSON.parse(rawText.replace(/^data:\s*/, ''));
    } else {
      json = JSON.parse(rawText);
    }

    const ms = Math.round(performance.now() - start);

    if (json.error) throw new Error(json.error.message || 'MCP error');

    const text = json.result?.content?.map(c => c.text).join('\n') ?? '';
    connectionStatus.set('online');

    addToolTrace({
      toolName,
      toolArgs,
      isLive: true,
      ms,
      status: '200 OK',
      requestPayload: payload,
      responsePayload: json,
      rawResult: text,
      sessionId: sid,
      endpoint: serverUrl,
    });

    return { ok: true, text, ms, isLive: true };
  } catch (err) {
    const ms = Math.round(performance.now() - start);
    connectionStatus.set('offline');

    addToolTrace({
      toolName,
      toolArgs,
      isLive: false,
      ms,
      status: `Failed (${err.message})`,
      requestPayload: payload || { method: 'tools/call', name: toolName, arguments: toolArgs },
      responsePayload: { error: err.message },
      rawResult: err.message,
      sessionId: sid,
      endpoint: serverUrl,
    });

    return { ok: false, error: err.message, isLive: false };
  }
}

// ---------- Named tool wrappers ---------------------------
// Each returns { text, isLive, ms, resultType, resultData }
// resultType tells the UI which rich renderer to use.
// resultData is a parsed JS object for structured display.

export async function callFamilyBrief(memberName = '') {
  const args = memberName && memberName !== 'all' ? { member_name: memberName } : {};
  const raw = await callTool('family_brief', args);
  if (raw.ok) {
    return { ...raw, resultType: 'family_brief', resultData: parseFamilyBrief(raw.text) };
  }
  const demo = demoFamilyBrief(memberName);
  return { ok: true, text: demo.text, isLive: false, ms: 0,
           resultType: 'family_brief', resultData: demo.data };
}

export async function callGetExpiringDocuments(days = 30) {
  const raw = await callTool('get_expiring_documents', { days });
  if (raw.ok) {
    return { ...raw, resultType: 'expiring_docs', resultData: parseExpiringDocs(raw.text) };
  }
  const demo = demoExpiringDocs();
  return { ok: true, text: demo.text, isLive: false, ms: 0,
           resultType: 'expiring_docs', resultData: demo.data };
}

export async function callListUpcomingTasks(days = 30) {
  const raw = await callTool('list_upcoming_tasks', { days });
  if (raw.ok) {
    return { ...raw, resultType: 'upcoming_tasks', resultData: parseUpcomingTasks(raw.text) };
  }
  const demo = demoUpcomingTasks();
  return { ok: true, text: demo.text, isLive: false, ms: 0,
           resultType: 'upcoming_tasks', resultData: demo.data };
}

export async function callCheckSchemeEligibility(name, tags = '') {
  const raw = await callTool('check_scheme_eligibility', { name, tags });
  if (raw.ok) {
    return { ...raw, resultType: 'scheme_eligibility', resultData: parseEligibility(raw.text, name) };
  }
  const demo = demoEligibility(name);
  return { ok: true, text: demo.text, isLive: false, ms: 0,
           resultType: 'scheme_eligibility', resultData: demo.data };
}

export async function callGetSchemeChecklist(scheme) {
  const raw = await callTool('get_scheme_checklist', { scheme });
  if (raw.ok) {
    return { ...raw, resultType: 'scheme_checklist', resultData: parseChecklist(raw.text) };
  }
  const demo = demoChecklist(scheme);
  return { ok: true, text: demo.text, isLive: false, ms: 0,
           resultType: 'scheme_checklist', resultData: demo.data };
}

export async function callPlanSchemeApplication(name, scheme, days_to_prepare = 7) {
  const raw = await callTool('plan_scheme_application', { name, scheme, days_to_prepare });
  if (raw.ok) {
    return { ...raw, resultType: 'plan_application', resultData: parsePlan(raw.text) };
  }
  const demo = demoPlan(name, scheme);
  return { ok: true, text: demo.text, isLive: false, ms: 0,
           resultType: 'plan_application', resultData: demo.data };
}

export async function callListFamilyMembers() {
  const raw = await callTool('list_family_members');
  if (raw.ok) {
    return { ...raw, resultType: 'family_members', resultData: parseFamilyMembers(raw.text) };
  }
  return { ok: true, text: demoMembersText(), isLive: false, ms: 0,
           resultType: 'family_members', resultData: demoMembersData() };
}

export async function callAddFamilyMember(name, relation, birth_year, status) {
  return callTool('add_family_member', { name, relation, birth_year, status });
}

export async function callAddDocument(doc_type, owner, expiry_date) {
  return callTool('add_document', { doc_type, owner, expiry_date });
}

export async function callAddTask(title, due_date, owner = '') {
  return callTool('add_task', { title, due_date, owner });
}

export async function callGetFamilyDashboard() {
  const raw = await callTool('get_family_dashboard');
  if (raw.ok) {
    return { ...raw, resultType: 'family_dashboard', resultData: parseDashboard(raw.text) };
  }
  return {
    ok: true,
    text: demoDashboardText(),
    isLive: false,
    ms: 0,
    resultType: 'family_dashboard',
    resultData: demoDashboardData(),
  };
}

// Test connectivity — used by Settings panel
export async function testConnection() {
  const raw = await callTool('list_family_members');
  return raw.ok;
}

// ---------- Text parsers ----------------------------------
// Convert the plain-text MCP responses into structured objects
// so rich renderer components have typed data to work with.

function parseExpiringDocs(text) {
  // Lines like: "Ramesh's Passport - 2026-10-14 (URGENT, 7 days left)"
  return text.split('\n').filter(Boolean).map(line => {
    const m = line.match(/^(.+?)'s (.+?) - (\d{4}-\d{2}-\d{2}) \((.+?)\)/);
    if (!m) return { raw: line };
    const [, member, docType, expiryDate, statusText] = m;
    const daysLeft = parseInt(statusText.match(/-?\d+/)?.[0] ?? '999');
    const urgency = statusText.startsWith('EXPIRED') ? 'expired'
                  : daysLeft <= 7 ? 'urgent'
                  : daysLeft <= 14 ? 'soon'
                  : 'safe';
    return { member, docType, expiryDate, statusText, daysLeft, urgency };
  });
}

function parseUpcomingTasks(text) {
  return text.split('\n').filter(Boolean).map(line => {
    const m = line.match(/^(.+?)(?: \((.+?)\))? - (\d{4}-\d{2}-\d{2}) \((.+?)\)/);
    if (!m) return { raw: line };
    const [, title, member, dueDate, statusText] = m;
    const overdue = statusText.startsWith('OVERDUE');
    return { title, member: member || null, dueDate, statusText, overdue };
  });
}

function parseEligibility(text, personName) {
  const eligible = [], checkNeeded = [], almostEligible = [], notEligible = [];
  let section = null;
  let currentAlmost = null;
  for (const line of text.split('\n')) {
    if (line.includes('May be eligible')) { section = 'eligible'; continue; }
    if (line.includes('Requires verification')) { section = 'check'; continue; }
    if (line.includes('Coming up soon')) { section = 'almost'; continue; }
    if (line.includes('Not eligible')) { section = 'not'; continue; }
    if (line.startsWith('•')) {
      const entry = { text: line.slice(1).trim() };
      if (section === 'eligible') eligible.push(entry);
      else if (section === 'check') checkNeeded.push(entry);
      else if (section === 'almost') {
        currentAlmost = entry;
        almostEligible.push(entry);
      }
      else if (section === 'not') notEligible.push(entry);
    } else if ((line.trim().startsWith('→ Suggested:') || line.trim().startsWith('-> Suggested:')) && currentAlmost) {
      currentAlmost.suggestedTask = line.trim().replace(/^(?:→|->)\s*Suggested:\s*/, '').trim();
    }
  }
  return { personName, eligible, checkNeeded, almostEligible, notEligible };
}

function parseChecklist(text) {
  const items = [];
  let name = '', summary = '', notes = '', sourceUrl = '', applyUrl = '';
  for (const line of text.split('\n')) {
    if (line.startsWith('Document Checklist for ')) name = line.slice(23);
    else if (line.startsWith('Summary: ')) summary = line.slice(9);
    else if (line.startsWith('Notes: ')) notes = line.slice(7);
    else if (line.startsWith('Official details: ')) sourceUrl = line.slice(18);
    else if (line.startsWith('Apply online: ')) applyUrl = line.slice(14);
    else if (line.startsWith('• ')) items.push(line.slice(2));
  }
  return { name, summary, items, notes, sourceUrl, applyUrl };
}

function parsePlan(text) {
  const tasks = [], docs = [];
  let schemeName = '', status = '', portal = '';
  let inDocs = false;
  for (const line of text.split('\n')) {
    if (line.startsWith('Application plan created for ')) {
      const m = line.match(/— (.+?):/);
      if (m) schemeName = m[1];
    } else if (line.includes('Eligibility status:')) {
      status = line.replace('• Eligibility status:', '').trim();
    } else if (line.startsWith('• Task')) {
      tasks.push(line.slice(2).trim());
    } else if (line.startsWith('• Official portal:')) {
      portal = line.slice(18).trim();
    } else if (line.startsWith('Documents needed:')) {
      inDocs = true;
    } else if (inDocs && line.startsWith('  - ')) {
      docs.push(line.slice(4).trim());
    }
  }
  return { schemeName, status, tasks, portal, docs };
}

function parseFamilyBrief(text) {
  // Return raw text plus parsed sub-sections
  const expiringMatch = text.match(/Expiring Documents[^:]*: (\d+)/);
  const tasksMatch = text.match(/Upcoming Tasks[^:]*: (\d+)/);
  return {
    raw: text,
    expiringCount: expiringMatch ? parseInt(expiringMatch[1]) : 0,
    tasksCount: tasksMatch ? parseInt(tasksMatch[1]) : 0,
  };
}

function parseFamilyMembers(text) {
  return text.split('\n').filter(Boolean).map(line => {
    const m = line.match(/^(.+?) \((.+?)\) — born (\d{4}), (.+)$/);
    if (!m) return { raw: line };
    const [, name, relation, birthYear, status] = m;
    return { name, relation, birthYear: parseInt(birthYear), status };
  });
}

// ---------- Demo data (shown when server is offline) ------

function demoExpiringDocs() {
  const data = [
    { member: 'Chandler', docType: 'Passport', expiryDate: '2026-10-15', statusText: 'URGENT, 6 days left', daysLeft: 6, urgency: 'urgent' },
    { member: 'Justin',   docType: 'Motor Vehicle Insurance', expiryDate: '2026-10-21', statusText: 'URGENT, 12 days left', daysLeft: 12, urgency: 'urgent' },
    { member: 'Gwen',     docType: 'University Transit Pass', expiryDate: '2026-10-24', statusText: '15 days left', daysLeft: 15, urgency: 'soon' },
    { member: 'Amy',      docType: 'Pension Verification Certificate', expiryDate: '2026-10-27', statusText: '18 days left', daysLeft: 18, urgency: 'soon' },
    { member: 'Justin',   docType: 'Driving Licence', expiryDate: '2026-10-31', statusText: '22 days left', daysLeft: 22, urgency: 'soon' },
    { member: 'Riley',    docType: 'Health Insurance Policy', expiryDate: '2026-11-06', statusText: '28 days left', daysLeft: 28, urgency: 'soon' },
  ];
  return {
    text: data.map(d => `${d.member}'s ${d.docType} - ${d.expiryDate} (${d.statusText})`).join('\n'),
    data,
  };
}

function demoUpcomingTasks() {
  const data = [
    { title: "Renew Chandler's passport appointment", member: 'Chandler', dueDate: '2026-10-13', statusText: '4 days left', overdue: false },
    { title: 'Check Ayushman & senior benefits',     member: 'Chandler', dueDate: '2026-10-17', statusText: '8 days left', overdue: false },
  ];
  return {
    text: data.map(t => `${t.title} (${t.member}) - ${t.dueDate} (${t.statusText})`).join('\n'),
    data,
  };
}

function demoEligibility(name) {
  const eligible = [
    { text: 'Ayushman Vay Vandana Card (AB PM-JAY) — age fits the age rule. Official link: https://beneficiary.nha.gov.in' },
  ];
  const almostEligible = [
    {
      text: `${name} — ${name} is not eligible for Senior Citizens Savings Scheme today, but may qualify around 2029. Official link: https://sbi.bank.in`,
      suggestedTask: `Check eligibility for Senior Citizens Savings Scheme (around 2029)`,
    },
  ];
  const notEligible = [
    { text: 'Atal Pension Yojana (APY) — age requirement not met' },
  ];
  const text = `Eligibility check for ${name}:\n\nMay be eligible:\n${eligible.map(e => '• ' + e.text).join('\n')}\n\nComing up soon:\n${almostEligible.map(e => '• ' + e.text + '\n  → Suggested: ' + e.suggestedTask).join('\n')}\n\nNot eligible:\n${notEligible.map(e => '• ' + e.text).join('\n')}\n\nNote: Guidance only. Please verify details on official government portals.`;
  return { text, data: { personName: name, eligible, checkNeeded: [], almostEligible, notEligible } };
}

function demoChecklist(scheme) {
  return {
    text: `Document Checklist for Senior Citizens Savings Scheme (SCSS):\nSummary: Government-backed savings deposit.\n\nRequired Documents:\n• Age proof\n• Identity & address proof (PAN, voter ID, passport)\n• Passport-size photos\n\nNotes: Quarterly interest at post offices and banks.\nOfficial details: https://www.indiapost.gov.in`,
    data: {
      name: 'Senior Citizens Savings Scheme (SCSS)',
      summary: 'Government-backed savings deposit.',
      items: ['Age proof', 'Identity & address proof (PAN, voter ID, passport)', 'Passport-size photos'],
      notes: 'Quarterly interest at post offices and banks.',
      sourceUrl: 'https://www.indiapost.gov.in',
      applyUrl: '',
    },
  };
}

function demoPlan(name, scheme) {
  return {
    text: `Application plan created for ${name} — Senior Citizens Savings Scheme (SCSS):\n• Eligibility status: May Be Eligible\n• Task 1 created: Gather documents by 2026-10-15\n• Task 2 created: Submit application by 2026-10-22\n• Official portal: https://www.indiapost.gov.in\n\nDocuments needed:\n  - Age proof\n  - Identity & address proof`,
    data: {
      schemeName: 'Senior Citizens Savings Scheme (SCSS)',
      status: 'May Be Eligible',
      tasks: ['Task 1: Gather documents by 2026-10-15', 'Task 2: Submit application by 2026-10-22'],
      portal: 'https://www.indiapost.gov.in',
      docs: ['Age proof', 'Identity & address proof'],
    },
  };
}

function demoFamilyBrief(memberName = '') {
  if (memberName && memberName !== 'all') {
    const text = `Personal Briefing for ${memberName}:\n\nYour Expiring Documents (next 30 days): 1\n• Passport: 2026-10-15 (urgent (6d left))\n\nYour Upcoming Deadlines (next 14 days): 1\n• Renew passport appointment — due 2026-10-13 (4d left)\n\nGovernment Benefits You May Qualify For:\n• Ayushman Vay Vandana Card (AB PM-JAY)\n• Senior Citizens Savings Scheme (SCSS)\nAsk me 'Plan the application' or 'What documents are needed' anytime!`;
    return { text, data: { raw: text, expiringCount: 1, tasksCount: 1 } };
  }
  const text = `Family Briefing (6 family members tracked):\n\nExpiring Documents (next 30 days): 2\n• Chandler's Passport: 2026-10-15 (urgent, 6d left)\n• Justin's Driving Licence: 2026-10-29 (20d left)\n\nUpcoming Tasks (next 14 days): 1\n• Renew Chandler's passport appointment (Chandler) — due 2026-10-13 (4d left)`;
  return { text, data: { raw: text, expiringCount: 2, tasksCount: 1 } };
}

function demoMembersText() {
  return `Chandler (grandfather) — born 1950, retired\nAmy (grandmother) — born 1953, retired\nJustin (father) — born 1968, employed\nRiley (mother) — born 1972, employed\nJace (son) — born 2000, family admin\nGwen (daughter) — born 2003, family admin`;
}

function demoMembersData() {
  return [
    { name: 'Chandler', relation: 'grandfather', birthYear: 1950, status: 'retired' },
    { name: 'Amy',      relation: 'grandmother', birthYear: 1953, status: 'retired' },
    { name: 'Justin',   relation: 'father',      birthYear: 1968, status: 'employed' },
    { name: 'Riley',    relation: 'mother',      birthYear: 1972, status: 'employed' },
    { name: 'Jace',     relation: 'son',         birthYear: 2000, status: 'family admin' },
    { name: 'Gwen',     relation: 'daughter',    birthYear: 2003, status: 'family admin' },
  ];
}

function parseDashboard(text) {
  const sections = text.split('\n--- ');
  const metrics = {
    totalMembers: 0,
    totalDocs: 0,
    expiringDocs: 0,
    urgentDocs: 0,
    pendingTasks: 0,
    upcomingTasks: 0,
    overdueTasks: 0,
    schemeOpportunities: 0,
  };

  const headerMatch = text.match(/=== FAMILY ADMIN DASHBOARD \((\d+) Members Tracked\) ===/);
  if (headerMatch) metrics.totalMembers = parseInt(headerMatch[1], 10);

  const docMatch = text.match(/• Documents: (\d+) tracked \((\d+) expiring in 60d, (\d+) urgent\)/);
  if (docMatch) {
    metrics.totalDocs = parseInt(docMatch[1], 10);
    metrics.expiringDocs = parseInt(docMatch[2], 10);
    metrics.urgentDocs = parseInt(docMatch[3], 10);
  }

  const taskMatch = text.match(/• Tasks: (\d+) pending \((\d+) due in 30d, (\d+) overdue\)/);
  if (taskMatch) {
    metrics.pendingTasks = parseInt(taskMatch[1], 10);
    metrics.upcomingTasks = parseInt(taskMatch[2], 10);
    metrics.overdueTasks = parseInt(taskMatch[3], 10);
  }

  const schemeMatch = text.match(/• Scheme Opportunities: (\d+) matches identified/);
  if (schemeMatch) metrics.schemeOpportunities = parseInt(schemeMatch[1], 10);

  const members = [];
  const expiring = [];
  const tasks = [];
  const benefits = [];

  for (const sec of sections) {
    const lines = sec.split('\n').filter(Boolean);
    const title = lines[0].replace(' ---', '').trim();

    if (title === 'FAMILY ROSTER' || sec.includes('FAMILY ROSTER')) {
      for (const line of lines) {
        const m = line.match(/^• (.+?) \((.+?)\) — Born (\d+), (.+)$/);
        if (m) members.push({ name: m[1], relation: m[2], birthYear: m[3], status: m[4] });
      }
    } else if (title === 'EXPIRING DOCUMENTS' || sec.includes('EXPIRING DOCUMENTS')) {
      for (const line of lines) {
        const m = line.match(/^• (.+?)'s (.+?) — expires (\d{4}-\d{2}-\d{2}) \[(.+?)\]$/);
        if (m) {
          const status = m[4];
          const daysMatch = status.match(/-?\d+/);
          const daysLeft = daysMatch ? parseInt(daysMatch[0], 10) : null;
          expiring.push({ owner: m[1], member: m[1], docType: m[2], expiryDate: m[3], status, daysLeft });
        }
      }
    } else if (title === 'UPCOMING DEADLINES' || sec.includes('UPCOMING DEADLINES')) {
      for (const line of lines) {
        const m = line.match(/^• (.+?) — due (\d{4}-\d{2}-\d{2}) \[(.+?)\]$/);
        if (m) {
          const status = m[3];
          const daysMatch = status.match(/-?\d+/);
          const daysLeft = daysMatch ? parseInt(daysMatch[0], 10) : null;
          tasks.push({ title: m[1], dueDate: m[2], status, daysLeft });
        }
      }
    } else if (title === 'BENEFIT OPPORTUNITIES' || sec.includes('BENEFIT OPPORTUNITIES')) {
      for (const line of lines) {
        if (line.startsWith('• ')) benefits.push(line.slice(2).trim());
      }
    }
  }

  return { metrics, members, expiring, tasks, benefits, raw: text };
}

function demoDashboardData() {
  return {
    metrics: {
      totalMembers: 6,
      totalDocs: 18,
      expiringDocs: 3,
      urgentDocs: 1,
      pendingTasks: 4,
      upcomingTasks: 3,
      overdueTasks: 0,
      schemeOpportunities: 4,
    },
    members: demoMembersData(),
    expiring: [
      { owner: 'Chandler', member: 'Chandler', docType: 'Passport', expiryDate: '2026-10-21', status: 'URGENT (6d left)', daysLeft: 6 },
      { owner: 'Justin', member: 'Justin', docType: 'Motor Vehicle Insurance', expiryDate: '2026-10-27', status: '12d left', daysLeft: 12 },
      { owner: 'Gwen', member: 'Gwen', docType: 'University Transit Pass', expiryDate: '2026-10-30', status: '15d left', daysLeft: 15 },
    ],
    tasks: [
      { title: "Renew Chandler's passport appointment", member: 'Chandler', dueDate: '2026-10-19', status: '4d left', daysLeft: 4 },
      { title: "Check Ayushman & senior benefits", member: 'Chandler', dueDate: '2026-10-25', status: '10d left', daysLeft: 10 },
      { title: "Vehicle insurance renewal check", member: 'Justin', dueDate: '2026-10-29', status: '14d left', daysLeft: 14 },
    ],
    benefits: [
      "Chandler qualifies for Ayushman Vay Vandana Card (AB PM-JAY)",
      "Chandler qualifies for Senior Citizens Savings Scheme (SCSS)",
      "Amy qualifies for Ayushman Vay Vandana Card (AB PM-JAY)",
      "Amy qualifies for Senior Citizens Savings Scheme (SCSS)",
    ],
    raw: demoDashboardText(),
  };
}

function demoDashboardText() {
  return `=== FAMILY ADMIN DASHBOARD (6 Members Tracked) ===\n• Documents: 18 tracked (3 expiring in 60d, 1 urgent)\n• Tasks: 4 pending (3 due in 30d, 0 overdue)\n• Scheme Opportunities: 4 matches identified\n\n--- FAMILY ROSTER ---\n• Chandler (grandfather) — Born 1950, retired\n• Amy (grandmother) — Born 1953, retired\n• Justin (father) — Born 1968, employed\n• Riley (mother) — Born 1972, employed\n• Jace (son) — Born 2000, family admin\n• Gwen (daughter) — Born 2003, family admin\n\n--- EXPIRING DOCUMENTS ---\n• Chandler's Passport — expires 2026-10-21 [URGENT (6d left)]\n• Justin's Motor Vehicle Insurance — expires 2026-10-27 [12d left]\n• Gwen's University Transit Pass — expires 2026-10-30 [15d left]\n\n--- UPCOMING DEADLINES ---\n• Renew Chandler's passport appointment (Chandler) — due 2026-10-19 [4d left]\n• Check Ayushman & senior benefits (Chandler) — due 2026-10-25 [10d left]\n\n--- BENEFIT OPPORTUNITIES ---\n• Chandler qualifies for Ayushman Vay Vandana Card (AB PM-JAY)\n• Amy qualifies for Ayushman Vay Vandana Card (AB PM-JAY)\n\nNote: Guidance only. Verified on official portals.`;
}

