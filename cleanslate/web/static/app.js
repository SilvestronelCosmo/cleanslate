/* CleanSlate Web Application Client */

let currentScanData = {
  targetEmail: '',
  services: [],
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

// GDPR Modal Elements
const gdprModal = document.getElementById('gdpr-modal');
const btnCloseModal = document.getElementById('btn-close-modal');
const gdprUserName = document.getElementById('gdpr-user-name');
const gdprLang = document.getElementById('gdpr-lang');
const gdprDpoField = document.getElementById('gdpr-dpo-field');
const gdprSubjectField = document.getElementById('gdpr-subject-field');
const gdprBodyField = document.getElementById('gdpr-body-field');
const btnCopyGdpr = document.getElementById('btn-copy-gdpr');
const btnOpenMailto = document.getElementById('btn-open-mailto');

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

// OSINT Form
const formOsint = document.getElementById('form-osint');
formOsint.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('osint-email').value.trim();
  if (!email) return;

  setLoading(true, 'Scansione OSINT in corso...', `Verifica registrazione per ${email} su decine di servizi web`);
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
    showToast(`Scansione OSINT completata: trovati ${data.total_services} account.`);
  } catch (err) {
    alert(`Errore: ${err.message}`);
  } finally {
    setLoading(false);
  }
});

// IMAP Form
const formImap = document.getElementById('form-imap');
formImap.addEventListener('submit', async (e) => {
  e.preventDefault();
  const host = document.getElementById('imap-host').value.trim();
  const port = parseInt(document.getElementById('imap-port').value, 10);
  const username = document.getElementById('imap-user').value.trim();
  const password = document.getElementById('imap-pass').value.trim();

  setLoading(true, 'Connessione IMAP e analisi inbox...', `Scansione header per ${username} su ${host}`);
  resultsSection.style.display = 'none';

  try {
    const res = await fetch('/api/scan/imap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ host, port, username, password, max_emails: 150 }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Errore IMAP');
    }

    const data = await res.json();
    renderResults(data);
    showToast(`Audit inbox completato: identificati ${data.total_services} servizi.`);
  } catch (err) {
    alert(`Errore: ${err.message}`);
  } finally {
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
  setLoading(true, 'Parsing archivio email offline...', `Analisi del file ${file.name}`);
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
    alert(`Errore: ${err.message}`);
  } finally {
    setLoading(false);
  }
}

// Quick Demo Data
btnLoadDemo.addEventListener('click', async () => {
  setLoading(true, 'Caricamento scenario demo...', 'Simulazione footprint reale');
  try {
    const res = await fetch('/api/demo-data?email=portfolio.demo@example.com');
    const data = await res.json();
    renderResults(data);
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
  };

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
  const catBadgeClass = `badge badge-${s.category}`;
  const catLabels = {
    account: 'Account',
    subscription: 'Abbonamento',
    newsletter: 'Newsletter',
    breach: 'Breach Rilevato',
  };

  const diffBadgeClass = `badge badge-diff-${s.difficulty}`;
  const diffLabels = {
    easy: 'Canc. Facile',
    medium: 'Canc. Media',
    hard: 'Canc. Difficile',
    impossible: 'Impossibile',
    unknown: 'Rating N/D',
  };

  const initial = (s.name || s.domain).charAt(0).toUpperCase();

  // Action Buttons
  let actionButtonsHtml = '';

  // 1-Click Unsubscribe (for newsletters)
  if (s.category === 'newsletter' && (s.unsubscribe_url || s.unsubscribe_post)) {
    actionButtonsHtml += `
      <button class="btn btn-outline btn-sm btn-unsub" data-url="${s.unsubscribe_url || ''}">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
        </svg>
        1-Click Unsubscribe
      </button>
    `;
  }

  // Delete Account URL
  if (s.delete_url) {
    actionButtonsHtml += `
      <a href="${s.delete_url}" target="_blank" rel="noopener" class="btn btn-outline btn-sm">
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
    <button class="btn btn-primary btn-sm btn-gdpr" data-name="${s.name}" data-dpo="${s.dpo_email || ''}">
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
          <span class="service-title">${s.name}</span>
          <span class="service-domain">${s.domain}</span>
          <span class="${catBadgeClass}">${catLabels[s.category] || s.category}</span>
          <span class="${diffBadgeClass}">${diffLabels[s.difficulty] || s.difficulty}</span>
        </div>
        ${s.notes ? `<div class="service-notes">${s.notes}</div>` : ''}
        ${s.last_activity ? `<div style="font-size: 0.75rem; color: var(--text-dim);">Ultima attività rilevata: ${s.last_activity}</div>` : ''}
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
      const unsubUrl = unsubBtn.dataset.url;
      unsubBtn.disabled = true;
      unsubBtn.innerHTML = 'Invio richiesta...';
      try {
        const res = await fetch('/api/actions/unsubscribe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ unsub_url: unsubUrl, email: currentScanData.targetEmail }),
        });
        const result = await res.json();
        if (result.success) {
          unsubBtn.innerHTML = '✓ Disiscritto!';
          unsubBtn.classList.remove('btn-outline');
          unsubBtn.classList.add('btn-primary');
          showToast(`Disiscrizione completata per ${s.name}`);
        } else {
          unsubBtn.innerHTML = 'Apertura link...';
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
