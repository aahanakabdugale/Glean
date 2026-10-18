/**
 * traceExplain.js
 * Plain-English mapper and statistics calculation for Glean MCP Protocol Traces.
 */

/**
 * Calculates executive trace statistics: total calls, avg latency, success %, slowest call.
 * @param {Array} traces
 * @returns {{ total: number, avgLatency: number, successPct: number, slowestMs: number }}
 */
export function calculateTraceStats(traces) {
  if (!traces || traces.length === 0) {
    return {
      total: 0,
      avgLatency: 0,
      successPct: 100,
      slowestMs: 0
    };
  }

  const total = traces.length;
  const latencies = traces.map(t => (typeof t.ms === 'number' && !isNaN(t.ms)) ? t.ms : 0);
  const totalMs = latencies.reduce((acc, curr) => acc + curr, 0);
  const avgLatency = Math.round(totalMs / total);
  const slowestMs = latencies.length > 0 ? Math.max(...latencies) : 0;

  const successCount = traces.filter(t => {
    if (t.isLive) return true;
    const s = String(t.status || '').toLowerCase();
    return s.includes('200') || s.includes('ok') || s === 'success';
  }).length;

  const successPct = Math.round((successCount / total) * 100);

  return {
    total,
    avgLatency,
    successPct,
    slowestMs
  };
}

/**
 * Extracts a human-readable plain English explanation and arguments breakdown for a tool call.
 * @param {Object} trace
 * @returns {{ asked: string, argsList: Array<{ key: string, value: string }>, summary: string }}
 */
