async function borrowBook(itemId) {
  const user = getCurrentUser();

  if (!user) {
    alert("Please log in first.");
    window.location.href = "/login";
    return;
  }

  try {
    const result = await apiPost("/borrow", {
      user_id: user.id,
      item_id: itemId
    });

    alert(result.message || "Borrow successful");
    if (typeof loadBooks === "function") {
      await loadBooks();
    }
    if (typeof loadLibraryData === "function") {
      await loadLibraryData();
    }
  } catch (err) {
    alert("Borrow failed: " + err.message);
  }
}

async function reserveBook(itemId) {
  const user = getCurrentUser();

  if (!user) {
    alert("Please log in first.");
    window.location.href = "/login";
    return;
  }

  try {
    const result = await apiPost("/reserve", {
      user_id: user.id,
      item_id: itemId
    });

    alert(result.message || "Reservation successful");
    if (typeof loadBooks === "function") {
      await loadBooks();
    }
    if (typeof loadLibraryData === "function") {
      await loadLibraryData();
    }
  } catch (err) {
    alert("Reserve failed: " + err.message);
  }
}

async function returnBook(itemId) {
  const user = getCurrentUser();

  if (!user) {
    alert("Please log in first.");
    window.location.href = "/login";
    return;
  }

  try {
    const result = await apiPost("/return", {
      user_id: user.id,
      item_id: itemId
    });

    alert(result.message || "Return successful");
    if (typeof loadLibraryData === "function") {
      await loadLibraryData();
    }
    if (typeof loadBooks === "function") {
      await loadBooks();
    }
  } catch (err) {
    alert("Return failed: " + err.message);
  }
}

async function renewBook(itemId) {
  const user = getCurrentUser();

  if (!user) {
    alert("Please log in first.");
    window.location.href = "/login";
    return;
  }

  try {
    const result = await apiPost("/renew", {
      user_id: user.id,
      item_id: itemId
    });

    alert(result.message || "Renew successful");
    if (typeof loadLibraryData === "function") {
      await loadLibraryData();
    }
  } catch (err) {
    alert("Renew failed: " + err.message);
  }
}