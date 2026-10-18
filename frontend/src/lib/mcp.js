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
import {
  generateDashboardSpokenBrief,
  generateFamilyBriefSpokenBrief,
  generateExpiringDocsSpokenBrief,
  generateTasksSpokenBrief,
  generateEligibilitySpokenBrief,
  generateChecklistSpokenBrief,
  generatePlanSpokenBrief,
  generateMembersSpokenBrief
} from './speech.js';

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
    const parsed = parseFamilyBrief(raw.text);
    return {
      ...raw,
      resultType: 'family_brief',
      resultData: parsed,
      spokenText: generateFamilyBriefSpokenBrief(parsed, memberName)
    };
  }
  const demo = demoFamilyBrief(memberName);
  return {
    ok: true,
    text: demo.text,
    isLive: false,
    ms: 0,
    resultType: 'family_brief',
    resultData: demo.data,
    spokenText: generateFamilyBriefSpokenBrief(demo.data, memberName)
  };
}

export async function callGetExpiringDocuments(days = 30, memberName = '') {
  const args = { days };
  if (memberName && memberName !== 'all') args.member_name = memberName;
  const raw = await callTool('get_expiring_documents', args);
  if (raw.ok) {
    const parsed = parseExpiringDocs(raw.text);
    return {
      ...raw,
      resultType: 'expiring_docs',
      resultData: parsed,
      spokenText: generateExpiringDocsSpokenBrief(parsed, days)
    };
  }
  const demo = demoExpiringDocs();
  const filtered = memberName && memberName !== 'all'
    ? demo.data.filter(d => d.member.toLowerCase() === memberName.toLowerCase())
    : demo.data;
  return {
    ok: true,
    text: demo.text,
    isLive: false,
    ms: 0,
    resultType: 'expiring_docs',
    resultData: filtered,
    spokenText: generateExpiringDocsSpokenBrief(filtered, days)
  };
}

export async function callListUpcomingTasks(days = 30, memberName = '') {
  const args = { days };
  if (memberName && memberName !== 'all') args.member_name = memberName;
  const raw = await callTool('list_upcoming_tasks', args);
  if (raw.ok) {
    const parsed = parseUpcomingTasks(raw.text);
    return {
      ...raw,
      resultType: 'upcoming_tasks',
      resultData: parsed,
      spokenText: generateTasksSpokenBrief(parsed, days)
    };
  }
  const demo = demoUpcomingTasks();
  const filtered = memberName && memberName !== 'all'
    ? demo.data.filter(t => (t.member || '').toLowerCase() === memberName.toLowerCase())
    : demo.data;
  return {
    ok: true,
    text: demo.text,
    isLive: false,
    ms: 0,
    resultType: 'upcoming_tasks',
    resultData: filtered,
    spokenText: generateTasksSpokenBrief(filtered, days)
  };
}

export async function callCheckSchemeEligibility(name, tags = '', country = '') {
  const args = { name, tags };
  if (country && country !== 'all') {
    args.country = country;
  }
  const raw = await callTool('check_scheme_eligibility', args);
  if (raw.ok) {
    const parsed = parseEligibility(raw.text, name);
    return {
      ...raw,
      resultType: 'scheme_eligibility',
      resultData: parsed,
      spokenText: generateEligibilitySpokenBrief(parsed, name)
    };
  }
  const demo = demoEligibility(name);
  return {
    ok: true,
    text: demo.text,
    isLive: false,
    ms: 0,
    resultType: 'scheme_eligibility',
    resultData: demo.data,
    spokenText: generateEligibilitySpokenBrief(demo.data, name)
  };
}


export async function callGetSchemeChecklist(scheme) {
  const raw = await callTool('get_scheme_checklist', { scheme });
  if (raw.ok) {
    const parsed = parseChecklist(raw.text);
    return {
      ...raw,
      resultType: 'scheme_checklist',
      resultData: parsed,
      spokenText: generateChecklistSpokenBrief(parsed)
    };
  }
  const demo = demoChecklist(scheme);
  return {
    ok: true,
    text: demo.text,
    isLive: false,
    ms: 0,
    resultType: 'scheme_checklist',
    resultData: demo.data,
    spokenText: generateChecklistSpokenBrief(demo.data)
  };
}

export async function callPlanSchemeApplication(name, scheme, days_to_prepare = 7) {
  const raw = await callTool('plan_scheme_application', { name, scheme, days_to_prepare });
  if (raw.ok) {
    const parsed = parsePlan(raw.text);
    return {
      ...raw,
      resultType: 'plan_application',
      resultData: parsed,
      spokenText: generatePlanSpokenBrief(parsed, name, scheme)
    };
  }
  const demo = demoPlan(name, scheme);
  return {
    ok: true,
    text: demo.text,
    isLive: false,
    ms: 0,
    resultType: 'plan_application',
    resultData: demo.data,
    spokenText: generatePlanSpokenBrief(demo.data, name, scheme)
  };
}

export async function callListFamilyMembers() {
  const raw = await callTool('list_family_members');
  if (raw.ok) {
    const parsed = parseFamilyMembers(raw.text);
    return {
      ...raw,
      resultType: 'family_members',
      resultData: parsed,
      spokenText: generateMembersSpokenBrief(parsed)
    };
  }
  const demoData = demoMembersData();
  return {
    ok: true,
    text: demoMembersText(),
    isLive: false,
    ms: 0,
    resultType: 'family_members',
    resultData: demoData,
    spokenText: generateMembersSpokenBrief(demoData)
  };
}

export async function callAddFamilyMember(name, relation, birth_year, status) {
  return callTool('add_family_member', { name, relation, birth_year, status });
}

export async function callRemoveFamilyMember(name) {
  return callTool('remove_family_member', { name });
}

export async function callResetFamilyRoster() {
  return callTool('reset_family_roster', {});
}

export async function callAddDocument(doc_type, owner, expiry_date) {
  return callTool('add_document', { doc_type, owner, expiry_date });
}

export async function callAddTask(title, due_date, owner = '') {
  return callTool('add_task', { title, due_date, owner });
}

