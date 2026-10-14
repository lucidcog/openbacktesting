import { useEffect, useRef } from 'react'
import Editor, { DiffEditor, loader } from '@monaco-editor/react'
import * as monaco from 'monaco-editor/editor/editor.api.js'
import 'monaco-editor/languages/definitions/python/register.js'
import EditorWorker from 'monaco-editor/editor/editor.worker.js?worker'

self.MonacoEnvironment = { getWorker: () => new EditorWorker() }
loader.config({ monaco })
monaco.editor.defineTheme('studio-dark', { base: 'vs-dark', inherit: true, rules: [], colors: { 'editor.background': '#131722', 'editorLineNumber.foreground': '#5d6473' } })

export default function CodeEditor({ path, value, dark, readonly = false, original, line, onChange, onSave }: { path: string; value: string; dark: boolean; readonly?: boolean; line?: number; original?: string; onChange: (value: string) => void; onSave: () => void }) {
  const save = useRef(onSave)
  useEffect(() => { save.current = onSave }, [onSave])
  const options = { minimap: { enabled: false }, fontSize: 12, fontFamily: 'IBM Plex Mono, monospace', scrollBeyondLastLine: false, readOnly: readonly, automaticLayout: true, padding: { top: 12 } }
  if (original !== undefined) return <DiffEditor original={original} modified={value} language="python" theme={dark ? 'studio-dark' : 'light'} options={{ ...options, readOnly: true }} />
  return <Editor path={path} value={value} language="python" theme={dark ? 'studio-dark' : 'light'} options={options} onChange={value => onChange(value ?? '')} onMount={editor => { if (line) { editor.setPosition({ lineNumber: line, column: 1 }); editor.revealLineInCenter(line) }; editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => save.current()) }} />
}
