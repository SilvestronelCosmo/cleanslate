/* CleanSlate Web Application Client */

function escapeHtml(v) {
  if (v === null || v === undefined) return '';
  return String(v)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function safeHttpUrl(v) {
  if (!v) return null;
  try {
    const parsed = new URL(v);
    if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
      return parsed.href;
    }
  } catch (e) {}
  return null;
}

let currentScanData = {
  targetEmail: '',
  services: [],
  isDemo: false,
};

let activeFilter = 'all';
let searchQuery = '';
let currentGdprService = null;

// DOM Elements
const tabBtns = document.querySelectorAll('.tab-btn');
const tabPanes = document.querySelectorAll('.tab-pane');
const statusCard = document.getElementById('status-card');
const statusText = document.getElementById('status-text');
const statusSub = document.getElementById('status-sub');
const resultsSection = document.getElementById('results-section');
const servicesContainer = document.getElementById('services-container');
const btnLoadDemo = document.getElementById('btn-load-demo');
const tableSearch = document.getElementById('table-search');
const filterPills = document.querySelectorAll('.pill');
const toastEl = document.getElementById('toast');

// Guidance Modals Elements
const modalAppPass = document.getElementById('modal-apppass-guide');
const modalOsint = document.getElementById('modal-osint-guide');
const modalTakeout = document.getElementById('modal-takeout-guide');
const btnOpenGlobalGuide = document.getElementById('btn-open-global-guide');
const btnGuideOsint = document.getElementById('btn-guide-osint');
const btnGuideAppPassword = document.getElementById('btn-guide-apppassword');
const btnGuideTakeout = document.getElementById('btn-guide-takeout');
const closeGuideBtns = document.querySelectorAll('.btn-close-guide');

// Provider presets
const presetBtns = document.querySelectorAll('.preset-btn');
const imapHost = document.getElementById('imap-host');
const imapPort = document.getElementById('imap-port');
const imapUser = document.getElementById('imap-user');
const linkProviderAppPass = document.getElementById('link-provider-apppass');

const PROVIDER_CONFIGS = {
  gmail: {
    host: 'imap.gmail.com',
    port: 993,
    placeholder: 'tuonome@gmail.com',
    linkText: 'Crea Password Google →',
    linkUrl: 'https://myaccount.google.com/apppasswords',
  },
  outlook: {
    host: 'outlook.office365.com',
    port: 993,
    placeholder: 'tuonome@outlook.com',
    linkText: 'Crea Password Microsoft →',
    linkUrl: 'https://account.live.com/proofs/AppPassword',
  },
  icloud: {
    host: 'imap.mail.me.com',
    port: 993,
    placeholder: 'tuonome@icloud.com',
    linkText: 'Crea Password Apple →',
    linkUrl: 'https://appleid.apple.com',
  },
  yahoo: {
    host: 'imap.mail.yahoo.com',
    port: 993,
    placeholder: 'tuonome@yahoo.com',
    linkText: 'Crea Password Yahoo →',
    linkUrl: 'https://login.yahoo.com/account/security',
  },
};

// Preset switching
presetBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    presetBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const p = PROVIDER_CONFIGS[btn.dataset.preset];
    if (p) {
      imapHost.value = p.host;
      imapPort.value = p.port;
      imapUser.placeholder = p.placeholder;
      linkProviderAppPass.textContent = p.linkText;
      linkProviderAppPass.href = p.linkUrl;
    }
  });
});

// Guidance Modals Open/Close
btnOpenGlobalGuide.addEventListener('click', () => {
  modalAppPass.style.display = 'flex';
});

if (btnGuideOsint) {
  btnGuideOsint.addEventListener('click', () => {
    modalOsint.style.display = 'flex';
  });
}

if (btnGuideAppPassword) {
  btnGuideAppPassword.addEventListener('click', () => {
    modalAppPass.style.display = 'flex';
  });
}

if (btnGuideTakeout) {
  btnGuideTakeout.addEventListener('click', () => {
    modalTakeout.style.display = 'flex';
  });
}

closeGuideBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    modalAppPass.style.display = 'none';
    modalOsint.style.display = 'none';
    modalTakeout.style.display = 'none';
  });
});

[modalAppPass, modalOsint, modalTakeout].forEach(m => {
  if (m) {
    m.addEventListener('click', (e) => {
      if (e.target === m) m.style.display = 'none';
    });
  }
});

