/**
 * Formats a number as a currency string (USD).
 * Returns a fallback string if value is null or undefined.
 */
export function formatCurrency(value: number | null | undefined, fallback = '-'): string {
  if (value === null || value === undefined) {
    return fallback;
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
}

/**
 * Formats a number with standard commas.
 */
export function formatNumber(value: number | null | undefined, fallback = '-'): string {
  if (value === null || value === undefined) {
    return fallback;
  }
  return new Intl.NumberFormat('en-US').format(value);
}

/**
 * Formats an ISO date string or Date object into a readable date string.
 */
export function formatDate(date: string | Date | null | undefined, fallback = '-'): string {
  if (!date) {
    return fallback;
  }
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) {
    return fallback;
  }
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(d);
}

/**
 * Formats an ISO date string or Date object into a readable date and time string.
 */
export function formatDateTime(date: string | Date | null | undefined, fallback = '-'): string {
  if (!date) {
    return fallback;
  }
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) {
    return fallback;
  }
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(d);
}
