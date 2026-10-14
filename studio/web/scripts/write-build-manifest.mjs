import process from 'node:process'
import { URL } from 'node:url'
import { createHash } from 'node:crypto'
import { readFile, writeFile, readdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'
const studio = fileURLToPath(new URL('../..', import.meta.url))
const web = join(studio, 'src/openbacktesting_studio/web')
const digest = bytes => createHash('sha256').update(bytes).digest('hex')
async function inventory(root, prefix = '') {
  const result = {}
  for (const entry of await readdir(join(root, prefix), { withFileTypes: true })) {
    const name = join(prefix, entry.name)
    if (entry.isDirectory()) Object.assign(result, await inventory(root, name))
    else if (entry.isFile()) result[name] = digest(await readFile(join(root, name)))
  }
  return result
}
const inputs = {}
for (const [name, hash] of Object.entries(await inventory(join(studio, 'web/src')))) inputs['web/src/' + name] = hash
for (const name of ['web/package.json', 'web/package-lock.json', 'web/vite.config.ts', 'web/tsconfig.json', 'web/scripts/build-chart.mjs', 'web/scripts/collect-notices.mjs', 'web/scripts/write-build-manifest.mjs', 'vendor-metadata/lightweight-charts.json']) inputs[name] = digest(await readFile(join(studio, name)))
const assets = await inventory(web)
delete assets['build-manifest.json']
await writeFile(join(web, 'build-manifest.json'), JSON.stringify({ schemaVersion: 1, inputs, assets }, null, 2) + '\n')
process.stdout.write(`Verified build inventory: ${Object.keys(assets).length} local assets\n`)