export function explainTrace(trace) {
  if (!trace) {
    return {
      asked: 'No trace selected.',
      argsList: [],
      summary: 'Select a trace from the table to view execution details.'
    };
  }

  const toolName = trace.toolName || 'unknown_tool';
  const args = trace.toolArgs || {};
  const rawResult = trace.rawResult || (typeof trace.responsePayload?.result === 'string' ? trace.responsePayload.result : '');

  // Format arguments into key/value chip items
  const argsList = Object.entries(args).map(([key, value]) => ({
    key,
    value: typeof value === 'object' ? JSON.stringify(value) : String(value)
  }));

  // Tool-specific mapping
  switch (toolName) {
    case 'list_family_members': {
      let count = 6;
      if (typeof rawResult === 'string' && rawResult.includes('Found')) {
        const match = rawResult.match(/Found (\d+)/i);
        if (match) count = parseInt(match[1], 10);
      }
      return {
        asked: 'Asked the database for all family members and registered profiles.',
        argsList,
        summary: `Returned ${count} family members with active roles and birth records.`
      };
    }

    case 'add_family_member': {
      const name = args.name || 'new member';
      const rel = args.relation ? ` (${args.relation})` : '';
      return {
        asked: `Added ${name}${rel} to the household family roster.`,
        argsList,
        summary: rawResult || `Registered ${name} in SQLite family database.`
      };
    }

    case 'remove_family_member': {
      const name = args.name || 'member';
      return {
        asked: `Removed ${name} from the household family roster.`,
        argsList,
        summary: rawResult || `Deleted ${name} and related records from database.`
      };
    }

    case 'reset_family_roster':
      return {
        asked: 'Reset family roster to canonical demo dataset.',
        argsList,
        summary: 'Restored 6 demo family members with aligned evaluation dates.'
      };

    case 'get_family_dashboard':
      return {
        asked: 'Requested aggregated executive dashboard metrics for the whole family.',
        argsList,
        summary: 'Aggregated expiring documents, upcoming tasks, and government schemes.'
      };

    case 'audit_document_dependencies': {
      const name = args.member_name ? `for ${args.member_name}` : 'for the family';
      return {
        asked: `Audited document expiration dates, renewal blockers, and prerequisites ${name}.`,
        argsList,
        summary: 'Identified critical document renewal milestones and dependent benefits.'
      };
    }

    case 'orchestrate_life_event': {
      const event = args.event_type ? `'${args.event_type}'` : 'life milestone';
      const target = args.member_name ? ` for ${args.member_name}` : '';
      return {
        asked: `Generated an end-to-end milestone timeline for ${event}${target}.`,
        argsList,
        summary: 'Constructed chronological action items, statutory deadlines, and required forms.'
      };
    }

    case 'family_brief':
      return {
        asked: 'Queried daily family status brief and identity vault summary.',
        argsList,
        summary: 'Generated consolidated summary of pending tasks and urgent alerts.'
      };

    case 'check_scheme_eligibility': {
      const who = args.member_name ? `for ${args.member_name}` : '';
      const scheme = args.scheme_id ? ` under '${args.scheme_id}'` : '';
      return {
        asked: `Evaluated government scheme eligibility rules ${who}${scheme}.`,
        argsList,
        summary: 'Evaluated age thresholds, citizenship, income bounds, and prerequisite documentation.'
      };
    }

    case 'search_schemes': {
      const q = args.query ? `'${args.query}'` : 'all schemes';
      const country = args.country ? ` in jurisdiction ${args.country}` : '';
      return {
        asked: `Searched verified public welfare schemes matching ${q}${country}.`,
        argsList,
        summary: 'Retrieved matching government schemes from verified policy database.'
      };
    }

    case 'resolve_dialect_intent': {
      const dialect = args.dialect ? ` (${args.dialect})` : '';
      return {
        asked: `Analyzed voice input with regional dialect adaptation${dialect}.`,
        argsList,
        summary: 'Standardized colloquial intent into deterministic system query.'
      };
    }

    case 'verify_pension_superannuation': {
      const member = args.member_name ? `for ${args.member_name}` : '';
      return {
        asked: `Audited pension, superannuation, and retirement entitlements ${member}.`,
        argsList,
        summary: 'Verified age milestones, payout calculations, and annuity documentation.'
      };
    }

    case 'generate_scheme_checklist': {
      const scheme = args.scheme_id ? `for ${args.scheme_id}` : '';
      return {
        asked: `Compiled mandatory application checklist and prerequisites ${scheme}.`,
        argsList,
        summary: 'Returned verified document checklist, official submission portal, and fees.'
      };
    }

    case 'plan_scheme_application': {
      const scheme = args.scheme_id ? `for '${args.scheme_id}'` : '';
      return {
        asked: `Generated step-by-step application execution plan ${scheme}.`,
        argsList,
        summary: 'Constructed structured stage milestones and document dependencies.'
      };
    }

    case 'check_bureaucratic_conflicts':
      return {
        asked: 'Scanned active family schemes for regulatory conflicts and benefit overlaps.',
        argsList,
        summary: 'Audited multi-scheme rules for clause incompatibilities and disqualifiers.'
      };

    case 'sync_family_calendar':
      return {
        asked: 'Synchronized deadlines and milestone reminders to family calendar.',
        argsList,
        summary: 'Scheduled alert notifications and renewal deadlines in family schedule.'
      };

    case 'query_family_vault':
      return {
        asked: 'Queried secure local vault for stored document identifiers.',
        argsList,
        summary: 'Retrieved verified document records from encrypted local storage.'
      };

    case 'complete_task': {
      const task = args.task_title || (args.task_id ? `Task #${args.task_id}` : 'task');
      const who = args.member_name ? ` for ${args.member_name}` : '';
      return {
        asked: `Marked task '${task}'${who} as completed in family records.`,
        argsList,
        summary: rawResult || 'Task status updated to done (done = 1).'
      };
    }

    default: {
      const argCount = Object.keys(args).length;
      return {
        asked: `Invoked MCP tool '${toolName}' with ${argCount} argument${argCount === 1 ? '' : 's'}.`,
        argsList,
        summary: rawResult
          ? (rawResult.length > 120 ? rawResult.slice(0, 117) + '…' : rawResult)
          : 'Returned deterministic response from MCP server.'
      };
    }
  }
}
