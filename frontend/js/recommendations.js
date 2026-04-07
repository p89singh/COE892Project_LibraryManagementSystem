function renderRecommendations(items) {
  const container = document.getElementById("recommendationsContainer");
  container.innerHTML = "";

  if (!items.length) {
    container.innerHTML = `<div class="empty-card"><p>No recommendations available.</p></div>`;
    return;
  }

  items.forEach(item => {
    container.innerHTML += `
      <div class="card book-card">
        <h3>${item.title}</h3>
        <p class="book-meta"><strong>Author:</strong> ${item.author}</p>
        <p class="book-meta"><strong>Genre:</strong> ${item.genre || "N/A"}</p>
        <p class="book-meta"><strong>Media Type:</strong> ${item.media_type || "N/A"}</p>
        <p class="book-meta"><strong>Description:</strong> ${item.description || "No description"}</p>
      </div>
    `;
  });
}

async function loadRecommendations() {
  const user = getCurrentUser();

  if (!user) {
    window.location.href = "/login";
    return;
  }

  try {
    const items = await apiGet(`/recommendations/${user.id}`);
    renderRecommendations(items);
  } catch (err) {
    document.getElementById("recommendationsContainer").innerHTML =
      `<div class="empty-card"><p>Failed to load recommendations: ${err.message}</p></div>`;
  }
}

window.onload = () => {
  updateUserBanner("recommendationBanner");
  loadRecommendations();
};