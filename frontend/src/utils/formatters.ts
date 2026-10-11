/**
 * Defangs a URL to prevent accidental browser clicks or automatic link expansion.
 * Converts http:// -> hxxp://, https:// -> hxxps://, and replaces dots in domains with [.]
 * E.g., https://evil.com/login -> hxxps://evil[.]com/login
 */
export function defangUrl(rawUrl: string): string {
  if (!rawUrl) return '';

  return rawUrl
    .replace(/^http:\/\//i, 'hxxp://')
    .replace(/^https:\/\//i, 'hxxps://')
    .replace(/^ftp:\/\//i, 'fxp://')
    .replace(/\./g, '[.]');
}

/**
 * Truncates long hashes or identifiers with middle ellipsis
 */
export function truncateIdentifier(id: string, startChars = 8, endChars = 8): string {
  if (!id) return '';
  if (id.length <= startChars + endChars + 3) return id;
  return `${id.slice(0, startChars)}...${id.slice(-endChars)}`;
}

/**
 * Formats bytes into a human-readable file size string
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}
