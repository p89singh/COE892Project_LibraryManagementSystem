function renderLoans(loans) {
  const container = document.getElementById("loansContainer");
  container.innerHTML = "";

  if (!loans.length) {
    container.innerHTML = `<div class="empty-card"><p>No loans found.</p></div>`;
    return;
  }

  loans.forEach(loan => {
    container.innerHTML += `
      <div class="card">
        <p><strong>Loan ID:</strong> ${loan.id}</p>
        <p><strong>Item ID:</strong> ${loan.item_id}</p>
        <p><strong>Status:</strong> ${loan.status}</p>
        <p><strong>Borrowed:</strong> ${loan.borrowed_at}</p>
        <p><strong>Due:</strong> ${loan.due_date}</p>
        <div class="actions">
          ${loan.status === "ACTIVE" ? `<button class="btn" onclick="renewBook(${loan.item_id})">Renew</button>` : ""}
          ${loan.status === "ACTIVE" ? `<button class="btn btn-secondary" onclick="returnBook(${loan.item_id})">Return</button>` : ""}
        </div>
      </div>
    `;
  });
}

function renderReservations(reservations) {
  const container = document.getElementById("reservationsContainer");
  container.innerHTML = "";

  if (!reservations.length) {
    container.innerHTML = `<div class="empty-card"><p>No reservations found.</p></div>`;
    return;
  }

  reservations.forEach(r => {
    container.innerHTML += `
      <div class="card">
        <p><strong>Reservation ID:</strong> ${r.id}</p>
        <p><strong>Item ID:</strong> ${r.item_id}</p>
        <p><strong>Status:</strong> ${r.status}</p>
        <p><strong>Reserved At:</strong> ${r.reserved_at}</p>
        <p><strong>Queue Position:</strong> ${r.queue_position ?? "N/A"}</p>
      </div>
    `;
  });
}

async function loadLibraryData() {
  const user = getCurrentUser();

  if (!user) {
    window.location.href = "/login";
    return;
  }

  try {
    const loans = await apiGet(`/loans/${user.id}`);
    const reservations = await apiGet(`/reservations/${user.id}`);
    renderLoans(loans);
    renderReservations(reservations);
  } catch (err) {
    document.getElementById("loansContainer").innerHTML =
      `<div class="empty-card"><p>Failed to load loans: ${err.message}</p></div>`;
    document.getElementById("reservationsContainer").innerHTML =
      `<div class="empty-card"><p>Failed to load reservations: ${err.message}</p></div>`;
  }
}

window.onload = () => {
  updateUserBanner("libraryUserBanner");
  loadLibraryData();
};