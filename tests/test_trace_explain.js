import test from 'node:test';
import assert from 'node:assert/strict';
import { calculateTraceStats, explainTrace } from '../frontend/src/lib/traceExplain.js';

test('calculateTraceStats calculates total, avg, success %, and slowest correctly', () => {
  const sampleTraces = [
    { ms: 20, status: '200 OK' },
    { ms: 90, status: '200 OK' },
    { ms: 50, status: 'Failed (timeout)' },
    { ms: 40, status: '200 OK' }
  ];

  const stats = calculateTraceStats(sampleTraces);
  assert.equal(stats.total, 4);
  assert.equal(stats.avgLatency, 50); // (20 + 90 + 50 + 40) / 4 = 50
  assert.equal(stats.slowestMs, 90);
  assert.equal(stats.successPct, 75); // 3 out of 4 succeeded
});

test('calculateTraceStats handles empty traces gracefully', () => {
  const stats = calculateTraceStats([]);
  assert.equal(stats.total, 0);
  assert.equal(stats.avgLatency, 0);
  assert.equal(stats.slowestMs, 0);
  assert.equal(stats.successPct, 100);
});

test('explainTrace generates accurate plain English for known tools', () => {
  // Test 1: list_family_members
  const listTrace = {
    toolName: 'list_family_members',
    toolArgs: {},
    rawResult: 'Found 6 family members'
  };
  const listExplanation = explainTrace(listTrace);
  assert.match(listExplanation.asked, /all family members/i);
  assert.match(listExplanation.summary, /6 family members/i);
  assert.equal(listExplanation.argsList.length, 0);

  // Test 2: audit_document_dependencies with args
  const auditTrace = {
    toolName: 'audit_document_dependencies',
    toolArgs: { member_name: 'Chandler' },
    rawResult: 'Chandler Passport expires soon'
  };
  const auditExplanation = explainTrace(auditTrace);
  assert.match(auditExplanation.asked, /Chandler/i);
  assert.equal(auditExplanation.argsList.length, 1);
  assert.equal(auditExplanation.argsList[0].key, 'member_name');
  assert.equal(auditExplanation.argsList[0].value, 'Chandler');
});

test('explainTrace handles unknown tools with safe fallback', () => {
  const unknownTrace = {
    toolName: 'custom_mcp_plugin_call',
    toolArgs: { param1: 'test_val', num: 42 },
    rawResult: 'Custom result execution succeeded'
  };
  const explanation = explainTrace(unknownTrace);
  assert.match(explanation.asked, /custom_mcp_plugin_call/i);
  assert.match(explanation.asked, /2 arguments/i);
  assert.match(explanation.summary, /Custom result execution succeeded/i);
  assert.equal(explanation.argsList.length, 2);
});
