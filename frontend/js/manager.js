/**
 * Manager Dashboard JS — TN Bus Lost & Found
 * Implements: Auth, Found Item Posting, AI Matching Result View, Real-time SocketIO
 */

const API_BASE = "/api/manager";
const AUTH_TOKEN = localStorage.getItem("jwt_token");
let socket;

/** Initialize */
function initManager() {
  if (!AUTH_TOKEN) {
    window.location.href = "/login.html";
    return;
  }

  // Role Guard
  const userRole = localStorage.getItem("user_role");
  if (userRole !== "manager") {
    window.location.href = "/dashboard.html"; // Redirect to passenger dashboard
    return;
  }

  fetchReports();
  fetchFoundItems();
  setupSocket();
  setupEventListeners();
  fetchManagerInfo();

  // Auto Refresh every 60 seconds
  setInterval(() => {
    fetchReports();
    fetchFoundItems();
  }, 60000);
}

/** Fetch Manager/Depot Info */
function fetchManagerInfo() {
  fetch("/api/auth/me", {
    headers: { "Authorization": `Bearer ${AUTH_TOKEN}` }
  })
    .then(res => res.json())
    .then(user => {
      if (user.assigned_depot_name) {
        document.getElementById('manager-depot-name').innerHTML = `
    <i class="fas fa-map-marker-alt"></i> ${user.assigned_depot_name}
  `;
        // Initialize minimal map for manager's depot
        initManagerMap(user);
      }
    })
    .catch(err => console.error("Error fetching info:", err));
}

function initManagerMap(user) {
  if (!user.assigned_depot_id) return;

  // Use the global /api/depots endpoint
  fetch(`/api/depots`)
    .then(res => res.json())
    .then(data => {
      const depot = data.depots.find(d => d.depot_id === user.assigned_depot_id);
      if (depot && depot.latitude && depot.longitude) {
        const mgrMap = L.map('manager-depot-map', { zoomControl: false }).setView([depot.latitude, depot.longitude], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(mgrMap);

        const icon = L.divIcon({
          className: 'custom-bus-icon',
          html: `<div class="bus-marker-inner" style="border-color: #7A0C0C; color: #7A0C0C; background: white; width:30px; height:30px; display:flex; align-items:center; justify-content:center; border-radius:50%; border:2px solid #7A0C0C;">
                    <i class="fas fa-bus"></i>
                 </div>`,
          iconSize: [30, 30]
        });

        L.marker([depot.latitude, depot.longitude], { icon: icon })
          .addTo(mgrMap)
          .bindPopup(`<strong>${depot.name}</strong><br>${depot.city}`)
          .openPopup();
      }
    });
}

/** Fetch Relevant Lost Reports (Pathing through this depot) */
function fetchReports() {
  fetch(`${API_BASE}/reports`, {
    headers: { "Authorization": `Bearer ${AUTH_TOKEN}` }
  })
    .then(res => res.json())
    .then(data => {
      renderReports(data.reports || []);
      updateStats(data.reports || []);
    })
    .catch(err => {
      console.error("Error fetching reports:", err);
      showAlert("Official communication error: Failed to sync reports.", "error");
    });
}

/** Fetch Items Found in THIS Depot */
function fetchFoundItems() {
  fetch(`${API_BASE}/found-luggage`, {
    headers: { "Authorization": `Bearer ${AUTH_TOKEN}` }
  })
    .then(res => res.json())
    .then(data => {
      renderFoundItems(data.items || []);
      document.getElementById('stat-found-count').textContent = (data.items || []).length;
    })
    .catch(err => console.error("Error fetching found items:", err));
}

/** Render My Depot Found Items */
function renderFoundItems(items) {
  const tbody = document.querySelector('#found-items-table tbody');
  const msg = document.getElementById('no-found-items-msg');
  tbody.innerHTML = "";

  if (items.length === 0) {
    msg.classList.remove('hidden');
    return;
  }
  msg.classList.add('hidden');

  items.forEach(item => {
    const row = document.createElement('tr');
    row.innerHTML = `
            <td>
                <div style="display:flex; align-items:center; gap:12px;">
                    <img src="${item.photo_url}" style="width:50px;height:50px;border-radius:6px;object-fit:cover; border:1px solid #ddd;">
                    <div style="display:flex; flex-direction:column;">
                        <span style="font-weight:600; color:var(--text);">${item.description}</span>
                        <small class="muted">Ref: ${item.id.substring(18)}</small>
                    </div>
                </div>
            </td>
            <td><strong>${item.found_date}</strong></td>
            <td><span class="badge" style="background:#DCFCE7; color:#166534; font-size:0.75rem;">IN CUSTODY</span></td>
            <td>
                <div class="row-actions">
                    <button class="btn-icon edit" title="Edit Entry" onclick="editFoundItem('${item.id}', '${item.description.replace(/'/g, "\\'")}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon delete" title="Remove Entry" onclick="deleteFoundItem('${item.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
    tbody.appendChild(row);
  });
}

window.editFoundItem = (id, oldDesc) => {
  const newDesc = prompt("Update Item Description:", oldDesc);
  if (!newDesc || newDesc === oldDesc) return;

  fetch(`${API_BASE}/found-luggage/${id}`, {
    method: 'PUT',
    headers: {
      "Authorization": `Bearer ${AUTH_TOKEN}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ description: newDesc })
  })
    .then(res => res.json())
    .then(data => {
      showAlert(data.message, "success");
      fetchFoundItems();
    })
    .catch(() => showAlert("Failed to update item.", "error"));
};