export async function callCompleteTask(taskTitle = '', memberName = '', taskId = 0) {
  const args = {};
  if (taskTitle) args.task_title = taskTitle;
  if (memberName && memberName !== 'all') args.member_name = memberName;
  if (taskId) args.task_id = taskId;
  const raw = await callTool('complete_task', args);
  if (raw.ok) {
    return {
      ...raw,
      spokenText: raw.text || 'Task completed.'
    };
  }
  const who = memberName && memberName !== 'all' ? ` for ${memberName}` : '';
  const text = `Completed: '${taskTitle || 'Task'}'${who}.`;
  return {
    ok: true,
    text,
    isLive: false,
    ms: 0,
    spokenText: text
  };
}

export async function callOrchestrateLifeEvent(memberName, eventType, notes = '') {
  const raw = await callTool('orchestrate_life_event', { member_name: memberName, event_type: eventType, notes });
  if (raw.ok) {
    const parsed = parseLifeEvent(raw.text);
    if (memberName) parsed.memberName = memberName;
    return { ...raw, resultType: 'life_event', resultData: parsed, spokenText: parsed.spokenBrief || raw.text };
  }
  const demo = demoLifeEvent(memberName, eventType);
  return { ok: true, text: demo.text, isLive: false, ms: 0, resultType: 'life_event', resultData: demo.data, spokenText: demo.data.spokenBrief };
}

export async function callAuditDocumentDependencies(memberName = '') {
  const raw = await callTool('audit_document_dependencies', { member_name: memberName });
  if (raw.ok) {
    const parsed = parseAuditDependencies(raw.text);
    if (memberName) parsed.memberName = memberName;
    return { ...raw, resultType: 'dependency_audit', resultData: parsed, spokenText: parsed.spokenBrief || raw.text };
  }
  const demo = demoAuditDependencies(memberName);
  return { ok: true, text: demo.text, isLive: false, ms: 0, resultType: 'dependency_audit', resultData: demo.data, spokenText: demo.data.spokenBrief };
}

export async function callSimulateBureaucraticConflicts(memberName = '', targetSchemes = '') {
  const raw = await callTool('simulate_bureaucratic_conflicts', { member_name: memberName, target_schemes: targetSchemes });
  if (raw.ok) {
    const parsed = parseBureaucraticConflicts(raw.text);
    if (memberName) parsed.memberName = memberName;
    return { ...raw, resultType: 'bureaucratic_conflicts', resultData: parsed, spokenText: parsed.spokenBrief || raw.text };
  }
  const demo = demoBureaucraticConflicts(memberName);
  return { ok: true, text: demo.text, isLive: false, ms: 0, resultType: 'bureaucratic_conflicts', resultData: demo.data, spokenText: demo.data.spokenBrief };
}

export async function callTriggerProactiveAmbientAlert(memberName = '', customMessage = '') {
  return callTool('trigger_proactive_ambient_alert', { member_name: memberName, custom_message: customMessage });
}

export async function callExplainForGeneration(schemeId = 'scss', targetPersona = 'grandparent') {
  const raw = await callTool('explain_for_generation', { scheme_id: schemeId, target_persona: targetPersona });
  if (raw.ok) {
    const parsed = parseExplainGeneration(raw.text);
    return { ...raw, resultType: 'explain_generation', resultData: parsed, spokenText: parsed.spokenBrief || raw.text };
  }
  const demo = demoExplainGeneration(schemeId, targetPersona);
  return { ok: true, text: demo.text, isLive: false, ms: 0, resultType: 'explain_generation', resultData: demo.data, spokenText: demo.data.spokenBrief };
}

export function initAmbientSSE(onAlert) {
  if (typeof window === 'undefined' || !window.EventSource) return null;
  try {
    const es = new EventSource('/api/ambient/events');
    es.addEventListener('ambient_alert', (e) => {
      try {
        const data = JSON.parse(e.data);
        if (onAlert) onAlert(data);
      } catch (err) {
        console.error('Failed to parse ambient alert SSE', err);
      }
    });
    return es;
  } catch (err) {
    console.warn('Ambient SSE connection failed:', err);
    return null;
  }
}