// Tab Navigation
tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    tabBtns.forEach(b => b.classList.remove('active'));
    tabPanes.forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const targetTab = document.getElementById(btn.dataset.tab);
    if (targetTab) targetTab.classList.add('active');
  });
});

// Toast notification
function showToast(message, duration = 3000) {
  toastEl.textContent = message;
  toastEl.style.display = 'block';
  setTimeout(() => {
    toastEl.style.display = 'none';
  }, duration);
}

// Show/Hide Loading
function setLoading(loading, title = 'Analisi in corso...', subtitle = 'Interrogazione endpoint e parsing header') {
  if (loading) {
    statusText.textContent = title;
    statusSub.textContent = subtitle;
    statusCard.style.display = 'flex';
  } else {
    statusCard.style.display = 'none';
  }
}

// OSINT Form (Real Discovery)
const formOsint = document.getElementById('form-osint');
formOsint.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('osint-email').value.trim();
  if (!email) return;

  const consent = document.getElementById('osint-consent');
  if (consent && !consent.checked) {
    alert('Devi confermare che si tratta del tuo indirizzo email prima di avviare la scansione.');
    return;
  }

  setLoading(true, 'Scansione OSINT reale in corso...', 'Verifica registrazione su 16 servizi (circa 10–25 s)');
  resultsSection.style.display = 'none';

  try {
    const res = await fetch('/api/scan/osint', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Errore durante la scansione');
    }

    const data = await res.json();
    renderResults(data);
    const uncertain = data.unverified?.length || 0;
    showToast(`Scansione OSINT completata: ${data.total_services} account segnalati${uncertain ? `; ${uncertain} servizi non verificabili` : ''}.`);
  } catch (err) {
    alert(`Errore scansione: ${err.message}`);
  } finally {
    setLoading(false);
  }
});

// IMAP Form (Real Inbox)
const formImap = document.getElementById('form-imap');
formImap.addEventListener('submit', async (e) => {
  e.preventDefault();
  const host = imapHost.value.trim();
  const port = parseInt(imapPort.value, 10);
  const username = imapUser.value.trim();
  const password = document.getElementById('imap-pass').value;
  const maxEmails = parseInt(document.getElementById('imap-limit').value, 10) || 150;
  const durationEl = document.getElementById('imap-duration');
  const submitButton = formImap.querySelector('button[type="submit"]');

  const startedAt = performance.now();
  const formatDuration = (milliseconds) => {
    const seconds = Math.floor(milliseconds / 1000);
    return seconds < 60 ? `${seconds} s` : `${Math.floor(seconds / 60)} min ${seconds % 60} s`;
  };
  const elapsed = () => formatDuration(performance.now() - startedAt);
  durationEl.hidden = true;
  submitButton.disabled = true;

  setLoading(true, 'Connessione IMAP e analisi inbox...', `Ultimi ${maxEmails} messaggi · Tempo trascorso: 0 s`);
  resultsSection.style.display = 'none';
  const timer = setInterval(() => {
    statusSub.textContent = `Ultimi ${maxEmails} messaggi · Tempo trascorso: ${elapsed()}`;
  }, 1000);
  let completed = false;
  let finishedAt = startedAt;

  try {
    const profileName = profileSelect ? profileSelect.value : '';
    const body = { host, port, username, password, max_emails: maxEmails };
    if (profileName) {
      body.profile_name = profileName;
    }
    const res = await fetch('/api/scan/imap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Errore IMAP');
    }

    const data = await res.json();
    renderResults(data);
    finishedAt = performance.now();
    completed = true;
    showToast(`Audit inbox completato: identificati ${data.total_services} servizi.`);
  } catch (err) {
    finishedAt = performance.now();
    alert(`Errore di connessione IMAP:\n\n${err.message}\n\nSuggerimento: Se usi Gmail, assicurati di usare una "Password per le app" da myaccount.google.com/apppasswords e non la tua password normale.`);
  } finally {
    clearInterval(timer);
    durationEl.textContent = `${completed ? 'Durata effettiva della scansione' : 'Tentativo terminato dopo'}: ${formatDuration(finishedAt - startedAt)}.`;
    durationEl.hidden = false;
    submitButton.disabled = false;
    setLoading(false);
  }
});

// Dropzone (.mbox / .eml)
const dropzone = document.getElementById('dropzone');
const mboxFileInput = document.getElementById('mbox-file-input');

