/**
 * Passenger Reports Dashboard JS — TN Bus Lost & Found
 * Implements: Report Fetching, Stats, AI Matches View, Logout
 */

const API_BASE = "/api";
const AUTH_TOKEN = localStorage.getItem("jwt_token");

/** Initialize Dashboard */
function initDashboard() {
  if (!AUTH_TOKEN) {
    window.location.href = "/login.html";
    return;
  }

  fetchMyReports();
  setupEventListeners();
}

/** Fetch user's reports */
function fetchMyReports() {
  fetch(`${API_BASE}/my-reports`, {
    headers: { "Authorization": `Bearer ${AUTH_TOKEN}` }
  })
    .then(res => res.json())
    .then(data => {
      renderReports(data.reports || []);
      updateStats(data.reports || []);
    })
    .catch(err => {
      console.error("Error fetching reports:", err);
      showAlert("Failed to load your reports.", "error");
    });
}

/** Render Table */
function renderReports(reports) {
  const tbody = document.querySelector('#reports-table tbody');
  const emptyState = document.getElementById('no-reports-message');

  tbody.innerHTML = "";

  if (reports.length === 0) {
    tbody.innerHTML = "";
    emptyState.classList.remove('hidden');
    return;
  }

  emptyState.classList.add('hidden');

  reports.forEach(r => {
    const row = document.createElement('tr');
    row.innerHTML = `
            <td>
                <div class="item-cell">
                    <strong>${r.item_name}</strong>
                    <span class="trip-badge" style="display:block; font-size:0.75rem; color:var(--text-muted);">${r.source_depot_id} &rarr; ${r.destination_depot_id}</span>
                </div>
            </td>
            <td><small>${r.date_lost}</small></td>
            <td><span class="badge ${r.status}">${r.status === 'under_review' ? 'Under Review' : r.status.charAt(0).toUpperCase() + r.status.slice(1)}</span></td>
            <td>
                <button onclick="viewMatches('${r.id}')" class="action-btn">
                    <i class="fas fa-search-location"></i> View AI Matches
                </button>
            </td>
        `;
    tbody.appendChild(row);
  });
}

/** View AI Matches (Same as manager view but restricted to own report) */
window.viewMatches = (reportId) => {
  const modal = document.getElementById('match-modal');
  const container = document.getElementById('match-results-container');

  container.innerHTML = "<div class='loader-spinner'></div> <p>AI is scanning for matches...</p>";
  modal.classList.remove('hidden');

  // Securely fetch matches for this specific report
  fetch(`/api/matches/${reportId}`, {
    headers: { "Authorization": `Bearer ${AUTH_TOKEN}` }
  })
    .then(res => res.json())
    .then(data => {
      const matches = data.matches || [];
      if (matches.length === 0) {
        container.innerHTML = "<p>No matches found yet. We will notify you when a manager finds an item that matches your description.</p>";
        return;
      }

      container.innerHTML = matches.map(m => `
            <div class="match-card">
                <div class="match-score">${m.match_score}% Match</div>
                <div class="match-body">
                    <img src="${m.photo_url}" class="match-img" alt="Matched Item">
                    <div class="match-info">
                        <h4>Potential Match Found</h4>
                        <p>${m.description}</p>
                        <p><small><i class="fas fa-calendar-alt"></i> Found on: ${m.found_date}</small></p>
                        <p><small><i class="fas fa-warehouse"></i> At Depot: <strong>${m.depot_id}</strong></small></p>
                        <div class="match-actions mt-2">
                            <button class="btn-primary" onclick="window.claimItem('${m.id}', '${m.depot_id}')">
                                <i class="fas fa-hand-holding"></i> Claim Item
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join("");
    })
    .catch(err => {
      console.error("Match error:", err);
      container.innerHTML = "<p class='error'>Failed to load matches.</p>";
    });
};

function updateStats(reports) {
  const total = reports.length;
  const pending = reports.filter(r => r.status === "under_review").length;
  const resolved = reports.filter(r => r.status === "found" || r.status === "returned").length;

  document.getElementById('total-reports').textContent = total;
  document.getElementById('pending-reports').textContent = pending;
  document.getElementById('resolved-reports').textContent = resolved;
}

function setupEventListeners() {
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      if (typeof clearToken === 'function') clearToken();
      else {
        localStorage.removeItem('jwt_token');
        localStorage.removeItem('user_role');
      }
      window.location.href = "/login.html";
    });
  }
}

function showAlert(msg, type) {
  const container = document.getElementById('reports-alert');
  if (container) {
    container.innerHTML = `<div class="alert ${type}">${msg}</div>`;
    setTimeout(() => container.innerHTML = "", 5500);
  }
}

/** Claim Request (Mocked as per Step 6) */
window.claimItem = (foundId, depotId) => {
  alert(`CLAIM REQUESTED!\n\nYour request for item ${foundId} has been sent to ${depotId}.\n\nPlease visit the depot with valid ID proof (Aadhar/Voter ID) to collect your item.\n\nNote: Depot may contact you at your registered mobile number.`);
  // Future update: Add backend claim tracking
};

document.addEventListener('DOMContentLoaded', initDashboard);
