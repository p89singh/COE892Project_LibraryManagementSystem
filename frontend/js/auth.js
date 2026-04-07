function getCurrentUser() {
  const raw = localStorage.getItem("user");
  return raw ? JSON.parse(raw) : null;
}

function logoutUser() {
  localStorage.removeItem("user");
  window.location.href = "/login";
}

function updateUserBanner(elementId) {
  const user = getCurrentUser();
  const el = document.getElementById(elementId);
  if (!el) return;

  if (user) {
    el.textContent = `Signed in as ${user.full_name} (${user.email})`;
  } else {
    el.textContent = "Not signed in";
  }
}

async function registerUser() {
  const full_name = document.getElementById("full_name").value.trim();
  const email = document.getElementById("email").value.trim();
  const message = document.getElementById("message");

  if (!full_name || !email) {
    message.textContent = "Please enter your full name and email.";
    return;
  }

  try {
    const user = await apiPost("/auth/register", { full_name, email });
    localStorage.setItem("user", JSON.stringify(user));
    message.textContent = "Registration successful. Redirecting...";
    setTimeout(() => {
      window.location.href = "/catalog";
    }, 700);
  } catch (err) {
    message.textContent = "Registration failed: " + err.message;
  }
}

async function loginUser() {
  const email = document.getElementById("email").value.trim();
  const message = document.getElementById("message");

  if (!email) {
    message.textContent = "Please enter your email.";
    return;
  }

  try {
    const user = await apiPost("/auth/login", { email });
    localStorage.setItem("user", JSON.stringify(user));
    message.textContent = "Login successful. Redirecting...";
    setTimeout(() => {
      window.location.href = "/catalog";
    }, 700);
  } catch (err) {
    message.textContent = "Login failed: " + err.message;
  }
}