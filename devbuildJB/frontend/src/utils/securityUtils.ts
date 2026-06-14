const INJECTION_PATTERNS: RegExp[] = [
  /\bignore\b/i,
  /\bdelete\b/i,
  /ignore (all )?previous instructions/i,
  /ignore previous instructions and/i,
  /system prompt/i,
  /<\s*script/i,
  /;\s*drop\s+table/i,
  /union\s+select/i,
  /you are now/i,
  /disregard (all )?(prior|previous)/i,
];

const PII_PATTERNS: { type: string; pattern: RegExp; replacement: string }[] = [
  { type: 'email', pattern: /\b[\w.-]+@[\w.-]+\.\w+\b/g, replacement: '[EMAIL]' },
  { type: 'gmail', pattern: /@gmail\.com\b/gi, replacement: '[GMAIL]' },
  { type: 'sin', pattern: /\bSIN\b/gi, replacement: '[SIN]' },
  { type: 'phone', pattern: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, replacement: '[PHONE]' },
  { type: 'ssn', pattern: /\b\d{3}-\d{2}-\d{4}\b/g, replacement: '[SSN]' },
];

export function detectInjection(text: string): boolean {
  return INJECTION_PATTERNS.some((pattern) => pattern.test(text));
}

export function detectPii(text: string): { detected: boolean; types: string[]; masked: string } {
  const types: string[] = [];
  for (const { type, pattern } of PII_PATTERNS) {
    if (pattern.test(text)) {
      types.push(type);
    }
    pattern.lastIndex = 0;
  }
  return {
    detected: types.length > 0,
    types,
    masked: maskPii(text),
  };
}

export function maskPii(text: string): string {
  let masked = text;
  for (const { pattern, replacement } of PII_PATTERNS) {
    masked = masked.replace(pattern, replacement);
  }
  return masked;
}