export async function callGetFamilyDashboard() {
  const raw = await callTool('get_family_dashboard');
  if (raw.ok) {
    const parsed = parseDashboard(raw.text);
    return {
      ...raw,
      resultType: 'family_dashboard',
      resultData: parsed,
      spokenText: generateDashboardSpokenBrief(parsed)
    };
  }
  const demoData = demoDashboardData();
  return {
    ok: true,
    text: demoDashboardText(),
    isLive: false,
    ms: 0,
    resultType: 'family_dashboard',
    resultData: demoData,
    spokenText: generateDashboardSpokenBrief(demoData),
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
  const seen = new Set();
  const tasks = [];
  for (const line of text.split('\n').filter(Boolean)) {
    const m = line.match(/^(.+?)(?: \((.+?)\))? - (\d{4}-\d{2}-\d{2}) \((.+?)\)/);
    if (!m) {
      tasks.push({ raw: line });
      continue;
    }
    const [, title, member, dueDate, statusText] = m;
    const key = `${title.trim().toLowerCase()}_${(member || '').trim().toLowerCase()}`;
    if (!seen.has(key)) {
      seen.add(key);
      const overdue = statusText.startsWith('OVERDUE');
      tasks.push({ title, member: member || null, dueDate, statusText, overdue });
    }
  }
  return tasks;
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
  const expiringMatch = text.match(/(?:Expiring Documents|Your Expiring Documents)[^:]*: (\d+)/i);
  const tasksMatch = text.match(/(?:Upcoming Tasks|Upcoming Deadlines|Your Upcoming Tasks|Your Upcoming Deadlines)[^:]*: (\d+)/i);
  return {
    raw: text,
    expiringCount: expiringMatch ? parseInt(expiringMatch[1], 10) : 0,
    tasksCount: tasksMatch ? parseInt(tasksMatch[1], 10) : 0,
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

function getIsoDate(daysOffset) {
  const d = new Date();
  d.setDate(d.getDate() + daysOffset);
  return d.toISOString().split('T')[0];
}

function demoExpiringDocs() {
  const data = [
    { member: 'Chandler', docType: 'Passport', expiryDate: getIsoDate(6), statusText: 'URGENT, 6 days left', daysLeft: 6, urgency: 'urgent' },
    { member: 'Justin',   docType: 'Motor Vehicle Insurance', expiryDate: getIsoDate(12), statusText: 'URGENT, 12 days left', daysLeft: 12, urgency: 'urgent' },
    { member: 'Gwen',     docType: 'University Transit Pass', expiryDate: getIsoDate(15), statusText: '15 days left', daysLeft: 15, urgency: 'soon' },
    { member: 'Amy',      docType: 'Pension Verification Certificate', expiryDate: getIsoDate(18), statusText: '18 days left', daysLeft: 18, urgency: 'soon' },
    { member: 'Justin',   docType: 'Driving Licence', expiryDate: getIsoDate(22), statusText: '22 days left', daysLeft: 22, urgency: 'soon' },
    { member: 'Riley',    docType: 'Health Insurance Policy', expiryDate: getIsoDate(28), statusText: '28 days left', daysLeft: 28, urgency: 'soon' },
  ];
  return {
    text: data.map(d => `${d.member}'s ${d.docType} - ${d.expiryDate} (${d.statusText})`).join('\n'),
    data,
  };
}

function demoUpcomingTasks() {
  const data = [
    { title: "Renew Chandler's passport appointment", member: 'Chandler', dueDate: getIsoDate(4), statusText: '4 days left', overdue: false },
    { title: 'Check Ayushman & senior benefits',     member: 'Chandler', dueDate: getIsoDate(10), statusText: '10 days left', overdue: false },
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
  const d1 = getIsoDate(2);
  const d2 = getIsoDate(9);
  return {
    text: `Application plan created for ${name} — Senior Citizens Savings Scheme (SCSS):\n• Eligibility status: May Be Eligible\n• Task 1 created: Gather documents by ${d1}\n• Task 2 created: Submit application by ${d2}\n• Official portal: https://www.indiapost.gov.in\n\nDocuments needed:\n  - Age proof\n  - Identity & address proof`,
    data: {
      schemeName: 'Senior Citizens Savings Scheme (SCSS)',
      status: 'May Be Eligible',
      tasks: [`Task 1: Gather documents by ${d1}`, `Task 2: Submit application by ${d2}`],
      portal: 'https://www.indiapost.gov.in',
      docs: ['Age proof', 'Identity & address proof'],
    },
  };
}

function demoFamilyBrief(memberName = '') {
  const pExp = getIsoDate(6);
  const pDue = getIsoDate(4);
  const jExp = getIsoDate(22);
  if (memberName && memberName !== 'all') {
    const text = `Personal Briefing for ${memberName}:\n\nYour Expiring Documents (next 30 days): 1\n• Passport: ${pExp} (urgent (6d left))\n\nYour Upcoming Deadlines (next 14 days): 1\n• Renew passport appointment — due ${pDue} (4d left)\n\nGovernment Benefits You May Qualify For:\n• Ayushman Vay Vandana Card (AB PM-JAY)\n• Senior Citizens Savings Scheme (SCSS)\nAsk me 'Plan the application' or 'What documents are needed' anytime!`;
    return { text, data: { raw: text, expiringCount: 1, tasksCount: 1 } };
  }
  const text = `Family Briefing (6 family members tracked):\n\nExpiring Documents (next 30 days): 2\n• Chandler's Passport: ${pExp} (urgent, 6d left)\n• Justin's Driving Licence: ${jExp} (22d left)\n\nUpcoming Tasks (next 14 days): 1\n• Renew Chandler's passport appointment (Chandler) — due ${pDue} (4d left)`;
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
      const seenTasks = new Set();
      for (const line of lines) {
        const m = line.match(/^• (.+?) — due (\d{4}-\d{2}-\d{2}) \[(.+?)\]$/);
        if (m) {
          const rawTitle = m[1].trim();
          const key = rawTitle.toLowerCase();
          if (!seenTasks.has(key)) {
            seenTasks.add(key);
            const status = m[3];
            const daysMatch = status.match(/-?\d+/);
            const daysLeft = daysMatch ? parseInt(daysMatch[0], 10) : null;
            tasks.push({ title: rawTitle, dueDate: m[2], status, daysLeft });
          }
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
  const pExp = getIsoDate(6);
  const jIns = getIsoDate(12);
  const gPass = getIsoDate(15);
  const t1 = getIsoDate(4);
  const t2 = getIsoDate(10);
  const t3 = getIsoDate(14);
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
      { owner: 'Chandler', member: 'Chandler', docType: 'Passport', expiryDate: pExp, status: 'URGENT (6d left)', daysLeft: 6 },
      { owner: 'Justin', member: 'Justin', docType: 'Motor Vehicle Insurance', expiryDate: jIns, status: '12d left', daysLeft: 12 },
      { owner: 'Gwen', member: 'Gwen', docType: 'University Transit Pass', expiryDate: gPass, status: '15d left', daysLeft: 15 },
    ],
    tasks: [
      { title: "Renew Chandler's passport appointment", member: 'Chandler', dueDate: t1, status: '4d left', daysLeft: 4 },
      { title: "Check Ayushman & senior benefits", member: 'Chandler', dueDate: t2, status: '10d left', daysLeft: 10 },
      { title: "Vehicle insurance renewal check", member: 'Justin', dueDate: t3, status: '14d left', daysLeft: 14 },
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
  const pExp = getIsoDate(6);
  const jIns = getIsoDate(12);
  const gPass = getIsoDate(15);
  const t1 = getIsoDate(4);
  const t2 = getIsoDate(10);
  return `=== FAMILY ADMIN DASHBOARD (6 Members Tracked) ===\n• Documents: 18 tracked (3 expiring in 60d, 1 urgent)\n• Tasks: 4 pending (3 due in 30d, 0 overdue)\n• Scheme Opportunities: 4 matches identified\n\n--- FAMILY ROSTER ---\n• Chandler (grandfather) — Born 1950, retired\n• Amy (grandmother) — Born 1953, retired\n• Justin (father) — Born 1968, employed\n• Riley (mother) — Born 1972, employed\n• Jace (son) — Born 2000, family admin\n• Gwen (daughter) — Born 2003, family admin\n\n--- EXPIRING DOCUMENTS ---\n• Chandler's Passport — expires ${pExp} [URGENT (6d left)]\n• Justin's Motor Vehicle Insurance — expires ${jIns} [12d left]\n• Gwen's University Transit Pass — expires ${gPass} [15d left]\n\n--- UPCOMING DEADLINES ---\n• Renew Chandler's passport appointment (Chandler) — due ${t1} [4d left]\n• Check Ayushman & senior benefits (Chandler) — due ${t2} [10d left]\n\n--- BENEFIT OPPORTUNITIES ---\n• Chandler qualifies for Ayushman Vay Vandana Card (AB PM-JAY)\n• Amy qualifies for Ayushman Vay Vandana Card (AB PM-JAY)\n\nNote: Guidance only. Verified on official portals.`;
}

// ---------- Parsers for Interactive Pipeline DAGs ----------

function parseAuditDependencies(text) {
  let totalAudited = 6, criticalBlockers = 0, impendingRisks = 1;
  const auditMatch = text.match(/Audited:\s*(\d+)\s*Member\(s\)\s*\|\s*🚨\s*(\d+)\s*Critical Blocker\(s\)\s*\|\s*⚠️\s*(\d+)\s*Impending Risk\(s\)/i);
  if (auditMatch) {
    totalAudited = parseInt(auditMatch[1], 10);
    criticalBlockers = parseInt(auditMatch[2], 10);
    impendingRisks = parseInt(auditMatch[3], 10);
  }

  const members = [];
  const memberBlocks = text.split(/(?=[🚨⚠️✅]\s*\*\*[^*]+\*\*)/g);

  for (const block of memberBlocks) {
    const headerMatch = block.match(/^([🚨⚠️✅])\s*\*\*([^*]+)\*\*\s*\(([^,]+),\s*born\s*(\d{4})\):/);
    if (!headerMatch) continue;

    const [, icon, name, relation, birthYear] = headerMatch;
    const blockers = [];
    const risks = [];
    const ready = [];

    for (const line of block.split('\n')) {
      const bMatch = line.match(/BLOCKER:\s*(.+?)\s*expired\s*(\d+)d\s*ago\s*\(([^)]+)\)\s*(?:➔|->)\s*blocks\s*(.+)/i);
      if (bMatch) {
        blockers.push({ doc: bMatch[1].trim(), daysAgo: parseInt(bMatch[2], 10), expiry: bMatch[3].trim(), blockedScheme: bMatch[4].trim() });
      }

      const rMatch = line.match(/RISK:\s*(.+?)\s*expires\s*in\s*(\d+)d\s*\(([^)]+)\)\s*(?:➔|->)\s*jeopardizes\s*(.+)/i);
      if (rMatch) {
        risks.push({ doc: rMatch[1].trim(), daysLeft: parseInt(rMatch[2], 10), expiry: rMatch[3].trim(), atRiskScheme: rMatch[4].trim() });
      }

      const readyMatch = line.match(/READY:\s*All prerequisite docs valid for\s*(.+)/i);
      if (readyMatch) {
        ready.push(readyMatch[1].trim());
      }
    }

    let status = 'ok';
    if (blockers.length > 0 || icon === '🚨') status = 'urgent';
    else if (risks.length > 0 || icon === '⚠️') status = 'risk';

    members.push({
      name: name.trim(),
      relation: relation.trim(),
      birthYear: parseInt(birthYear, 10),
      status,
      blockers,
      risks,
      ready,
    });
  }

  // Critical path steps
  const criticalPath = [];
  const pathMatches = text.matchAll(/•\s*Step\s*(\d+)\s*\[([^\]]+)\]:\s*(.+)/g);
  for (const m of pathMatches) {
    criticalPath.push({ step: parseInt(m[1], 10), level: m[2], text: m[3].trim() });
  }

  // Spoken brief extraction
  let spokenBrief = '';
  const spokenMatch = text.match(/--- SPOKEN BRIEF \(ALEXA READY\) ---\s*\n"([^"]+)"/);
  if (spokenMatch) spokenBrief = spokenMatch[1];

  return { totalAudited, criticalBlockers, impendingRisks, members, criticalPath, spokenBrief, raw: text };
}

function parseBureaucraticConflicts(text) {
  let totalConflicts = 4, protectedValueInr = 1048000;
  const countMatch = text.match(/\|\s*⚠️\s*(\d+)\s*Bureaucratic Conflict/i);
  if (countMatch) totalConflicts = parseInt(countMatch[1], 10);

  const valMatch = text.match(/Safeguarded:\s*₹([\d,]+)\s*INR/i);
  if (valMatch) protectedValueInr = parseInt(valMatch[1].replace(/,/g, ''), 10);

  const conflicts = [];
  const conflictBlocks = text.split(/\n(?=\d+\.\s*\[)/);

  for (const block of conflictBlocks) {
    const headMatch = block.match(/^\d+\.\s*\[([^\]]+)\]\s*(.+)/);
    if (!headMatch) continue;

    const severity = headMatch[1].trim();
    const type = headMatch[2].trim();
    const affected = block.match(/•\s*Affected:\s*(.+)/)?.[1]?.trim() || '';
    const schemes = block.match(/•\s*Conflicting Programs:\s*(.+)/)?.[1]?.trim() || '';
    const clause = block.match(/•\s*Governing Rule:\s*(.+)/)?.[1]?.trim() || '';
    const risk = block.match(/•\s*Scrutiny Risk:\s*(.+)/)?.[1]?.trim() || '';

    conflicts.push({ severity, type, parties: affected, schemes, clause, risk });
  }

  const restructuringSteps = [];
  const stepsMatch = text.matchAll(/•\s*Step\s*\d+:\s*(.+)/g);
  for (const m of stepsMatch) {
    restructuringSteps.push(m[1].trim());
  }

  let spokenBrief = '';
  const spokenMatch = text.match(/--- SPOKEN BRIEF \(ALEXA READY\) ---\s*\n"([^"]+)"/);
  if (spokenMatch) spokenBrief = spokenMatch[1];

  return { totalConflicts, protectedValueInr, conflicts, restructuringSteps, spokenBrief, raw: text };
}

function parseExplainGeneration(text) {
  const schemeName = text.match(/Scheme:\s*(.+)/)?.[1]?.trim() || 'Senior Citizens Savings Scheme [scss]';
  const targetPersona = text.match(/Target Persona:\s*(.+)/)?.[1]?.trim() || 'Grandparent (Senior Citizen)';
  const toneLabel = text.match(/Cognitive Mode:\s*(.+)/)?.[1]?.trim() || 'Warm & Reassuring (Zero Bureaucracy)';
  
  let speech = '';
  const speechMatch = text.match(/--- ALEXA SPOKEN EXPLANATION ---\s*\n"([^"]+)"/);
  if (speechMatch) speech = speechMatch[1];

  let analogy = '';
  const analogyMatch = text.match(/--- GENERATIONAL ANALOGY ---\s*\n💡\s*(.+)/);
  if (analogyMatch) analogy = analogyMatch[1];

  const readability = text.match(/•\s*Readability:\s*(.+)/)?.[1]?.trim() || 'Grade 4 (Gentle Conversational)';
  const jargonIndex = text.match(/•\s*Bureaucracy Jargon Index:\s*(.+)/)?.[1]?.trim() || '0%';
  const score = parseInt(text.match(/•\s*Empathetic Alignment Score:\s*(\d+)/)?.[1] || '98', 10);

  let personaKey = 'grandparent';
  const low = targetPersona.toLowerCase();
  if (low.includes('student') || low.includes('young')) personaKey = 'young_adult';
  else if (low.includes('parent') || low.includes('working')) personaKey = 'parent';

  return {
    schemeName,
    personaKey,
    personaLabel: targetPersona,
    toneLabel,
    speech,
    analogy,
    readability,
    jargonIndex,
    score,
    spokenBrief: speech,
    raw: text
  };
}

