const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../cleanslate/web/static/app.js'), 'utf8');

function openApp() {
  const elements = new Map();
  const el = id => {
    if (!elements.has(id)) elements.set(id, {
      innerHTML: '', value: '', style: {}, dataset: {},
      addEventListener() {}, appendChild() {}, querySelectorAll() { return []; },
      classList: { add() {}, remove() {}, toggle() {} },
    });
    return elements.get(id);
  };
  const context = vm.createContext({
    document: { getElementById: el, querySelectorAll: () => [], createElement: () => el('option') },
    fetch: async () => ({ ok: true, json: async () => [] }),
    localStorage: { getItem() { return null; }, setItem() {}, removeItem() {} },
    setTimeout() {}, clearTimeout() {}, setInterval() {}, clearInterval() {}, URL, console,
  });
  vm.runInContext(source, context);
  return { context, el };
}

const base = { services: [], target_email: 'nessuno@example.com', total_services: 0, accounts_count: 0, subscriptions_count: 0, newsletters_count: 0 };

test('unverified summary is neutral and details distinguish observed cause from hypothesis', () => {
  const { context, el } = openApp();
  context.renderResults({ ...base, unverified: ['github.com', 'discord.com'], unverified_details: [
    { domain: 'github.com', cause: 'HTTP 403' },
    { domain: 'discord.com', cause: 'RuntimeError', hint: 'Il flusso può richiedere un captcha.' },
  ] });
  const html = el('unverified-note').innerHTML;
  assert.match(html, /^<strong>2 servizi non verificabili<\/strong>\./);
  assert.ok(!html.includes('endpoint protetti'));
  assert.match(html, /<strong>github.com<\/strong>: HTTP 403<\/li>/);
  assert.match(html, /<strong>discord.com<\/strong>: RuntimeError — Possibile causa: Il flusso può richiedere un captcha\./);
  assert.match(html, /<ul[^>]+hidden/);
  assert.match(html, /Mostra dettagli/);
  assert.equal(el('unverified-note').style.display, 'block');
});

test('all unverified details are escaped and removed after a successful scan', () => {
  const { context, el } = openApp();
  context.renderResults({ ...base, unverified: ['example.com'], unverified_details: [
    { domain: '<img src=x>', cause: '<script>oops</script>', hint: '<svg onload=x>' },
  ] });
  const html = el('unverified-note').innerHTML;
  assert.ok(html.includes('&lt;img src=x&gt;'));
  assert.ok(html.includes('&lt;script&gt;oops&lt;/script&gt;'));
  assert.ok(html.includes('&lt;svg onload=x&gt;'));
  assert.ok(!html.includes('<script>') && !html.includes('<img') && !html.includes('<svg'));
  context.renderResults({ ...base, unverified: [], unverified_details: [] });
  assert.equal(el('unverified-note').innerHTML, '');
  assert.equal(el('unverified-note').style.display, 'none');
});