dropzone.addEventListener('click', () => mboxFileInput.click());
dropzone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropzone.style.borderColor = 'var(--accent)';
});
dropzone.addEventListener('dragleave', () => {
  dropzone.style.borderColor = 'var(--border-light)';
});
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.style.borderColor = 'var(--border-light)';
  if (e.dataTransfer.files.length) {
    handleFileUpload(e.dataTransfer.files[0]);
  }
});
mboxFileInput.addEventListener('change', (e) => {
  if (e.target.files.length) {
    handleFileUpload(e.target.files[0]);
  }
});

async function handleFileUpload(file) {
  setLoading(true, 'Parsing archivio email offline...', `Analisi del file locale: ${file.name}`);
  resultsSection.style.display = 'none';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/scan/mbox', {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Errore lettura archivio');
    }

    const data = await res.json();
    renderResults(data);
    showToast(`Analisi archivio completata: trovati ${data.total_services} servizi.`);
  } catch (err) {
    alert(`Errore archivio: ${err.message}`);
  } finally {
    setLoading(false);
  }
}

// Quick Demo Data
btnLoadDemo.addEventListener('click', async () => {
  setLoading(true, 'Caricamento scenario dimostrativo...', 'Popolamento dashboard');
  try {
    const res = await fetch('/api/demo-data?email=alex.rossi@example.com');
    const data = await res.json();
    renderResults(data);
    currentScanData.isDemo = true;
    showToast('Scenario dimostrativo caricato con successo.');
  } catch (err) {
    alert('Errore caricamento demo');
  } finally {
    setLoading(false);
  }
});

// Render Results & Metrics
function renderResults(data) {
  currentScanData = {
    targetEmail: data.target_email,
    services: data.services || [],
    isDemo: false,
  };

  const unverifiedNote = document.getElementById('unverified-note');
  if (unverifiedNote) {
    if (data.unverified && data.unverified.length > 0) {
      const count = data.unverified.length;
      let html = `<strong>${count} servizi non verificabili</strong>.`;
      if (data.unverified_details && data.unverified_details.length > 0) {
        html += ' <button class="btn-expand-unverified" onclick="this.nextElementSibling.hidden=!this.nextElementSibling.hidden;this.textContent=this.nextElementSibling.hidden?\'Mostra dettagli\':\'Nascondi dettagli\'" style="background:none;border:none;color:var(--accent);cursor:pointer;font-size:0.85rem;text-decoration:underline;">Mostra dettagli</button>';
        html += '<ul class="unverified-detail-list" hidden style="margin-top:0.5rem;padding-left:1.2rem;font-size:0.85rem;">';
        for (const item of data.unverified_details) {
          const cause = item.cause || item.reason || 'Causa non disponibile';
          const hint = item.hint ? ` — Possibile causa: ${escapeHtml(item.hint)}` : '';
          html += `<li><strong>${escapeHtml(item.domain)}</strong>: ${escapeHtml(cause)}${hint}</li>`;
        }
        html += '</ul>';
      }
      unverifiedNote.innerHTML = html;
      unverifiedNote.style.display = 'block';
    } else {
      unverifiedNote.innerHTML = '';
      unverifiedNote.style.display = 'none';
    }
  }

  document.getElementById('val-total').textContent = data.total_services;
  document.getElementById('val-accounts').textContent = data.accounts_count;
  document.getElementById('val-subscriptions').textContent = data.subscriptions_count;
  document.getElementById('val-newsletters').textContent = data.newsletters_count;
  document.getElementById('sub-target-email').textContent = data.target_email;

  document.getElementById('count-all').textContent = currentScanData.services.length;
  document.getElementById('count-accounts').textContent = currentScanData.services.filter(s => s.category === 'account').length;
  document.getElementById('count-subs').textContent = currentScanData.services.filter(s => s.category === 'subscription').length;
  document.getElementById('count-news').textContent = currentScanData.services.filter(s => s.category === 'newsletter').length;

  resultsSection.style.display = 'block';
  applyFiltersAndRender();
}

// Filter pills
filterPills.forEach(pill => {
  pill.addEventListener('click', () => {
    filterPills.forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    activeFilter = pill.dataset.filter;
    applyFiltersAndRender();
  });
});

