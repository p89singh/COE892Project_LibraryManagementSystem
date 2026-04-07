function getAdminPayload(prefix) {
  return {
    title: document.getElementById(`${prefix}_title`).value.trim(),
    author: document.getElementById(`${prefix}_author`).value.trim(),
    genre: document.getElementById(`${prefix}_genre`).value.trim() || null,
    media_type: document.getElementById(`${prefix}_media_type`).value.trim(),
    isbn: document.getElementById(`${prefix}_isbn`).value.trim() || null,
    publication_year: document.getElementById(`${prefix}_publication_year`).value
      ? parseInt(document.getElementById(`${prefix}_publication_year`).value, 10)
      : null,
    description: document.getElementById(`${prefix}_description`).value.trim() || null,
    total_copies: document.getElementById(`${prefix}_total_copies`).value
      ? parseInt(document.getElementById(`${prefix}_total_copies`).value, 10)
      : 1
  };
}

async function createItem() {
  const message = document.getElementById("adminAddMessage");
  const payload = getAdminPayload("add");

  if (!payload.title || !payload.author || !payload.media_type) {
    message.textContent = "Title, author, and media type are required.";
    return;
  }

  try {
    const result = await apiPost("/items", payload);
    message.textContent = `Item created with ID ${result.id}.`;
  } catch (err) {
    message.textContent = "Create failed: " + err.message;
  }
}

async function loadItemForEdit() {
  const id = document.getElementById("edit_id").value;
  const message = document.getElementById("adminEditMessage");

  if (!id) {
    message.textContent = "Please enter an item ID.";
    return;
  }

  try {
    const item = await apiGet(`/items/${id}`);
    document.getElementById("edit_title").value = item.title || "";
    document.getElementById("edit_author").value = item.author || "";
    document.getElementById("edit_genre").value = item.genre || "";
    document.getElementById("edit_media_type").value = item.media_type || "";
    document.getElementById("edit_isbn").value = item.isbn || "";
    document.getElementById("edit_publication_year").value = item.publication_year || "";
    document.getElementById("edit_description").value = item.description || "";
    document.getElementById("edit_total_copies").value = item.total_copies || 1;
    message.textContent = "Item loaded.";
  } catch (err) {
    message.textContent = "Load failed: " + err.message;
  }
}

async function updateItem() {
  const id = document.getElementById("edit_id").value;
  const message = document.getElementById("adminEditMessage");

  if (!id) {
    message.textContent = "Please enter an item ID.";
    return;
  }

  const payload = getAdminPayload("edit");

  try {
    await apiPut(`/items/${id}`, payload);
    message.textContent = `Item ${id} updated successfully.`;
  } catch (err) {
    message.textContent = "Update failed: " + err.message;
  }
}

async function deleteItem() {
  const id = document.getElementById("edit_id").value;
  const message = document.getElementById("adminEditMessage");

  if (!id) {
    message.textContent = "Please enter an item ID.";
    return;
  }

  try {
    await apiDelete(`/items/${id}`);
    message.textContent = `Item ${id} deleted successfully.`;
  } catch (err) {
    message.textContent = "Delete failed: " + err.message;
  }
}