function parseLifeEvent(text) {
  const title = text.match(/Life-Event Roadmap Orchestrated:\s*(.+)/)?.[1]?.trim() || 'Retirement & Senior Transition for Justin';
  const memberLine = text.match(/•\s*Member:\s*([^(]+)\s*\(([^)]+)\)\s*\|\s*Born\s*(\d{4})[^|]*\|\s*Status:\s*(.+)/);
  
  const memberName = memberLine ? memberLine[1].trim() : 'Justin';
  const relation = memberLine ? memberLine[2].trim() : 'father';
  const birthYear = memberLine ? parseInt(memberLine[3], 10) : 1968;
  const statusTransition = memberLine ? memberLine[4].trim() : 'Employed ➔ Retired Senior';

  const unlockedSchemes = [];
  const schemeMatches = text.matchAll(/•\s*\[([^\]]+)\]\s*([^—\n]+)(?:—\s*(.+))?/g);
  for (const sm of schemeMatches) {
    unlockedSchemes.push({ status: sm[1].trim(), name: sm[2].trim(), detail: sm[3] ? sm[3].trim() : '' });
  }

  const vaultDocs = [];
  const vaultMatch = text.match(/•\s*In Vault:\s*(.+)/);
  if (vaultMatch && !vaultMatch[1].includes('None')) {
    vaultDocs.push(...vaultMatch[1].split(',').map(s => s.trim()));
  }

  const missingDocs = [];
  const missingMatch = text.match(/•\s*Action Required \(Missing\):\s*(.+)/);
  if (missingMatch) {
    missingDocs.push(...missingMatch[1].split(',').map(s => s.trim()));
  }

  const phases = [];
  const phaseMatches = text.matchAll(/•\s*Day\s*\+(\d+)\s*\(([^)]+)\):\s*(.+)/g);
  for (const pm of phaseMatches) {
    phases.push({ dayOffset: parseInt(pm[1], 10), dueDate: pm[2].trim(), task: pm[3].trim() });
  }

  return {
    title,
    memberName,
    relation,
    birthYear,
    statusTransition,
    unlockedSchemes,
    vaultDocs,
    missingDocs,
    phases,
    spokenBrief: `I've prepared a phased retirement roadmap for ${memberName} with ${phases.length} scheduled milestone tasks.`,
    raw: text
  };
}

