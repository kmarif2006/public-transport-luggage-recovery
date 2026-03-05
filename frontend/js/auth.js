const API_BASE = "/api";

// ── Token helpers ─────────────────────────────────────────────────────────────
function setToken(token, role) {
  localStorage.setItem("jwt_token", token);
  localStorage.setItem("user_role", role || "user");
}

function getToken() {
  return localStorage.getItem("jwt_token");
}

function clearToken() {
  localStorage.removeItem("jwt_token");
  localStorage.removeItem("user_role");
}

// ── Alert helper ──────────────────────────────────────────────────────────────
function showAlert(containerId, message, type = "error") {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `<div class="alert ${type}">${message}</div>`;
}

// ── Redirect if already logged in (on auth pages) ────────────────────────────
function redirectIfLoggedIn() {
  const token = getToken();
  if (token) {
    const role = localStorage.getItem("user_role");
    window.location.href = role === "manager" ? "/manager_dashboard.html" : "/map.html";
  }
}

// ── OAuth callback handling ───────────────────────────────────────────────────
function checkOAuthCallback() {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get("code");
  if (!code) return;

  const path = window.location.pathname;
  if (path.includes("/google/callback")) {
    handleOAuthCallback("google", code);
  } else if (path.includes("/microsoft/callback")) {
    handleOAuthCallback("microsoft", code);
  }
}

async function handleOAuthCallback(provider, code) {
  console.log(`[AUTH] Handling ${provider} OAuth callback...`);
  try {
    const res = await fetch(`${API_BASE}/auth/${provider}/callback?code=${code}`);
    const data = await res.json();
    if (!res.ok) {
      showAlert("login-alert", data.message || "OAuth login failed", "error");
      return;
    }
    setToken(data.token, data.user.role);
    window.location.href = data.user.role === "manager" ? "/manager_dashboard.html" : "/map.html";
  } catch (err) {
    console.error("[AUTH] OAuth error:", err);
    showAlert("login-alert", "Network error during OAuth login", "error");
  }
}

// ── Email/password login ──────────────────────────────────────────────────────
async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const submitBtn = e.target.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="loading"></span> Signing in...';

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) {
      showAlert("login-alert", data.message || "Login failed", "error");
      submitBtn.disabled = false;
      submitBtn.textContent = "Sign In";
      return;
    }
    setToken(data.token, data.user.role);
    window.location.href = data.user.role === "manager" ? "/manager_dashboard.html" : "/map.html";
  } catch (err) {
    console.error("[AUTH] Login error:", err);
    showAlert("login-alert", "Network error during login. Please try again.", "error");
    submitBtn.disabled = false;
    submitBtn.textContent = "Sign In";
  }
}

// ── Signup ────────────────────────────────────────────────────────────────────
async function handleSignup(e) {
  e.preventDefault();
  const name = document.getElementById("name").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const confirmPassword = document.getElementById("confirm-password").value;
  const role = "user"; // Hardcoded for public signup
  const submitBtn = e.target.querySelector('button[type="submit"]');

  if (password !== confirmPassword) {
    showAlert("signup-alert", "Passwords do not match.", "error");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="loading"></span> Creating account...';

  try {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password, role }),
    });
    const data = await res.json();
    if (!res.ok) {
      showAlert("signup-alert", data.message || "Signup failed", "error");
      submitBtn.disabled = false;
      submitBtn.textContent = "Create Account";
      return;
    }
    setToken(data.token, data.user.role);
    window.location.href = data.user.role === "manager" ? "/manager_dashboard.html" : "/map.html";
  } catch (err) {
    console.error("[AUTH] Signup error:", err);
    showAlert("signup-alert", "Network error during signup. Please try again.", "error");
    submitBtn.disabled = false;
    submitBtn.textContent = "Create Account";
  }
}

// ── OAuth initiation ──────────────────────────────────────────────────────────
async function startOAuth(provider) {
  const endpoint =
    provider === "google" ? `${API_BASE}/auth/google/url` : `${API_BASE}/auth/microsoft/url`;
  try {
    const res = await fetch(endpoint);
    const data = await res.json();
    if (data.url) {
      window.location.href = data.url;
    } else {
      showAlert("login-alert", "OAuth not configured. Please use email/password login.", "warning");
    }
  } catch {
    showAlert("login-alert", "Could not initiate OAuth. Please use email/password login.", "warning");
  }
}

// ── Event Binding ─────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  checkOAuthCallback();

  const loginForm = document.getElementById("login-form");
  const signupForm = document.getElementById("signup-form");
  const googleBtn = document.getElementById("google-login");
  const msBtn = document.getElementById("ms-login");
  const managerLoginForm = document.getElementById("manager-login-form");
  const managerGoogleBtn = document.getElementById("manager-google-login");
  const managerMsBtn = document.getElementById("manager-ms-login");

  // On login/signup pages: redirect if already authenticated
  if (loginForm || signupForm || managerLoginForm) {
    redirectIfLoggedIn();
  }

  if (loginForm) loginForm.addEventListener("submit", handleLogin);
  if (signupForm) signupForm.addEventListener("submit", handleSignup);
  if (googleBtn) googleBtn.addEventListener("click", () => startOAuth("google"));
  if (msBtn) msBtn.addEventListener("click", () => startOAuth("microsoft"));

  if (managerLoginForm) {
    managerLoginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value;
      try {
        const res = await fetch(`${API_BASE}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if (!res.ok) {
          showAlert("manager-login-alert", data.message || "Login failed", "error");
          return;
        }
        if (data.user.role !== "manager") {
          showAlert("manager-login-alert", "Access denied. Manager account required.", "error");
          return;
        }
        setToken(data.token, data.user.role);
        window.location.href = "/manager_dashboard.html";
      } catch {
        showAlert("manager-login-alert", "Network error during login", "error");
      }
    });
  }

  if (managerGoogleBtn) managerGoogleBtn.addEventListener("click", () => startOAuth("google"));
  if (managerMsBtn) managerMsBtn.addEventListener("click", () => startOAuth("microsoft"));
});
