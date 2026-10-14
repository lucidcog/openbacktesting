import { readFileSync, readdirSync, writeFileSync, existsSync, realpathSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath, URL } from 'node:url'
const root = fileURLToPath(new URL('..', import.meta.url))
const notices = [], seen = new Set()
function locate(name, parent) {
  for (let current = parent; ; current = dirname(current)) {
    const candidate = join(current, 'node_modules', name, 'package.json')
    if (existsSync(candidate)) return dirname(realpathSync(candidate))
    if (dirname(current) === current) throw new Error(`Missing runtime license dependency: ${name}`)
  }
}
function visit(path, include = true) {
  const pkg = JSON.parse(readFileSync(join(path, 'package.json'), 'utf8'))
  const identity = `${pkg.name}@${pkg.version}`
  if (seen.has(identity)) return
  seen.add(identity)
  if (include) {
    const names = readdirSync(path, { withFileTypes: true }).filter(entry => entry.isFile() && /^(license|licence|copying|notice|ofl)(\.|$)/i.test(entry.name)).map(entry => entry.name)
    const texts = names.map(name => `${name}\n${readFileSync(join(path, name), 'utf8')}`)
    notices.push(`${identity}\nLicense: ${pkg.license ?? 'See package documentation'}\n${texts.join('\n\n')}`)
  }
  for (const name of Object.keys(pkg.dependencies ?? {})) visit(locate(name, path))
}
visit(root, false)
writeFileSync(new URL('../../src/openbacktesting_studio/web/third-party-notices.txt', import.meta.url), notices.join('\n\n----------------------------------------\n\n'))