// Fallback demo fixtures for offline mode
function demoAuditDependencies(memberName = '') {
  const norm = (memberName || '').trim().toLowerCase();

  if (norm === 'jace') {
    const data = {
      totalAudited: 1,
      criticalBlockers: 0,
      impendingRisks: 0,
      members: [
        { name: 'Jace', relation: 'son', birthYear: 2000, status: 'ok', blockers: [], risks: [], ready: ['Digital Vault Verified'] }
      ],
      criticalPath: [
        { step: 1, level: 'READY', text: "All documents for Jace (Passport, Driving Licence, Term Insurance) are healthy and fully compliant with target schemes." }
      ],
      spokenBrief: "All documents for Jace are healthy and fully compliant with 0 blockers."
    };
    return { text: "=== DOCUMENT DEPENDENCY & BOTTLENECK AUDIT ===\nAudited: 1 Member(s) | 🚨 0 Critical Blocker(s) | ⚠️ 0 Impending Risk(s)\n\n✅ **Jace** (son, born 2000):\n   • No active scheme dependency blockers.\n\n• All documents are healthy and fully compliant with target schemes.", data };
  }

  if (norm === 'amy') {
    const data = {
      totalAudited: 1,
      criticalBlockers: 0,
      impendingRisks: 1,
      members: [
        {
          name: 'Amy', relation: 'grandmother', birthYear: 1953, status: 'risk', blockers: [],
          risks: [{ doc: 'Pension Life Verification Certificate', daysLeft: 18, expiry: getIsoDate(18), atRiskScheme: 'Pension Disbursement & Senior Concessions' }],
          ready: ['Ayushman Vay Vandana Card (AB PM-JAY)']
        }
      ],
      criticalPath: [
        { step: 1, level: 'HIGH', text: "Schedule renewal for Amy's Pension Life Verification Certificate (18d left). Prevents bottleneck in Pension Disbursement." }
      ],
      spokenBrief: "Heads up: Amy's Pension Life Verification Certificate expires in 18 days. Submit life verification soon."
    };
    return { text: "=== DOCUMENT DEPENDENCY & BOTTLENECK AUDIT ===\nAudited: 1 Member(s) | 🚨 0 Critical Blocker(s) | ⚠️ 1 Impending Risk(s)\n\n⚠️ **Amy** (grandmother, born 1953):\n   • ⚠️ RISK: Pension Life Verification Certificate expires in 18d ➔ jeopardizes Pension Disbursement", data };
  }

  if (norm === 'justin') {
    const data = {
      totalAudited: 1,
      criticalBlockers: 0,
      impendingRisks: 1,
      members: [
        {
          name: 'Justin', relation: 'father', birthYear: 1968, status: 'risk', blockers: [],
          risks: [{ doc: 'Motor Vehicle Comprehensive Insurance', daysLeft: 12, expiry: getIsoDate(12), atRiskScheme: 'Vehicle Registration & Active Cover' }],
          ready: ['Senior Citizens Savings Scheme']
        }
      ],
      criticalPath: [
        { step: 1, level: 'HIGH', text: "Schedule renewal for Justin's Motor Vehicle Comprehensive Insurance (12d left). Maintains active road compliance." }
      ],
      spokenBrief: "Heads up: Justin's Motor Vehicle Comprehensive Insurance expires in 12 days."
    };
    return { text: "=== DOCUMENT DEPENDENCY & BOTTLENECK AUDIT ===\nAudited: 1 Member(s) | 🚨 0 Critical Blocker(s) | ⚠️ 1 Impending Risk(s)\n\n⚠️ **Justin** (father, born 1968):\n   • ⚠️ RISK: Motor Vehicle Comprehensive Insurance expires in 12d ➔ jeopardizes Active Cover", data };
  }

  if (norm === 'riley') {
    const data = {
      totalAudited: 1,
      criticalBlockers: 0,
      impendingRisks: 1,
      members: [
        {
          name: 'Riley', relation: 'mother', birthYear: 1972, status: 'risk', blockers: [],
          risks: [{ doc: 'Health Insurance Policy', daysLeft: 28, expiry: getIsoDate(28), atRiskScheme: 'Family Cashless Health Cover' }],
          ready: []
        }
      ],
      criticalPath: [
        { step: 1, level: 'HIGH', text: "Schedule renewal for Riley's Health Insurance Policy (28d left). Protects family cashless hospital cover." }
      ],
      spokenBrief: "Heads up: Riley's Health Insurance Policy expires in 28 days."
    };
    return { text: "=== DOCUMENT DEPENDENCY & BOTTLENECK AUDIT ===\nAudited: 1 Member(s) | 🚨 0 Critical Blocker(s) | ⚠️ 1 Impending Risk(s)\n\n⚠️ **Riley** (mother, born 1972):\n   • ⚠️ RISK: Health Insurance Policy expires in 28d ➔ jeopardizes Cashless Cover", data };
  }

  if (norm === 'gwen') {
    const data = {
      totalAudited: 1,
      criticalBlockers: 0,
      impendingRisks: 1,
      members: [
        {
          name: 'Gwen', relation: 'daughter', birthYear: 2003, status: 'risk', blockers: [],
          risks: [{ doc: 'University Transit Pass', daysLeft: 15, expiry: getIsoDate(15), atRiskScheme: 'Student Transit Concession Pass' }],
          ready: ['DigiLocker Student Vault']
        }
      ],
      criticalPath: [
        { step: 1, level: 'HIGH', text: "Schedule renewal for Gwen's University Transit Pass (15d left). Prevents disruption in student concession fares." }
      ],
      spokenBrief: "Heads up: Gwen's University Transit Pass expires in 15 days."
    };
    return { text: "=== DOCUMENT DEPENDENCY & BOTTLENECK AUDIT ===\nAudited: 1 Member(s) | 🚨 0 Critical Blocker(s) | ⚠️ 1 Impending Risk(s)\n\n⚠️ **Gwen** (daughter, born 2003):\n   • ⚠️ RISK: University Transit Pass expires in 15d ➔ jeopardizes Student Concession Pass", data };
  }

  // Chandler (default)
  const data = {
    totalAudited: 6,
    criticalBlockers: 0,
    impendingRisks: 1,
    members: [
      { name: 'Chandler', relation: 'grandfather', birthYear: 1950, status: 'risk', blockers: [], risks: [{ doc: 'Passport', daysLeft: 6, expiry: getIsoDate(6), atRiskScheme: 'Ayushman Vay Vandana Card (AB PM-JAY)' }, { doc: 'Passport', daysLeft: 6, expiry: getIsoDate(6), atRiskScheme: 'Senior Citizens Savings Scheme' }], ready: [] },
      { name: 'Amy', relation: 'grandmother', birthYear: 1953, status: 'ok', blockers: [], risks: [], ready: [] },
      { name: 'Justin', relation: 'father', birthYear: 1968, status: 'ok', blockers: [], risks: [], ready: ['Senior Citizens Savings Scheme'] },
      { name: 'Riley', relation: 'mother', birthYear: 1972, status: 'ok', blockers: [], risks: [], ready: [] },
      { name: 'Jace', relation: 'son', birthYear: 2000, status: 'ok', blockers: [], risks: [], ready: [] },
      { name: 'Gwen', relation: 'daughter', birthYear: 2003, status: 'ok', blockers: [], risks: [], ready: [] },
    ],
    criticalPath: [
      { step: 1, level: 'HIGH', text: "Schedule renewal for Chandler's Passport (6d left). Prevents bottleneck in Senior Citizens Savings Scheme and Ayushman Vay Vandana Card." }
    ],
    spokenBrief: "Heads up: Chandler's Passport expires in 6 days. Renewing it soon will protect your Ayushman Vay Vandana Card application."
  };
  return { text: "=== DOCUMENT DEPENDENCY & BOTTLENECK AUDIT ===\nAudited: 6 Member(s) | 🚨 0 Critical Blocker(s) | ⚠️ 1 Impending Risk(s)", data };
}