// Search input
tableSearch.addEventListener('input', (e) => {
  searchQuery = e.target.value.toLowerCase().trim();
  applyFiltersAndRender();
});

function applyFiltersAndRender() {
  servicesContainer.innerHTML = '';

  let filtered = currentScanData.services.filter(s => {
    const matchesCategory = (activeFilter === 'all') || (s.category === activeFilter);
    const matchesSearch = !searchQuery ||
      s.name.toLowerCase().includes(searchQuery) ||
      s.domain.toLowerCase().includes(searchQuery) ||
      (s.notes && s.notes.toLowerCase().includes(searchQuery));
    return matchesCategory && matchesSearch;
  });

  if (filtered.length === 0) {
    servicesContainer.innerHTML = `
      <div style="text-align: center; padding: 2.5rem; color: var(--text-dim); background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border);">
        Nessun servizio trovato corrispondente ai filtri attuali.
      </div>
    `;
    return;
  }

  filtered.forEach(service => {
    const card = createServiceCard(service);
    servicesContainer.appendChild(card);
  });
}

function createServiceCard(s) {
  const div = document.createElement('div');
  div.className = 'service-card';

  // Badges
  const catKey = escapeHtml(s.category);
  const diffKey = escapeHtml(s.difficulty);
  const catBadgeClass = `badge badge-${catKey}`;
  const catLabels = {
    account: 'Account Registrato',
    subscription: 'Abbonamento Attivo',
    newsletter: 'Newsletter / Lista',
    breach: 'Breach Rilevato',
  };

  const diffBadgeClass = `badge badge-diff-${diffKey}`;
  const diffLabels = {
    easy: 'Canc. Facile',
    medium: 'Canc. Media',
    hard: 'Canc. Difficile',
    impossible: 'Impossibile',
    unknown: 'Rating N/D',
  };

  const displayName = escapeHtml(s.name);
  const displayDomain = escapeHtml(s.domain);
  const displayNotes = escapeHtml(s.notes);
  const displayActivity = escapeHtml(s.last_activity);
  const displayVia = escapeHtml(s.found_via);
  const initial = escapeHtml((s.name || s.domain || '?').charAt(0).toUpperCase());

  const safeDeleteUrl = safeHttpUrl(s.delete_url);
  const safeUnsubUrl = safeHttpUrl(s.unsubscribe_url);

  // Action Buttons
  let actionButtonsHtml = '';

  // 1-Click Unsubscribe (for newsletters) - only if safe URL
  if (s.category === 'newsletter' && safeUnsubUrl) {
    actionButtonsHtml += `
      <button class="btn btn-outline btn-sm btn-unsub" data-url="${escapeHtml(safeUnsubUrl)}">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
        </svg>
        1-Click Unsubscribe
      </button>
    `;
  }

  // Delete Account URL - only if safe URL
  if (safeDeleteUrl) {
    actionButtonsHtml += `
      <a href="${escapeHtml(safeDeleteUrl)}" target="_blank" rel="noopener" class="btn btn-outline btn-sm">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"/>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
        </svg>
        Elimina Account
      </a>
    `;
  }

  // GDPR Request Button
  actionButtonsHtml += `
    <button class="btn btn-primary btn-sm btn-gdpr" data-name="${displayName}" data-dpo="${escapeHtml(s.dpo_email || '')}">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
      </svg>
      Art. 17 GDPR
    </button>
  `;

  div.innerHTML = `
    <div class="service-main">
      <div class="service-avatar">${initial}</div>
      <div class="service-meta">
        <div class="service-name-row">
          <span class="service-title">${displayName}</span>
          <span class="service-domain">${displayDomain}</span>
          <span class="${catBadgeClass}">${escapeHtml(catLabels[s.category] || s.category)}</span>
          <span class="${diffBadgeClass}">${escapeHtml(diffLabels[s.difficulty] || s.difficulty)}</span>
        </div>
        ${displayNotes ? `<div class="service-notes">${displayNotes}</div>` : ''}
        ${displayActivity ? `<div style="font-size: 0.75rem; color: var(--text-dim);">Rilevato: ${displayActivity} • Metodo: ${displayVia}</div>` : ''}
      </div>
    </div>
    <div class="service-actions">
      ${actionButtonsHtml}
    </div>
  `;

  // Hook up button events
  const unsubBtn = div.querySelector('.btn-unsub');
  if (unsubBtn) {
    unsubBtn.addEventListener('click', async () => {
      if (currentScanData.isDemo) {
        unsubBtn.textContent = 'Modalità demo: nessuna richiesta inviata.';
        unsubBtn.disabled = true;
        unsubBtn.classList.remove('btn-outline');
        unsubBtn.classList.add('btn-primary');
        showToast('Modalità demo: nessuna richiesta inviata.');
        return;
      }

      const unsubUrl = unsubBtn.dataset.url;
      unsubBtn.disabled = true;
      unsubBtn.textContent = 'Invio richiesta...';
      try {
        const res = await fetch('/api/actions/unsubscribe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ unsub_url: unsubUrl, email: currentScanData.targetEmail }),
        });
        const result = await res.json();
        if (result.success) {
          unsubBtn.textContent = '✓ Disiscritto!';
          unsubBtn.classList.remove('btn-outline');
          unsubBtn.classList.add('btn-primary');
          showToast(`Disiscrizione completata per ${s.name}`);
        } else {
          unsubBtn.textContent = 'Apertura link...';
          window.open(unsubUrl, '_blank');
        }
      } catch (err) {
        window.open(unsubUrl, '_blank');
      }
    });
  }

  const gdprBtn = div.querySelector('.btn-gdpr');
  if (gdprBtn) {
    gdprBtn.addEventListener('click', () => {
      openGdprModal(s);
    });
  }

  return div;
}