window.deleteFoundItem = (id) => {
  if (!confirm("Are you sure you want to remove this found item record?")) return;

  fetch(`${API_BASE}/found-luggage/${id}`, {
    method: 'DELETE',
    headers: { "Authorization": `Bearer ${AUTH_TOKEN}` }
  })
    .then(res => res.json())
    .then(data => {
      showAlert(data.message, "success");
      fetchFoundItems();
    })
    .catch(() => showAlert("Failed to delete item.", "error"));
};

/** Render Reports Table */
function renderReports(reports) {
  const tbody = document.querySelector('#lost-reports-table tbody');
  tbody.innerHTML = "";

  if (reports.length === 0) {
    tbody.innerHTML = "<tr><td colspan='4' style='text-align:center; padding: 2rem;'><p class='muted'>No relevant lost reports found for this depot pathing.</p></td></tr>";
    return;
  }

  reports.forEach(r => {
    const row = document.createElement('tr');
    const statusClass = r.status.replace("_", "-");
    row.innerHTML = `
            <td>
                <div class="item-cell">
                    <strong>${r.item_name}</strong>
                    <div style="font-size:0.75rem; margin-top:4px;">
                        <span style="color:#2563EB; font-weight:600;">${r.source_depot_id}</span> 
                        <span style="color:#9CA3AF;">&rarr;</span> 
                        <span style="color:#2563EB; font-weight:600;">${r.destination_depot_id}</span>
                    </div>
                    <small class="muted"><i class="fas fa-calendar-day"></i> Travel Date: ${r.date_lost}</small>
                </div>
            </td>
            <td>
                <div class="user-cell">
                    <span style="display:block; font-weight:500;"><i class="fas fa-phone"></i> ${r.contact_phone}</span>
                    <small class="muted">Ref: ${r.id.substring(18)}</small>
                </div>
            </td>
            <td>
                <button onclick="showMatches('${r.id}', '${r.item_name.replace(/'/g, "\\'")}')" class="action-btn" style="background:#7C3AED; color:white; border:none; border-radius:4px; padding:6px 12px; font-size:0.8rem; cursor:pointer;">
                    <i class="fas fa-magic"></i> AI Analysis
                </button>
            </td>
            <td>
                <select onchange="updateReportStatus('${r.id}', this.value)" class="status-select-official" style="padding:4px; border-radius:4px; border:1px solid #ddd; font-size:0.85rem; background: ${getStatusColor(r.status)}">
                    <option value="reported" ${r.status === 'reported' ? 'selected' : ''}>Reported</option>
                    <option value="under_review" ${r.status === 'under_review' ? 'selected' : ''}>Under Review</option>
                    <option value="found" ${r.status === 'found' ? 'selected' : ''}>Found</option>
                    <option value="returned" ${r.status === 'returned' ? 'selected' : ''}>Returned</option>
                </select>
            </td>
        `;
    tbody.appendChild(row);
  });
}

function getStatusColor(status) {
  switch (status) {
    case 'reported': return '#FFEDD5';
    case 'under_review': return '#FEF9C3';
    case 'found': return '#DCFCE7';
    case 'returned': return '#DBEAFE';
    default: return 'white';
  }
}

