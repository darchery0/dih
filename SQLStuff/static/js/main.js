const input = document.getElementById('searchInput');
const form = document.getElementById('searchForm');
const toast = document.getElementById('toast');
let toastTimer;

// Real-time catalog searching
function filterCatalog(query) {
  const term = query.trim().toLowerCase();
  
  // Search local card grids and tables
  const groups = [
    { selector: '#bookGrid .searchable', empty: 'booksEmpty' },
    { selector: '#requestTable tbody .searchable', empty: 'requestsEmpty' },
    { selector: '#resourceTable tbody .searchable', empty: 'resourcesEmpty' }
  ];

  let totalMatches = 0;
  groups.forEach(group => {
    const rows = [...document.querySelectorAll(group.selector)];
    let matches = 0;
    rows.forEach(row => {
      const text = (row.dataset.search || row.textContent).toLowerCase();
      const found = !term || text.includes(term);
      row.style.display = found ? '' : 'none';
      if (found) matches++;
    });
    
    const emptyElem = document.getElementById(group.empty);
    if (emptyElem) emptyElem.style.display = matches === 0 ? 'block' : 'none';
    totalMatches += matches;
  });

  if (term && totalMatches === 0) {
    showToast('No local records found for “' + query.trim() + '”.');
  }
}

// Search Form Handler
form.addEventListener('submit', event => {
  event.preventDefault();
  filterCatalog(input.value);
  document.getElementById('books').scrollIntoView({ behavior: 'smooth', block: 'start' });
});

input.addEventListener('input', () => filterCatalog(input.value));

// Popular Search Chips
document.querySelectorAll('[data-query]').forEach(button => {
  button.addEventListener('click', () => {
    const query = button.dataset.query;
    input.value = query;
    filterCatalog(query);
  });
});

// Toast Notifications
function showToast(message) {
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
}

// Modal Handlers for "View All Books"
function openAllBooksModal() {
  document.getElementById('allBooksModal').style.display = 'block';
}

function closeAllBooksModal() {
  document.getElementById('allBooksModal').style.display = 'none';
}

window.onclick = function(event) {
  const modal = document.getElementById('allBooksModal');
  if (event.target === modal) {
    modal.style.display = 'none';
  }
};