// GDPR Modal Handlers
const gdprModal = document.getElementById('gdpr-modal');
const btnCloseModal = document.getElementById('btn-close-modal');
const gdprUserName = document.getElementById('gdpr-user-name');
const gdprLang = document.getElementById('gdpr-lang');
const gdprDpoField = document.getElementById('gdpr-dpo-field');
const gdprSubjectField = document.getElementById('gdpr-subject-field');
const gdprBodyField = document.getElementById('gdpr-body-field');
const btnCopyGdpr = document.getElementById('btn-copy-gdpr');
const btnOpenMailto = document.getElementById('btn-open-mailto');

async function openGdprModal(service) {
  currentGdprService = service;
  gdprModal.style.display = 'flex';
  await updateGdprTemplate();
}

async function updateGdprTemplate() {
  if (!currentGdprService) return;

  const payload = {
    user_name: gdprUserName.value.trim() || 'Mario Rossi',
    user_email: currentScanData.targetEmail || 'utente@esempio.com',
    service_name: currentGdprService.name,
    dpo_email: currentGdprService.dpo_email,
    language: gdprLang.value,
  };

  try {
    const res = await fetch('/api/actions/gdpr-template', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    gdprDpoField.value = data.dpo_email;
    gdprSubjectField.value = data.subject;
    gdprBodyField.value = data.body;
    btnOpenMailto.href = data.mailto_uri;
  } catch (err) {
    console.error('Error generating GDPR letter', err);
  }
}

gdprUserName.addEventListener('input', debounce(updateGdprTemplate, 300));
gdprLang.addEventListener('change', updateGdprTemplate);

btnCloseModal.addEventListener('click', () => {
  gdprModal.style.display = 'none';
});

gdprModal.addEventListener('click', (e) => {
  if (e.target === gdprModal) gdprModal.style.display = 'none';
});

btnCopyGdpr.addEventListener('click', () => {
  const fullText = `A: ${gdprDpoField.value}\nOggetto: ${gdprSubjectField.value}\n\n${gdprBodyField.value}`;
  navigator.clipboard.writeText(fullText).then(() => {
    showToast('Lettera GDPR copiata negli appunti!');
  });
});

// IMAP Profile Management (macOS Keychain)
let savedProfiles = [];
let profilesLoaded = false;
let profileLoadVersion = 0;
const profileSelect = document.getElementById('imap-profile-select');
const btnSaveProfile = document.getElementById('btn-save-profile');
const btnDeleteProfile = document.getElementById('btn-delete-profile');
const profileStatus = document.getElementById('profile-status');
const lastImapProfileKey = 'cleanslate.lastImapProfile';

function rememberImapProfile(name) {
  try {
    if (name) localStorage.setItem(lastImapProfileKey, name);
    else localStorage.removeItem(lastImapProfileKey);
  } catch (e) {}
}

function lastImapProfile() {
  try {
    return localStorage.getItem(lastImapProfileKey) || '';
  } catch (e) {
    return '';
  }
}

function applyImapProfile(name) {
  const profile = savedProfiles.find(p => p.name === name);
  const passField = document.getElementById('imap-pass');
  profileSelect.value = profile ? profile.name : '';
  passField.value = '';
  passField.required = !profile;
  passField.placeholder = profile ? '(salvata nel Portachiavi)' : 'es. abcd efgh ijkl mnop';
  btnDeleteProfile.disabled = !profile;
  if (profile) {
    imapHost.value = profile.host;
    imapPort.value = profile.port;
    imapUser.value = profile.username;
    profileStatus.textContent = 'Profilo caricato. La password verrà letta dal Portachiavi.';
  }
  profileStatus.hidden = !profile;
  rememberImapProfile(profile ? profile.name : '');
}

async function loadImapProfiles(preferredName) {
  const version = ++profileLoadVersion;
  try {
    const res = await fetch('/api/imap/profiles');
    if (!res.ok) throw new Error('Caricamento profili non riuscito.');
    const profiles = await res.json();
    if (version !== profileLoadVersion) return;
    let selected = preferredName !== undefined ? preferredName : profileSelect.value;
    if (!profilesLoaded && preferredName === undefined && !selected) {
      const last = lastImapProfile();
      selected = profiles.some(p => p.name === last) ? last : (profiles.length === 1 ? profiles[0].name : '');
    }
    const previous = profileSelect.value;
    savedProfiles = profiles;
    profileSelect.innerHTML = '<option value="">Inserisci un altro account</option>';
    for (const p of savedProfiles) {
      const opt = document.createElement('option');
      opt.value = p.name;
      opt.textContent = `${p.username} — ${p.host}:${p.port}`;
      profileSelect.appendChild(opt);
    }
    profileSelect.value = savedProfiles.some(p => p.name === selected) ? selected : '';
    if (!profilesLoaded || preferredName !== undefined || profileSelect.value !== previous) {
      applyImapProfile(profileSelect.value);
    }
    profilesLoaded = true;
  } catch (e) {
    if (version !== profileLoadVersion) return;
    profileStatus.textContent = 'Impossibile caricare i profili. Riprova aprendo la scheda IMAP.';
    profileStatus.hidden = false;
  }
}

profileSelect.addEventListener('change', () => applyImapProfile(profileSelect.value));

function detachImapProfile() {
  if (profileSelect.value) applyImapProfile('');
}
[imapHost, imapPort, imapUser].forEach(field => field.addEventListener('input', detachImapProfile));
presetBtns.forEach(btn => btn.addEventListener('click', detachImapProfile));

btnSaveProfile.addEventListener('click', async () => {
  const host = imapHost.value.trim();
  const port = parseInt(imapPort.value, 10);
  const username = imapUser.value.trim();
  const password = document.getElementById('imap-pass').value;
  if (!host || !Number.isInteger(port) || port < 1 || port > 65535 || !username || !password) {
    alert('Inserisci server, porta, email e password prima di salvare il profilo.');
    return;
  }
  btnSaveProfile.disabled = true;
  try {
    const res = await fetch('/api/imap/profiles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ host, port, username, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Errore salvataggio profilo.');
    document.getElementById('imap-pass').value = '';
    rememberImapProfile(data.profile_name);
    await loadImapProfiles(data.profile_name);
    showToast(data.message || 'Profilo salvato nel Portachiavi.');
  } catch (e) {
    alert('Impossibile salvare il profilo nel Portachiavi.');
  } finally {
    btnSaveProfile.disabled = false;
  }
});

btnDeleteProfile.addEventListener('click', async () => {
  const name = profileSelect.value;
  if (!name) return;
  if (!confirm(`Eliminare il profilo "${name}" e la sua password dal Portachiavi?`)) return;
  btnDeleteProfile.disabled = true;
  try {
    const res = await fetch(`/api/imap/profiles/${encodeURIComponent(name)}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Errore eliminazione profilo.');
    applyImapProfile('');
    await loadImapProfiles('');
    showToast(data.message || 'Profilo eliminato.');
  } catch (e) {
    alert('Impossibile eliminare il profilo dal Portachiavi. Riprova.');
  } finally {
    btnDeleteProfile.disabled = !profileSelect.value;
  }
});

tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    if (btn.dataset.tab === 'tab-imap') loadImapProfiles();
  });
});

loadImapProfiles();

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
