/**
 * Centralized urgency classification for days left.
 *
 * Rules:
 *  - <= 7 days (or negative/expired): 'urgent' (Red)
 *  - 8 to 30 days: 'soon' (Yellow)
 *  - > 30 days: 'ok' (Green)
 *
 * @param {number|null|undefined} daysLeft
 * @returns {'urgent' | 'soon' | 'ok'}
 */
export function urgencyOf(daysLeft) {
  if (daysLeft === null || daysLeft === undefined) return 'soon';
  const num = Number(daysLeft);
  if (isNaN(num)) return 'soon';
  if (num <= 7) return 'urgent';
  if (num <= 30) return 'soon';
  return 'ok';
}

/**
 * Returns human-readable label paired with the status.
 * e.g. "Expired (2d ago)", "6 days left", "22 days left", "90 days left"
 *
 * @param {number} daysLeft
 * @returns {string}
 */
export function formatDaysLeft(daysLeft) {
  if (daysLeft === null || daysLeft === undefined) return '';
  const num = Number(daysLeft);
  if (isNaN(num)) return '';
  if (num < 0) return `Expired (${Math.abs(num)}d ago)`;
  if (num === 0) return 'Due today';
  if (num === 1) return '1 day left';
  return `${num} days left`;
}
