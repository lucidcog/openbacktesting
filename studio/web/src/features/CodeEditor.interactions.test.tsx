// @vitest-environment jsdom
import '@/test/dom'
import { render } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import CodeEditor from './CodeEditor'
type EditorApi = { addCommand: (key: number, callback: () => void) => void; setPosition: (position: { lineNumber: number; column: number }) => void; revealLineInCenter: (line: number) => void }
type EditorProps = { onMount: (editor: EditorApi) => void; onChange: (value: string | undefined) => void; options: { readOnly: boolean }; path: string; value: string; original?: string; modified?: string; theme: string }
const mock = vi.hoisted(() => ({ editor: vi.fn<(props: EditorProps) => null>(() => null), diff: vi.fn<(props: EditorProps) => null>(() => null), config: vi.fn(), theme: vi.fn() }))
vi.mock('@monaco-editor/react', () => ({ default: mock.editor, DiffEditor: mock.diff, loader: { config: mock.config } }))
vi.mock('monaco-editor/editor/editor.api.js', () => ({ KeyMod: { CtrlCmd: 2048 }, KeyCode: { KeyS: 49 }, editor: { defineTheme: mock.theme } }))
vi.mock('monaco-editor/languages/definitions/python/register.js', () => ({}))
vi.mock('monaco-editor/editor/editor.worker.js?worker', () => ({ default: class Worker {} }))
const props = () => mock.editor.mock.lastCall![0]
it('UI-M01: Ctrl/Cmd+S invokes the latest save callback after rerender', () => {
  const first = vi.fn(), next = vi.fn(), commands = new Map<number, () => void>()
  const view = render(<CodeEditor path="a.py" value="one" dark onChange={vi.fn()} onSave={first} />)
  props().onMount({ addCommand: (key, callback) => commands.set(key, callback), setPosition: vi.fn(), revealLineInCenter: vi.fn() })
  commands.get(2048 | 49)!(); expect(first).toHaveBeenCalledOnce()
  view.rerender(<CodeEditor path="a.py" value="two" dark onChange={vi.fn()} onSave={next} />)
  commands.get(2048 | 49)!(); expect(next).toHaveBeenCalledOnce(); expect(first).toHaveBeenCalledOnce()
})
it('UI-M02: an empty editor emits an empty draft instead of undefined', () => {
  const change = vi.fn(); render(<CodeEditor path="a.py" value="one" dark onChange={change} onSave={vi.fn()} />)
  props().onChange(undefined); expect(change).toHaveBeenLastCalledWith('')
  props().onChange('changed'); expect(change).toHaveBeenLastCalledWith('changed')
})
it('UI-M03: snapshot editor is readonly and scrolls to the referenced source line', () => {
  render(<CodeEditor path="snapshot/a.py" value="code" dark readonly line={12} onChange={vi.fn()} onSave={vi.fn()} />)
  expect(props().options.readOnly).toBe(true)
  const editor = { addCommand: vi.fn(), setPosition: vi.fn(), revealLineInCenter: vi.fn() }; props().onMount(editor)
  expect(editor.setPosition).toHaveBeenCalledWith({ lineNumber: 12, column: 1 }); expect(editor.revealLineInCenter).toHaveBeenCalledWith(12)
})
it('UI-M04: conflict diff shows disk and draft readonly without registering a save shortcut', () => {
  render(<CodeEditor path="a.py" value="draft" original="disk" dark={false} onChange={vi.fn()} onSave={vi.fn()} />)
  expect(mock.diff.mock.lastCall![0]).toMatchObject({ original: 'disk', modified: 'draft', theme: 'light', options: { readOnly: true } })
  expect(mock.diff.mock.lastCall![0].onMount).toBeUndefined()
})
it('UI-M05: file and theme changes update the editor model without replacing the draft', () => {
  const view = render(<CodeEditor path="a.py" value="draft a" dark onChange={vi.fn()} onSave={vi.fn()} />)
  expect(props()).toMatchObject({ path: 'a.py', value: 'draft a', theme: 'studio-dark' })
  view.rerender(<CodeEditor path="b.py" value="draft b" dark={false} onChange={vi.fn()} onSave={vi.fn()} />)
  expect(props()).toMatchObject({ path: 'b.py', value: 'draft b', theme: 'light' })
})
