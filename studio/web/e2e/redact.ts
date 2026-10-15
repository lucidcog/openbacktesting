/** Remove full quoted credentials as well as startup URLs and HTTP headers. */
export function redact(text: string): string {
  return text.replace(/((?:cookie|set-cookie|authorization)\s*:)\s*[^\r\n]+/gi, '$1[REDACTED]')
    .replace(/((?:startup[_-]?token|access[_-]?token|token|csrf|x-studio-csrf|password|secret|cookie|set-cookie|authorization)["']?\s*[:=]\s*)(?:"[^"\n]*"|'[^'\n]*'|[^\s&,;}]+)/gi, '$1[REDACTED]')
}
