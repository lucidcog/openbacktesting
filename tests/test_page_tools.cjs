/* Run with node --test tests/test_page_tools.cjs; no npm dependencies required. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "../docs/core/_static/page-tools.js"), "utf8");
const markdown = "# Strategy\n\n| Name | Value |\n| --- | --- |\n| EMA | 10 |\n\n```python\nprint('example')\n```\n";

function fixture({clipboard = true, denied = false, fetchError = false, status = 200} = {}) {
  const label = {textContent: "Copy as Markdown"};
  const message = {textContent: ""};
  const fallback = {hidden: true};
  const textarea = {value: "", focus() { this.focused = true; }, select() { this.selected = true; }};
  const button = {hidden: true, disabled: false, dataset: {markdownUrl: "index.md"}, querySelector() { return label; }};
  const result = {button, label, message, fallback, textarea, requests: [], writes: []};
  const context = {
    document: {
      querySelectorAll: () => [button],
      querySelector: () => fallback,
      getElementById: id => id === "ob-copy-status" ? message : textarea,
      addEventListener: (name, callback) => { result.click = () => callback({target: {closest: () => button}}); },
    },
    navigator: clipboard ? {clipboard: {writeText: async value => {
      if (denied) throw new Error("Permission denied");
      result.writes.push(value);
    }}} : {},
    fetch: async url => {
      result.requests.push(url);
      if (fetchError) throw new Error("Offline");
      return {ok: status === 200, text: async () => markdown};
    },
    setTimeout: callback => { result.reset = callback; },
  };
  vm.runInNewContext(source, context);
  return result;
}

test("copies the exact Markdown including tables and fenced code", async () => {
  const ui = fixture();
  assert.equal(ui.button.hidden, false);
  await ui.click();
  assert.deepEqual(ui.requests, ["index.md"]);
  assert.deepEqual(ui.writes, [markdown]);
  assert.equal(ui.label.textContent, "Copied!");
  assert.match(ui.message.textContent, /copied to clipboard/);
  assert.equal(ui.button.disabled, false);
  assert.equal(ui.fallback.hidden, true);
  ui.reset();
  assert.equal(ui.label.textContent, "Copy as Markdown");
});

for (const options of [{denied: true}, {clipboard: false}]) {
  test(`offers selected manual Markdown when clipboard is unavailable: ${JSON.stringify(options)}`, async () => {
    const ui = fixture(options);
    await ui.click();
    assert.equal(ui.fallback.hidden, false);
    assert.equal(ui.textarea.value, markdown);
    assert.equal(ui.textarea.focused, true);
    assert.equal(ui.textarea.selected, true);
    assert.match(ui.message.textContent, /Clipboard access unavailable/);
    assert.equal(ui.button.disabled, false);
    assert.equal(ui.writes.length, 0);
  });
}

for (const options of [{status: 404}, {fetchError: true}]) {
  test(`reports a failed download and allows retry: ${JSON.stringify(options)}`, async () => {
    const ui = fixture(options);
    await ui.click();
    assert.match(ui.message.textContent, /Could not load Markdown/);
    assert.equal(ui.button.disabled, false);
    assert.equal(ui.fallback.hidden, true);
    assert.equal(ui.writes.length, 0);
    await ui.click();
    assert.equal(ui.requests.length, 2);
  });
}

test("ignores a second click while copying", async () => {
  const ui = fixture();
  const first = ui.click();
  await ui.click();
  await first;
  assert.equal(ui.requests.length, 1);
});
