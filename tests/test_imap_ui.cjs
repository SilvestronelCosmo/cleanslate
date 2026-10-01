const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../cleanslate/web/static/app.js'), 'utf8');
const key = 'cleanslate.lastImapProfile';
const first = { name: 'user@example.com@imap.first.example:993', host: 'imap.first.example', port: 993, username: 'user@example.com' };
const second = { name: 'user@example.com@imap.second.example:1993', host: 'imap.second.example', port: 1993, username: 'user@example.com' };

class Element {
  constructor(id) {
    this.id = id;
    this.listeners = {};
    this.children = [];
    this.dataset = {};
    this.style = {};
    this.classList = { add() {}, remove() {}, toggle() {} };
    this.value = '';
  }
  set value(value) { this._value = String(value); }
  get value() { return this._value; }
  set innerHTML(html) { this.children = []; if (this.id === 'imap-profile-select') this.value = ''; }
  appendChild(child) { this.children.push(child); }
  addEventListener(event, fn) { (this.listeners[event] ||= []).push(fn); }
  querySelector() { return new Element('button'); }
  querySelectorAll() { return []; }
  async dispatch(event) { for (const fn of this.listeners[event] || []) await fn({ target: this, preventDefault() {} }); }
}

async function openApp(profiles, storage = new Map(), storageDenied = false) {
  const elements = new Map();
  const el = id => {
    if (!elements.has(id)) elements.set(id, new Element(id));
    return elements.get(id);
  };
  const imapTab = new Element('imap-tab');
  imapTab.dataset.tab = 'tab-imap';
  const preset = new Element('preset');
  preset.dataset.preset = 'gmail';
  const api = { profiles, failList: false, failDelete: false, requests: [] };
  const context = vm.createContext({
    document: {
      getElementById: el,
      querySelectorAll: selector => selector === '.tab-btn' ? [imapTab] : selector === '.preset-btn' ? [preset] : [],
      createElement: () => new Element('option'),
    },
    localStorage: {
      getItem(k) { if (storageDenied) throw new Error('denied'); return storage.get(k) || null; },
      setItem(k, v) { if (storageDenied) throw new Error('denied'); storage.set(k, v); },
      removeItem(k) { if (storageDenied) throw new Error('denied'); storage.delete(k); },
    },
    fetch: async (url, options = {}) => {
      api.requests.push({ url, ...options });
      if (options.method === 'POST') {
        const body = JSON.parse(options.body);
        const name = `${body.username}@${body.host}:${body.port}`.toLowerCase();
        api.profiles = [{ name, host: body.host, port: body.port, username: body.username }];
        return { ok: true, json: async () => ({ profile_name: name }) };
      }
      if (options.method === 'DELETE') {
        if (api.failDelete) return { ok: false, json: async () => ({ detail: 'fake-secret' }) };
        api.profiles = api.profiles.filter(p => !url.endsWith(encodeURIComponent(p.name)));
        return { ok: true, json: async () => ({ ok: true }) };
      }
      return { ok: !api.failList, json: async () => api.profiles };
    },
    alert: message => { api.lastAlert = message; },
    confirm: () => true,
    setTimeout: () => 1, clearTimeout() {}, setInterval: () => 1, clearInterval() {},
    URL, console,
  });
  vm.runInContext(source, context);
  await new Promise(resolve => setImmediate(resolve));
  return { el, context, storage, api, imapTab, preset };
}

function assertSelected(app, profile) {
  assert.equal(app.el('imap-profile-select').value, profile.name);
  assert.equal(app.el('imap-host').value, profile.host);
  assert.equal(app.el('imap-port').value, String(profile.port));
  assert.equal(app.el('imap-user').value, profile.username);
  assert.equal(app.el('imap-pass').value, '');
  assert.equal(app.el('imap-pass').required, false);
}

test('one profile is selected and filled on startup', async () => {
  const app = await openApp([first]);
  assertSelected(app, first);
  assert.equal(app.storage.get(key), first.name);
});

test('last selection survives reopening, list reload and returning to IMAP', async () => {
  const app = await openApp([first, second]);
  assert.equal(app.el('imap-profile-select').value, '');
  app.el('imap-profile-select').value = second.name;
  await app.el('imap-profile-select').dispatch('change');
  const reopened = await openApp([first, second], app.storage);
  assertSelected(reopened, second);
  await reopened.context.loadImapProfiles();
  assertSelected(reopened, second);
  await reopened.imapTab.dispatch('click');
  await new Promise(resolve => setImmediate(resolve));
  assertSelected(reopened, second);
});

test('editing the destination detaches the stored password', async () => {
  const app = await openApp([first]);
  app.el('imap-host').value = 'different.example';
  await app.el('imap-host').dispatch('input');
  assert.equal(app.el('imap-profile-select').value, '');
  assert.equal(app.el('imap-pass').required, true);
  assert.equal(app.storage.has(key), false);
  await app.context.loadImapProfiles();
  assert.equal(app.el('imap-profile-select').value, '');
  assert.equal(app.el('imap-host').value, 'different.example');
  app.el('imap-profile-select').value = first.name;
  await app.el('imap-profile-select').dispatch('change');
  await app.preset.dispatch('click');
  assert.equal(app.el('imap-profile-select').value, '');
});

test('save selects the canonical ID and persists only that ID', async () => {
  const app = await openApp([]);
  app.el('imap-host').value = second.host;
  app.el('imap-port').value = second.port;
  app.el('imap-user').value = second.username;
  app.el('imap-pass').value = 'fake-secret';
  await app.el('btn-save-profile').dispatch('click');
  assertSelected(app, second);
  assert.deepEqual([...app.storage], [[key, second.name]]);
  const request = app.api.requests.find(r => r.method === 'POST');
  assert.equal(JSON.parse(request.body).name, undefined);
});

test('failed deletion preserves selection; successful deletion clears it', async () => {
  const app = await openApp([first]);
  app.api.failDelete = true;
  await app.el('btn-delete-profile').dispatch('click');
  assertSelected(app, first);
  assert.equal(app.storage.get(key), first.name);
  assert.ok(!app.api.lastAlert.includes('fake-secret'));
  app.api.failDelete = false;
  await app.el('btn-delete-profile').dispatch('click');
  assert.equal(app.el('imap-profile-select').value, '');
  assert.equal(app.storage.has(key), false);
  assert.equal(app.el('imap-pass').required, true);
});

test('failed list refresh preserves the current profile', async () => {
  const app = await openApp([first]);
  app.api.failList = true;
  await app.context.loadImapProfiles();
  assertSelected(app, first);
  assert.equal(app.el('profile-status').hidden, false);
});

test('missing last profile falls back to sole profile, and storage denial is tolerated', async () => {
  assertSelected(await openApp([first], new Map([[key, 'missing']])), first);
  assertSelected(await openApp([first], new Map(), true), first);
});
