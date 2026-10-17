/**
 * speech.js — Audio speech sanitizer and conversational TTS brief generator
 *
 * Ensures all spoken responses sound natural, conversational, and clean.
 * Strips CLI banners (===, ---), markdown symbols (**, ##, •), bracket noise,
 * emojis, and expands shorthand (e.g. "60d" -> "60 days") so text-to-speech
 * engines never speak literal punctuation words like "equals, equals, equals".
 */

/**
 * Sanitizes any raw or markdown text into natural, speakable English.
 * @param {string} raw
 * @returns {string}
 */
export function cleanTextForSpeech(raw) {
  if (!raw) return '';
  let s = String(raw);

  // 1. Replace web URLs with a spoken phrase
  s = s.replace(/https?:\/\/\S+/g, ' on the official website ');

  // 2. Strip CLI banners & horizontal rules (=== HEADER ===, --- SECTION ---, etc.)
  // Converts "=== FAMILY ADMIN DASHBOARD (6 Members Tracked) ===" into "FAMILY ADMIN DASHBOARD. 6 Members Tracked."
  s = s.replace(/[=]{2,}\s*([^=\n]+?)\s*[=]{2,}/g, '$1. ');
  s = s.replace(/[-]{2,}\s*([^\-\n]+?)\s*[-]{2,}/g, '$1. ');
  s = s.replace(/[_]{2,}\s*([^_\n]+?)\s*[_]{2,}/g, '$1. ');

  // Remove any leftover repeated symbols (===, ---, ___, ***, ###)
  s = s.replace(/[=\-_*~#]{2,}/g, ' ');

  // 3. Remove markdown headers (# Header, ## Subheader)
  s = s.replace(/^#{1,6}\s+/gm, '');

  // 4. Markdown links: [Link text](http://...) -> Link text
  s = s.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');

  // 5. Markdown formatting: bold, italic, code, strikethrough
  s = s.replace(/\*\*([^*]+)\*\*/g, '$1');
  s = s.replace(/\*([^*]+)\*/g, '$1');
  s = s.replace(/__([^_]+)__/g, '$1');
  s = s.replace(/_([^_]+)_/g, '$1');
  s = s.replace(/`([^`]+)`/g, '$1');
  s = s.replace(/~~([^~]+)~~/g, '$1');

  // 6. Parentheses and brackets around tags:
  // Converts (6 Members Tracked) -> , 6 Members Tracked,
  // Converts [URGENT (6d left)] -> , URGENT, 6 days left,
  s = s.replace(/\[([^\]]+)\]/g, ', $1, ');
  s = s.replace(/\(([^)]+)\)/g, ', $1, ');

  // 7. Time shorthand expansion: 60d -> 60 days, 14d -> 14 days, 3mo -> 3 months
  s = s.replace(/\b(\d+)\s*d\b/gi, '$1 days');
  s = s.replace(/\b(\d+)\s*mo\b/gi, '$1 months');
  s = s.replace(/\b(\d+)\s*yr?s?\b/gi, '$1 years');

  // 8. Bullets, dots, arrows, hyphens
  s = s.replace(/[•\u2022\u25E6\u2043\u2219·]/g, '. ');
  s = s.replace(/^\s*[-*+>]\s+/gm, '. ');
  s = s.replace(/(?:->|→|=>|⇒)/g, ' leads to ');
  s = s.replace(/\s*[—–]\s*/g, ', ');

  // 9. Currency symbols: ₹5,00,000 -> 5,00,000 rupees
  s = s.replace(/₹\s*([0-9,.]+)/g, '$1 rupees');

  // 10. Strip emojis and miscellaneous symbols (avoids TTS announcing "clipboard", "warning", etc.)
  s = s.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}]/gu, '');

  // 11. Clean stray characters: pipe, tilde, caret, slash, backslash, brackets
  s = s.replace(/[|~^#<>{}\\]/g, ' ');

  // 12. Punctuation & whitespace normalization
  s = s.replace(/\s*,\s*,+/g, ', ');
  s = s.replace(/\s*\.\s*\.+/g, '. ');
  s = s.replace(/\s*,\s*\./g, '. ');
  s = s.replace(/\s*\.\s*,\s*/g, '. ');
  s = s.replace(/\s+([.,;:?!])/g, '$1');
  s = s.replace(/[ \t]+/g, ' ');
  s = s.replace(/(\r?\n)+/g, '. ');
  s = s.replace(/\s*\.\s*\.+/g, '. ');

  return s.trim();
}

/**
 * Generates a concise conversational spoken brief for the whole-family dashboard.
 */
export function generateDashboardSpokenBrief(dashboardData) {
  const m = dashboardData?.metrics || {};
  const members = m.totalMembers ?? (dashboardData?.members?.length || 6);
  const docs = m.totalDocs ?? 0;
  const urgent = m.urgentDocs ?? 0;
  const tasks = m.pendingTasks ?? 0;
  const overdue = m.overdueTasks ?? 0;
  const schemes = m.schemeOpportunities ?? 0;

  let brief = `Here is your family dashboard. You have ${members} family members tracked with ${docs} documents and ${tasks} pending tasks.`;
  if (urgent > 0) {
    brief += ` Attention needed: ${urgent} document is marked urgent.`;
  } else if (overdue > 0) {
    brief += ` Attention needed: ${overdue} task is overdue.`;
  } else if (schemes > 0) {
    brief += ` ${schemes} scheme opportunities identified.`;
  }
  return cleanTextForSpeech(brief);
}

/**
 * Generates a concise conversational spoken brief for family briefing.
 */
export function generateFamilyBriefSpokenBrief(briefData, memberName = '') {
  const isPersonal = memberName && memberName !== 'all';
  const expCount = briefData?.expiringCount ?? 0;
  const taskCount = briefData?.tasksCount ?? 0;

  if (isPersonal) {
    let text = `Here is the personal briefing for ${memberName}.`;
    if (expCount > 0 && taskCount > 0) {
      text += ` You have ${expCount} expiring documents and ${taskCount} upcoming tasks.`;
    } else if (expCount > 0) {
      text += ` You have ${expCount} expiring documents requiring attention.`;
    } else if (taskCount > 0) {
      text += ` You have ${taskCount} upcoming tasks due soon.`;
    } else {
      text += ` All documents and tasks are up to date.`;
    }
    return cleanTextForSpeech(text);
  }

  let text = `Here is your family briefing.`;
  if (expCount > 0 && taskCount > 0) {
    text += ` You have ${expCount} documents expiring and ${taskCount} tasks due in the next two weeks.`;
  } else if (expCount > 0) {
    text += ` You have ${expCount} documents expiring soon.`;
  } else if (taskCount > 0) {
    text += ` You have ${taskCount} tasks due soon.`;
  } else {
    text += ` Everything is up to date across all family records.`;
  }
  return cleanTextForSpeech(text);
}

/**
 * Generates a concise conversational spoken brief for expiring documents.
 */
export function generateExpiringDocsSpokenBrief(docs, days = 30) {
  if (!Array.isArray(docs) || docs.length === 0) {
    return `Good news. No family documents are expiring in the next ${days} days.`;
  }
  const urgentCount = docs.filter(d => d.urgency === 'urgent' || (d.daysLeft != null && d.daysLeft <= 7)).length;
  let brief = `Found ${docs.length} family documents expiring within ${days} days.`;
  if (urgentCount > 0) {
    brief += ` ${urgentCount} require urgent renewal.`;
  }
  return cleanTextForSpeech(brief);
}

/**
 * Generates a concise conversational spoken brief for upcoming tasks.
 */
export function generateTasksSpokenBrief(tasks, days = 30) {
  if (!Array.isArray(tasks) || tasks.length === 0) {
    return `No pending family tasks due in the next ${days} days.`;
  }
  const overdueCount = tasks.filter(t => t.overdue || (t.statusText && t.statusText.includes('OVERDUE'))).length;
  let brief = `You have ${tasks.length} upcoming tasks.`;
  if (overdueCount > 0) {
    brief += ` ${overdueCount} tasks are overdue.`;
  }
  return cleanTextForSpeech(brief);
}

/**
 * Generates a concise conversational spoken brief for scheme eligibility.
 */
export function generateEligibilitySpokenBrief(data, name) {
  const person = name || data?.personName || 'your family member';
  const eligibleCount = data?.eligible?.length ?? 0;
  const almostCount = data?.almostEligible?.length ?? 0;
  let brief = `Checked scheme eligibility for ${person}.`;
  if (eligibleCount > 0) {
    brief += ` Eligible for ${eligibleCount} government welfare schemes.`;
  }
  if (almostCount > 0) {
    brief += ` ${almostCount} schemes coming up soon based on milestone criteria.`;
  }
  return cleanTextForSpeech(brief);
}

/**
 * Generates a concise conversational spoken brief for scheme checklist.
 */
export function generateChecklistSpokenBrief(data) {
  const name = data?.name || data?.schemeName || 'the requested scheme';
  const count = data?.items?.length ?? 0;
  return cleanTextForSpeech(`Here is the required document checklist for ${name}. There are ${count} required items to prepare.`);
}

/**
 * Generates a concise conversational spoken brief for scheme application plan.
 */
export function generatePlanSpokenBrief(data, name, scheme) {
  const target = name || data?.memberName || 'your family member';
  const schemeName = scheme || data?.scheme || 'the scheme';
  return cleanTextForSpeech(`I have prepared a step-by-step application plan for ${target} for ${schemeName}.`);
}

/**
 * Generates a concise conversational spoken brief for family roster.
 */
export function generateMembersSpokenBrief(members) {
  const count = Array.isArray(members) ? members.length : 6;
  return cleanTextForSpeech(`You have ${count} family members registered in your vault.`);
}
