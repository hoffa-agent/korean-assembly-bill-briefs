const cards = document.querySelector('#cards');
const meta = document.querySelector('#meta');
const search = document.querySelector('#search');
let digest = { generated_at: null, bills: [] };

const fmtDate = d => new Intl.DateTimeFormat('en', { dateStyle: 'medium' }).format(new Date(d));
function render() {
  const q = search.value.trim().toLowerCase();
  const bills = digest.bills.filter(b => JSON.stringify(b).toLowerCase().includes(q));
  meta.textContent = digest.generated_at
    ? `Updated ${fmtDate(digest.generated_at)} · ${digest.bills.length} recent plenary notices tracked`
    : `${digest.bills.length} recent plenary notices tracked`;
  cards.innerHTML = bills.length ? bills.map(b => `
    <article class="card">
      <div class="date">${b.date || 'Date unavailable'}</div>
      <h2>${b.title}</h2>
      <p class="summary">${b.summary}</p>
      <ul class="key-points">${(b.key_points || []).map(p => `<li>${p}</li>`).join('')}</ul>
      <div class="details">
        ${(b.items || []).map(item => `<details><summary>${item.title}</summary><p>${item.summary}</p></details>`).join('')}
      </div>
      <p class="small">Source: <a href="${b.url}" target="_blank" rel="noreferrer">National Assembly plenary result</a></p>
    </article>`).join('') : `<div class="empty">No matching bills found.</div>`;
}

fetch('data/bills.json', { cache: 'no-store' })
  .then(r => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)))
  .then(data => { digest = data; render(); })
  .catch(err => {
    cards.innerHTML = `<div class="empty">Could not load the digest yet. The daily action may still be preparing data.<br>${err.message}</div>`;
    meta.textContent = 'Digest unavailable';
  });
search.addEventListener('input', render);