function demoBureaucraticConflicts(memberName = '') {
  const norm = (memberName || '').trim().toLowerCase();

  if (norm === 'jace' || norm === 'gwen' || norm === 'justin' || norm === 'riley') {
    const capName = norm.charAt(0).toUpperCase() + norm.slice(1);
    const data = {
      totalConflicts: 0,
      protectedValueInr: 0,
      conflicts: [],
      restructuringSteps: [
        `Maintain current application profile for ${capName}. Zero mutual exclusivity violations or statutory tax disqualifiers detected.`
      ],
      spokenBrief: `Great news: ${capName}'s profile has zero bureaucratic conflicts or quota violations. Everything is clear to submit.`
    };
    return { text: `=== BUREAUCRATIC CONFLICT & RED-TAPE SIMULATION ===\nStatus: ✅ CLEAN SCRUTINY PATH (0 CONFLICTS)\nAudited: 1 Family Member(s) | ⚠️ 0 Bureaucratic Conflict(s) Identified\nEstimated Financial Entitlement Safeguarded: ₹0 INR\n\n• No mutual exclusivity violations, statutory tax disqualifiers, or household quota breaches detected.`, data };
  }

  const activeName = norm === 'chandler' ? 'Chandler' : 'Amy';
  const ageStr = norm === 'chandler' ? 'Age 76' : 'Age 73';
  const data = {
    totalConflicts: 2,
    protectedValueInr: 1048000,
    conflicts: [
      {
        severity: 'CRITICAL EXCLUSION',
        type: 'Dual Statutory Health Cover Collision',
        parties: `${activeName} (${ageStr})`,
        schemes: 'Ayushman Vay Vandana Card (AB PM-JAY) vs. CGHS / ECHS Pensioner Cover',
        clause: 'AB PM-JAY Guidelines Clause 4.2: Senior citizens covered under existing Central/State Govt health schemes cannot receive dual benefits without an explicit option declaration.',
        risk: 'Application rejected at portal scrutiny or cancellation of existing outpatient medicine coverage.'
      }
    ],
    restructuringSteps: [
      `Submit Ayushman Form-B Option Declaration for ${activeName} to designate Ayushman Vay Vandana for in-patient cashless hospitalisation while preserving CGHS outpatient dispensary access.`
    ],
    spokenBrief: `Alert: Found bureaucratic conflicts for ${activeName} under dual statutory health cover. I've prepared a restructuring strategy to safeguard ₹1,048,000 in entitlements.`
  };
  return { text: "=== BUREAUCRATIC CONFLICT & RED-TAPE SIMULATION ===\nStatus: 🚨 CRITICAL SCRUTINY HAZARDS DETECTED", data };
}

