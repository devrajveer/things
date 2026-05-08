import { ulid } from 'ulid';

/**
 * Generates a new ULID prefixed with the given string.
 */
export function generateId(prefix: string): string {
  return `${prefix}_${ulid()}`;
}

/**
 * Parses a prefixed ULID and returns the raw ULID string.
 * Throws an error if the format is invalid.
 */
export function parseId(prefixedId: string): string {
  if (!prefixedId || typeof prefixedId !== 'string') {
    throw new Error('Invalid ID format');
  }
  
  const parts = prefixedId.split('_');
  if (parts.length !== 2) {
    throw new Error(`Invalid prefixed ID format: ${prefixedId}`);
  }
  
  const [, ulidStr] = parts;
  if (!ulidStr || ulidStr.length !== 26) {
    throw new Error(`Invalid ULID length in prefixed ID: ${prefixedId}`);
  }
  
  return ulidStr;
}
