export const PROTOCOL_VERSION = 1

export function requireProtocol(value: unknown): number {
  if (value !== PROTOCOL_VERSION) throw new Error('Unsupported Studio protocol version')
  return PROTOCOL_VERSION
}