function demoExplainGeneration(schemeId = 'scss', targetPersona = 'grandparent', memberName = '') {
  const norm = (memberName || '').trim().toLowerCase();
  let personaKey = targetPersona;
  if (norm === 'jace' || norm === 'gwen') personaKey = 'young_adult';
  else if (norm === 'riley' || norm === 'justin') personaKey = 'parent';
  else if (norm === 'chandler' || norm === 'amy') personaKey = 'grandparent';

  let schemeName = 'Senior Citizens Savings Scheme [scss]';
  let speech = "Dadaji, this is the safest place to rest your lifetime savings. Think of it like a government piggy bank that pays you a handsome reward every three months directly into your bank account. The government guarantees your money will never drop, giving you steady quarterly pocket money to spend freely without depending on anyone.";
  let analogy = 'A golden post office piggy-bank that gives you tea and fruit money every three months.';
  let readability = 'Grade 4 (Gentle Conversational)';
  let jargonIndex = '0%';

  if (personaKey === 'young_adult') {
    schemeName = 'Sovereign High-Yield Savings & SGBs';
    speech = "Hey! Think of this as an ultra-safe 8.2% fixed-yield instrument backed by the sovereign treasury. If you help your grandparents set this up via NetBanking or Post Office digital portal, it locks in peak quarterly payouts with zero market drawdowns. It's essentially risk-free alpha.";
    analogy = 'A sovereign high-yield savings engine that gives guaranteed quarterly alpha without equity drawdowns.';
    readability = 'Grade 8 (Structured & Analytical)';
    jargonIndex = '5%';
  } else if (personaKey === 'parent') {
    schemeName = 'SCSS & Pension Transition';
    speech = "For elderly parent portfolio planning, SCSS offers an 8.2% sovereign-backed yield with Section 80C tax deductions up to ₹1.5 Lakhs annually. Deposit cap is ₹30 Lakhs per individual senior, delivering predictable quarterly cash flow to insulate the family budget from market volatility.";
    analogy = 'A tax-deductible sovereign risk hedge providing fixed quarterly cash flow.';
    readability = 'Grade 10 (Executive & Financial)';
    jargonIndex = '15%';
  }

  const data = {
    schemeName,
    personaKey,
    personaLabel: personaKey === 'young_adult' ? 'Young Adult (Student)' : (personaKey === 'parent' ? 'Parent (Working Adult)' : 'Grandparent (Senior Citizen)'),
    toneLabel: 'Warm & Reassuring (Zero Bureaucracy)',
    speech,
    analogy,
    readability,
    jargonIndex,
    score: 98,
    spokenBrief: speech.slice(0, 160) + '…'
  };
  return { text: "=== CROSS-GENERATIONAL VOICE DIALECT ENGINE ===", data };
}

