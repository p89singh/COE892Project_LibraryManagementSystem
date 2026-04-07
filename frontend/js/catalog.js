function renderBooks(books) {
  const container = document.getElementById("booksContainer");
  container.innerHTML = "";

  if (!books.length) {
    container.innerHTML = `<div class="empty-card"><p>No items found.</p></div>`;
    return;
  }

  books.forEach(book => {
    container.innerHTML += `
      <div class="card book-card">
        <h3>${book.title}</h3>
        <p class="book-meta"><strong>Author:</strong> ${book.author}</p>
        <p class="book-meta"><strong>Genre:</strong> ${book.genre || "N/A"}</p>
        <p class="book-meta"><strong>Media Type:</strong> ${book.media_type || "N/A"}</p>
        <p class="book-meta"><strong>Year:</strong> ${book.publication_year || "N/A"}</p>
        <p class="book-meta"><strong>ISBN:</strong> ${book.isbn || "N/A"}</p>
        <p class="book-meta"><strong>Description:</strong> ${book.description || "No description"}</p>
        <p class="book-meta"><strong>Total Copies:</strong> ${book.total_copies ?? "N/A"}</p>
        <p class="status">Availability: ${book.availability}</p>
        <div class="actions">
          <button class="btn" onclick="borrowBook(${book.id})">Borrow</button>
          <button class="btn btn-secondary" onclick="reserveBook(${book.id})">Reserve</button>
        </div>
      </div>
    `;
  });
}

async function loadBooks() {
  try {
    const books = await apiGet("/search");
    renderBooks(books);
  } catch (err) {
    document.getElementById("booksContainer").innerHTML =
      `<div class="empty-card"><p>Failed to load catalog: ${err.message}</p></div>`;
  }
}

async function searchBooks() {
  const q = document.getElementById("searchInput").value.trim();

  try {
    const books = await apiGet(`/search?q=${encodeURIComponent(q)}`);
    renderBooks(books);
  } catch (err) {
    document.getElementById("booksContainer").innerHTML =
      `<div class="empty-card"><p>Search failed: ${err.message}</p></div>`;
  }
}

window.onload = () => {
  updateUserBanner("userBanner");
  loadBooks();
};