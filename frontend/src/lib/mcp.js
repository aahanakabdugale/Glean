// ============================================================
// mcp.js — Glean MCP client
//
// Every function here calls a single MCP tool over Streamable
// HTTP (POST to /mcp with a JSON-RPC 2.0 payload).
// If the server is unreachable, it falls back to demo data
// and marks the result as isLive: false.
// ============================================================

import { get } from 'svelte/store';
import { settings, connectionStatus } from './store.js';

// ---------- Low-level transport ---------------------------

async function callTool(toolName, toolArgs = {}) {
  const { serverUrl, serverToken } = get(settings);
  const start = performance.now();

  const headers = { 'Content-Type': 'application/json' };
  if (serverToken) headers['Authorization'] = `Bearer ${serverToken}`;

  const payload = {
    jsonrpc: '2.0',
    id: Date.now(),
    method: 'tools/call',
    params: { name: toolName, arguments: toolArgs },
  };

  try {
    const res = await fetch(serverUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(8000),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const json = await res.json();
    const ms = Math.round(performance.now() - start);

    if (json.error) throw new Error(json.error.message || 'MCP error');

    const text = json.result?.content?.map(c => c.text).join('\n') ?? '';
    connectionStatus.set('online');

    return { ok: true, text, ms, isLive: true };
  } catch (err) {
    connectionStatus.set('offline');
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
  const eligible = [], checkNeeded = [], notEligible = [];
  let section = null;
  for (const line of text.split('\n')) {
    if (line.includes('May be eligible')) { section = 'eligible'; continue; }
    if (line.includes('Requires verification')) { section = 'check'; continue; }
    if (line.includes('Not eligible')) { section = 'not'; continue; }
    if (!line.startsWith('•')) continue;
    const entry = { text: line.slice(1).trim() };
    if (section === 'eligible') eligible.push(entry);
    else if (section === 'check') checkNeeded.push(entry);
    else if (section === 'not') notEligible.push(entry);
  }
  return { personName, eligible, checkNeeded, notEligible };
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
    { text: 'Senior Citizens Savings Scheme (SCSS) — age fits the age rule. Official link: https://www.indiapost.gov.in' },
  ];
  const notEligible = [
    { text: 'Atal Pension Yojana (APY) — age requirement not met' },
  ];
  const text = `Eligibility check for ${name}:\n\nMay be eligible:\n${eligible.map(e => '• ' + e.text).join('\n')}\n\nNot eligible:\n${notEligible.map(e => '• ' + e.text).join('\n')}\n\nNote: Guidance only. Please verify details on official government portals.`;
  return { text, data: { personName: name, eligible, checkNeeded: [], notEligible } };
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