/** Update Status via API */
window.updateReportStatus = (reportId, newStatus) => {
  fetch(`${API_BASE}/update-status`, {
    method: 'PUT',
    headers: {
      "Authorization": `Bearer ${AUTH_TOKEN}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ report_id: reportId, status: newStatus })
  })
    .then(res => res.json())
    .then(data => {
      showAlert("✅ Status updated successfully!", "success");
      fetchReports(); // Refresh data
    })
    .catch(() => showAlert("Failed to update status.", "error"));
};

/** Show AI Matches Modal */
window.showMatches = (reportId, itemName) => {
  const modal = document.getElementById('match-modal');
  const container = document.getElementById('match-results-container');

  container.innerHTML = "<div class='loader-spinner'></div> <p>AI is analyzing descriptions for potential matches...</p>";
  modal.classList.remove('hidden');

  fetch(`${API_BASE}/matches/${reportId}`, {
    headers: { "Authorization": `Bearer ${AUTH_TOKEN}` }
  })
    .then(res => res.json())
    .then(data => {
      const matches = data.matches || [];
      if (matches.length === 0) {
        container.innerHTML = "<p>No potential matches found in the global database for this item.</p>";
        return;
      }

      container.innerHTML = matches.map(m => `
            <div class="match-card">
                <div class="match-score">${m.match_score}% Match</div>
                <div class="match-body">
                    <img src="${m.photo_url}" class="match-img" alt="Found Item">
                    <div class="match-info">
                        <strong>Found on: ${m.found_date}</strong>
                        <p>${m.description}</p>
                        <button class="btn-claim-action" onclick="claimMatch('${reportId}', '${m.id}')">
                            <i class="fas fa-hand-holding-heart"></i> Verify & Notify Passenger
                        </button>
                    </div>
                </div>
            </div>
        `).join("");
    })
    .catch(err => {
      console.error("Match error:", err);
      container.innerHTML = "<p class='error'>Failed to retrieve AI matches.</p>";
    });
};

/** Claim/Verify Match */
window.claimMatch = (lostId, foundId) => {
  showAlert("Verification notification sent to passenger (Mocked).", "success");
  // In a real system, this would update both reports and trigger SMS/Email
};

/** Setup SocketIO for Real-time Notifications */
function setupSocket() {
  socket = io();

  // Join room for this specific depot (Wait for manager info to get depot_id)
  fetch("/api/auth/me", {
    headers: { "Authorization": `Bearer ${AUTH_TOKEN}` }
  })
    .then(res => res.json())
    .then(user => {
      if (user.assigned_depot_id) {
        socket.emit("join", { room: `depot_${user.assigned_depot_id}` });
        console.log(`[Socket] Joined room: depot_${user.assigned_depot_id}`);
      }
    });

  socket.on("new_lost_report", (data) => {
    showAlert(`🚨 New Lost Luggage reported passing through this depot: <strong>${data.report.item_name}</strong>`, "info");
    fetchReports(); // Refresh list
  });
}

/** Setup Event Listeners */
function setupEventListeners() {
  // Post Found Luggage
  document.getElementById('found-luggage-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const btn = e.target.querySelector('button');
    btn.disabled = true;
    btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Processing...`;

    fetch(`${API_BASE}/found-luggage`, {
      method: 'POST',
      headers: { "Authorization": `Bearer ${AUTH_TOKEN}` },
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        if (data.id) {
          showAlert("✅ Found item registered successfully.", "success");
          e.target.reset();
          fetchFoundItems();
        } else {
          showAlert(data.message || "Registry failed.", "error");
        }
      })
      .catch(err => {
        console.error("Post error:", err);
        showAlert("Network error.", "error");
      })
      .finally(() => {
        btn.disabled = false;
        btn.innerHTML = `<i class="fas fa-upload"></i> Upload & Post Item`;
      });
  });

  // Logout
  const logoutBtn = document.getElementById('manager-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      localStorage.removeItem('jwt_token');
      localStorage.removeItem('user_role');
      window.location.href = "/login.html";
    });
  }

  // Close modal on click outside
  window.addEventListener('click', (event) => {
    const modal = document.getElementById('match-modal');
    if (event.target === modal) {
      modal.classList.add('hidden');
    }
  });

  // Re-attach close buttons via class targeting
  document.querySelectorAll('.close-modal').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('match-modal').classList.add('hidden');
    });
  });
}

function updateStats(reports) {
  document.getElementById('stat-lost-count').textContent = reports.length;
}

function showAlert(msg, type) {
  const container = document.getElementById('manager-alert');
  container.innerHTML = `<div class="alert ${type}">${msg}</div>`;
  setTimeout(() => { container.innerHTML = ""; }, 6000);
}

document.addEventListener('DOMContentLoaded', initManager);
