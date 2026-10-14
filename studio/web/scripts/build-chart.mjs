import { URL } from 'node:url'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { readFileSync, mkdirSync, writeFileSync, copyFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const directory = fileURLToPath(new URL('../../vendor/lightweight-charts/', import.meta.url))
const manifest = JSON.parse(readFileSync(new URL('../../vendor-metadata/lightweight-charts.json', import.meta.url)))
const changes = new Map(manifest.modifications.map((row) => [row.path, row.sha256]))
const tree = createHash('sha256')
for (const file of manifest.files) {
  const actual = createHash('sha256').update(readFileSync(`${directory}/${file.path}`)).digest('hex')
  if (actual !== (changes.get(file.path) ?? file.sha256)) throw new Error(`Unrecorded chart change: ${file.path}`)
  tree.update(`${file.path}\0${actual}\n`)
}
// No upstream install hooks or browser downloads are needed to compile this library.
execFileSync('npm', ['ci', '--ignore-scripts', '--no-audit', '--no-fund'], { cwd: directory, stdio: 'inherit' })
execFileSync('npm', ['run', 'build:release'], { cwd: directory, stdio: 'inherit' })
const output = new URL('../public/', import.meta.url)
mkdirSync(output, { recursive: true })
writeFileSync(new URL('chart-provenance.json', output), JSON.stringify({
  source: manifest.source, tag: manifest.tag, commit: manifest.commit, treeSha256: tree.digest('hex'),
  modifications: manifest.modifications.map(({ path, reason }) => ({ path, reason })),
}, null, 2) + '\n')
for (const name of ['LICENSE', 'NOTICE']) copyFileSync(`${directory}/${name}`, new URL(`lightweight-charts-${name}.txt`, output))