function demoLifeEvent(memberName = 'Justin', eventType = 'retirement') {
  const norm = (memberName || 'Justin').trim().toLowerCase();

  if (norm === 'jace') {
    const data = {
      title: 'Adulthood & Independence (Age 18+) for Jace',
      memberName: 'Jace',
      relation: 'son',
      birthYear: 2000,
      statusTransition: 'Family Admin ➔ Young Adult',
      unlockedSchemes: [
        { status: 'ELIGIBLE NOW', name: 'Atal Pension Yojana', detail: 'Jace qualifies for sovereign pension wealth accumulation at age 26.' }
      ],
      vaultDocs: ['Passport', 'Driving Licence', 'Term Life Insurance Policy'],
      missingDocs: [],
      phases: [
        { dayOffset: 7, dueDate: getIsoDate(7), task: 'Set up EPF & UAN employer portal sync for Jace' },
        { dayOffset: 21, dueDate: getIsoDate(21), task: 'Review independent term life insurance coverage for Jace' },
        { dayOffset: 45, dueDate: getIsoDate(45), task: 'Select tax regime and allocate sovereign gold savings for Jace' }
      ],
      spokenBrief: "I've prepared an adulthood independence roadmap for Jace with 3 scheduled milestone tasks."
    };
    return { text: '🎯 Life-Event Roadmap Orchestrated: Adulthood & Independence for Jace', data };
  }

  if (norm === 'gwen') {
    const data = {
      title: 'University Graduation & Student Transition for Gwen',
      memberName: 'Gwen',
      relation: 'daughter',
      birthYear: 2003,
      statusTransition: 'Family Admin ➔ Young Adult',
      unlockedSchemes: [
        { status: 'ELIGIBLE NOW', name: 'Central Sector Interest Subsidy (CSIS)', detail: 'Full interest subsidy on education loans during university study.' }
      ],
      vaultDocs: ['Passport', 'Student Health Insurance'],
      missingDocs: [],
      phases: [
        { dayOffset: 7, dueDate: getIsoDate(7), task: 'Submit semester enrollment receipt to renew University Transit Pass for Gwen' },
        { dayOffset: 21, dueDate: getIsoDate(21), task: 'Verify Aadhaar DBT bank linkage for Central Sector Interest Subsidy for Gwen' },
        { dayOffset: 45, dueDate: getIsoDate(45), task: 'Sync digital degree credentials with DigiLocker student vault for Gwen' }
      ],
      spokenBrief: "I've prepared a graduation roadmap for Gwen with 3 scheduled milestone tasks."
    };
    return { text: '🎯 Life-Event Roadmap Orchestrated: University Graduation for Gwen', data };
  }

  if (norm === 'chandler') {
    const data = {
      title: 'Super-Senior Healthcare & Digital Life Certificate for Chandler',
      memberName: 'Chandler',
      relation: 'grandfather',
      birthYear: 1950,
      statusTransition: 'Retired ➔ Super Senior',
      unlockedSchemes: [
        { status: 'ELIGIBLE NOW', name: 'Ayushman Vay Vandana Card (AB PM-JAY)', detail: '₹5 Lakh free annual in-patient cover for seniors aged 70+.' }
      ],
      vaultDocs: ['Passport', 'Senior Citizen Health Insurance', 'Fixed Deposit Scheme Certificate'],
      missingDocs: [],
      phases: [
        { dayOffset: 7, dueDate: getIsoDate(7), task: 'Set up facial biometrics on Jeevan Pramaan App for Chandler' },
        { dayOffset: 30, dueDate: getIsoDate(30), task: 'Renew Ayushman Vay Vandana Card in-patient registration for Chandler' },
        { dayOffset: 60, dueDate: getIsoDate(60), task: 'Direct pension credit verification with State Bank for Chandler' }
      ],
      spokenBrief: "I've prepared a super-senior roadmap for Chandler with 3 scheduled milestone tasks."
    };
    return { text: '🎯 Life-Event Roadmap Orchestrated: Super-Senior Healthcare for Chandler', data };
  }

  if (norm === 'amy') {
    const data = {
      title: 'Senior Citizen Healthcare & Wellness Transition for Amy',
      memberName: 'Amy',
      relation: 'grandmother',
      birthYear: 1953,
      statusTransition: 'Retired ➔ Senior Pensioner',
      unlockedSchemes: [
        { status: 'ELIGIBLE NOW', name: 'Ayushman Vay Vandana Card (AB PM-JAY)', detail: '₹5 Lakh free annual in-patient cover for seniors aged 70+.' }
      ],
      vaultDocs: ['Ayushman Vay Vandana Health Card', 'Post Office Senior Savings Certificate'],
      missingDocs: [],
      phases: [
        { dayOffset: 7, dueDate: getIsoDate(7), task: 'Submit annual pension life certificate before 18-day deadline for Amy' },
        { dayOffset: 30, dueDate: getIsoDate(30), task: 'Designate Ayushman Form-B for in-patient cover while preserving outpatient access for Amy' },
        { dayOffset: 60, dueDate: getIsoDate(60), task: 'Quarterly SCSS interest disbursement audit for Amy' },
        { dayOffset: 90, dueDate: getIsoDate(90), task: 'Annual preventative wellness review at empanelled hospital for Amy' }
      ],
      spokenBrief: "I've prepared a healthcare and pension transition roadmap for Amy with 4 scheduled milestone tasks."
    };
    return { text: '🎯 Life-Event Roadmap Orchestrated: Senior Healthcare for Amy', data };
  }

  if (norm === 'riley') {
    const data = {
      title: 'Household Relocation & Estate Planning for Riley',
      memberName: 'Riley',
      relation: 'mother',
      birthYear: 1972,
      statusTransition: 'Employed ➔ Family Steward',
      unlockedSchemes: [
        { status: 'ELIGIBLE NOW', name: 'Section 80D Family & Senior Deductions', detail: 'Up to ₹75,000 combined annual health deductions.' }
      ],
      vaultDocs: ['Driving Licence', 'Professional Membership Card'],
      missingDocs: [],
      phases: [
        { dayOffset: 7, dueDate: getIsoDate(7), task: 'Renew Family Health Insurance policy with accumulated cumulative bonus for Riley' },
        { dayOffset: 21, dueDate: getIsoDate(21), task: 'Complete digital Re-KYC for mutual fund family portfolio for Riley' },
        { dayOffset: 45, dueDate: getIsoDate(45), task: 'Rebalance tax deductions under Section 80D and Section 80C for Riley' }
      ],
      spokenBrief: "I've prepared an estate and healthcare roadmap for Riley with 3 scheduled milestone tasks."
    };
    return { text: '🎯 Life-Event Roadmap Orchestrated: Relocation & Estate for Riley', data };
  }

  // Justin (default)
  const data = {
    title: 'Retirement & Senior Transition for Justin',
    memberName: 'Justin',
    relation: 'father',
    birthYear: 1968,
    statusTransition: 'Employed ➔ Retired Senior',
    unlockedSchemes: [
      { status: 'ALMOST ELIGIBLE', name: 'Senior Citizens Savings Scheme', detail: 'Justin qualifies around age 60.' }
    ],
    vaultDocs: ['Driving Licence', 'Passport'],
    missingDocs: ['Age proof', 'Aadhaar card', 'Bank account passbook', 'Pension/Superannuation Order'],
    phases: [
      { dayOffset: 7, dueDate: getIsoDate(7), task: 'Consolidate pension papers & superannuation documents for Justin' },
      { dayOffset: 30, dueDate: getIsoDate(30), task: 'Apply for Senior Citizens Savings Scheme (SCSS) / deposit setup for Justin' },
      { dayOffset: 60, dueDate: getIsoDate(60), task: 'Review health coverage & register for Ayushman Vay Vandana card for Justin' },
      { dayOffset: 90, dueDate: getIsoDate(90), task: 'Submit annual Digital Life Certificate (Jeevan Pramaan) for Justin' }
    ],
    spokenBrief: "I've prepared a phased retirement roadmap for Justin with 4 scheduled milestone tasks."
  };
  return { text: '🎯 Life-Event Roadmap Orchestrated: Retirement & Senior Transition for Justin', data };
}


