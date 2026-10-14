// @vitest-environment jsdom
import '@/test/dom'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import { deferred } from '@/test/dom'
import { api } from '@/protocol/client'
import { WorkspacePicker } from './WorkspacePicker'
const directory = (path = '/work') => ({ path, parent: path === '/' ? '/' : '/', directories: path === '/work' ? ['child'] : [] })
let respond: (path: string) => unknown
beforeEach(() => {
  respond = url => directory(new URLSearchParams(url.split('?')[1]).get('path')!)
  vi.spyOn(api, 'request').mockImplementation(async <T,>(path: string) => await respond(path) as T)
})
function mount(onSelect = vi.fn(async () => {}), onOpenChange = vi.fn()) { render(<WorkspacePicker open initialPath="/work" onSelect={onSelect} onOpenChange={onOpenChange} />); return { onSelect, onOpenChange } }
it('UI-W01: directory child and parent browsing change only the listing until Open is pressed', async () => {
  const { onSelect } = mount(); const user = userEvent.setup(); await user.click(await screen.findByRole('button', { name: 'child' }))
  await waitFor(() => expect((screen.getByRole('textbox', { name: 'Workspace directory path' }) as HTMLInputElement).value).toBe('/work/child'))
  expect(onSelect).not.toHaveBeenCalled(); await user.click(screen.getByRole('button', { name: 'Parent directory' }))
  await waitFor(() => expect((screen.getByRole('textbox', { name: 'Workspace directory path' }) as HTMLInputElement).value).toBe('/'))
  expect((screen.getByRole('button', { name: 'Parent directory' }) as HTMLButtonElement).disabled).toBe(true)
})
it.each(['Browse', 'Enter'])('UI-W02: typed path submitted with %s browses without opening a workspace', async action => {
  const { onSelect } = mount(); await screen.findByRole('button', { name: 'child' }); const user = userEvent.setup(), input = screen.getByRole('textbox', { name: 'Workspace directory path' })
  await user.clear(input); await user.type(input, '/typed')
  if (action === 'Browse') await user.click(screen.getByRole('button', { name: 'Browse' })); else await user.keyboard('{Enter}')
  await waitFor(() => expect(api.request).toHaveBeenCalledWith('/directories?path=%2Ftyped', expect.anything()))
  expect(onSelect).not.toHaveBeenCalled()
})
it('UI-W03: Open directory passes the trimmed chosen path and blocks double submission', async () => {
  const pending = deferred<void>(), onSelect = vi.fn(() => pending.promise)
  mount(onSelect); await screen.findByRole('button', { name: 'child' }); fireEvent.change(screen.getByRole('textbox', { name: 'Workspace directory path' }), { target: { value: ' /chosen ' } })
  await userEvent.setup().dblClick(screen.getByRole('button', { name: 'Open directory' }))
  expect(onSelect).toHaveBeenCalledExactlyOnceWith('/chosen'); expect((screen.getByRole('button', { name: 'Opening workspace…' }) as HTMLButtonElement).disabled).toBe(true)
  await act(async () => pending.resolve())
})
it('UI-W04: selection failure remains visible and permits retry without losing the path', async () => {
  const onSelect = vi.fn().mockRejectedValueOnce(Error('Workspace busy')).mockResolvedValue(undefined)
  mount(onSelect); await screen.findByRole('button', { name: 'child' }); const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Open directory' })); await screen.findByText('Workspace busy')
  await user.click(screen.getByRole('button', { name: 'Open directory' })); await waitFor(() => expect(onSelect).toHaveBeenCalledTimes(2)); expect(screen.queryByText('Workspace busy')).toBeNull()
})
it('UI-W05: missing directory can be corrected and Close/Escape do not select a workspace', async () => {
  respond = path => path.includes('missing') ? Promise.reject(Error('Directory missing')) : directory('/work')
  const { onSelect, onOpenChange } = mount(); await screen.findByRole('button', { name: 'child' }); const user = userEvent.setup()
  fireEvent.change(screen.getByRole('textbox', { name: 'Workspace directory path' }), { target: { value: '/missing' } }); await user.click(screen.getByRole('button', { name: 'Browse' })); await screen.findByText('Directory missing')
  fireEvent.change(screen.getByRole('textbox', { name: 'Workspace directory path' }), { target: { value: '/work' } }); await user.click(screen.getByRole('button', { name: 'Browse' })); await screen.findByRole('button', { name: 'child' })
  expect(screen.queryByText('Directory missing')).toBeNull(); await user.click(screen.getByRole('button', { name: 'Close' })); expect(onOpenChange).toHaveBeenCalledWith(false); expect(onSelect).not.toHaveBeenCalled()
  await user.keyboard('{Escape}'); expect(onSelect).not.toHaveBeenCalled()
})
it('UI-W06: cancelled older directory requests cannot overwrite a later successful listing', async () => {
  const old = deferred<ReturnType<typeof directory>>()
  respond = path => path.includes('slow') ? old.promise : directory('/fresh')
  mount(); await screen.findByText('No subdirectories. You can select this directory.')
  const input = screen.getByRole('textbox', { name: 'Workspace directory path' })
  fireEvent.change(input, { target: { value: '/slow' } }); fireEvent.submit(input.closest('form')!)
  fireEvent.change(input, { target: { value: '/fresh' } }); fireEvent.submit(input.closest('form')!)
  await screen.findByText('No subdirectories. You can select this directory.')
  await act(async () => old.resolve(directory('/wrong-old')))
  expect((input as HTMLInputElement).value).toBe('/fresh')
})
