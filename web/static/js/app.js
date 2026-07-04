const API_BASE = "/api/expenses";

// -------------------------------------------------------
// Sidebar navigation — show/hide panels
// -------------------------------------------------------

const navLinks = document.querySelectorAll(".nav-link");
const panels   = document.querySelectorAll(".panel");

navLinks.forEach((link) => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    const target = link.dataset.section;

    panels.forEach((p) => p.classList.add("hidden"));
    navLinks.forEach((l) => l.classList.remove("active"));

    const targetPanel = document.getElementById(target);
    if (targetPanel) targetPanel.classList.remove("hidden");
    link.classList.add("active");
  });
});

// -------------------------------------------------------
// CSV Upload — drag & drop + file picker
// -------------------------------------------------------

const dropZone    = document.getElementById("drop-zone");
const csvInput    = document.getElementById("csv-input");
const fileInfo    = document.getElementById("file-info");
const fileNameEl  = document.getElementById("file-name");
const clearBtn    = document.getElementById("clear-file");
const uploadBtn   = document.getElementById("upload-btn");
const progressWrap = document.getElementById("progress-wrap");
const progressBar  = document.getElementById("progress-bar");
const progressLabel = document.getElementById("progress-label");
const uploadStatus = document.getElementById("upload-status");
const csvResults  = document.getElementById("csv-results");
const resultsMeta = document.getElementById("results-meta");
const csvThead    = document.getElementById("csv-thead");
const csvTbody    = document.getElementById("csv-tbody");

let selectedFile = null;

// Click on drop zone opens file picker
dropZone.addEventListener("click", () => csvInput.click());
dropZone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") csvInput.click();
});

// Drag events
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("drag-over");
});
["dragleave", "dragend"].forEach((evt) =>
  dropZone.addEventListener(evt, () => dropZone.classList.remove("drag-over"))
);
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) applyFile(file);
});

// File input change
csvInput.addEventListener("change", () => {
  if (csvInput.files[0]) applyFile(csvInput.files[0]);
});

// Clear selection
clearBtn.addEventListener("click", clearFile);

function applyFile(file) {
  selectedFile = file;
  fileNameEl.textContent = file.name;
  fileInfo.classList.remove("hidden");
  uploadBtn.disabled = false;
  setStatus("upload-status", "");
  csvResults.classList.add("hidden");
}

function clearFile() {
  selectedFile = null;
  csvInput.value = "";
  fileInfo.classList.add("hidden");
  uploadBtn.disabled = true;
  progressWrap.classList.add("hidden");
  setProgress(0);
  setStatus("upload-status", "");
  csvResults.classList.add("hidden");
}

// -------------------------------------------------------
// Upload with XHR so we can track real upload progress
// -------------------------------------------------------

uploadBtn.addEventListener("click", () => {
  if (!selectedFile) return;

  const formData = new FormData();
  formData.append("file", selectedFile);

  uploadBtn.disabled = true;
  progressWrap.classList.remove("hidden");
  setProgress(0);
  setStatus("upload-status", "");
  csvResults.classList.add("hidden");

  const xhr = new XMLHttpRequest();

  xhr.upload.addEventListener("progress", (e) => {
    if (e.lengthComputable) {
      const pct = Math.round((e.loaded / e.total) * 100);
      setProgress(pct);
    }
  });

  xhr.addEventListener("load", () => {
    setProgress(100);
    if (xhr.status === 200) {
      const data = JSON.parse(xhr.responseText);
      renderCSVResults(data);
      setStatus("upload-status", `Parsed ${data.rows} row(s) from "${data.filename}".`);
    } else {
      let detail = "Upload failed.";
      try { detail = JSON.parse(xhr.responseText).detail || detail; } catch (_) {}
      setStatus("upload-status", detail, true);
    }
    uploadBtn.disabled = false;
  });

  xhr.addEventListener("error", () => {
    setStatus("upload-status", "Network error — upload could not complete.", true);
    uploadBtn.disabled = false;
  });

  xhr.open("POST", "/api/upload-csv");
  xhr.send(formData);
});

function setProgress(pct) {
  progressBar.style.width = pct + "%";
  progressLabel.textContent = pct + "%";
}

function renderCSVResults(data) {
  // Meta line
  resultsMeta.innerHTML =
    `<strong>${data.rows}</strong> rows &nbsp;&bull;&nbsp; ` +
    `<strong>${data.columns.length}</strong> columns &nbsp;&bull;&nbsp; ` +
    `File: <strong>${escapeHtml(data.filename)}</strong>`;

  // Build header
  const trHead = document.createElement("tr");
  data.columns.forEach((col) => {
    const th = document.createElement("th");
    th.textContent = col;
    trHead.appendChild(th);
  });
  csvThead.innerHTML = "";
  csvThead.appendChild(trHead);

  // Build body (cap at 200 rows to keep the DOM light)
  csvTbody.innerHTML = "";
  const displayed = data.data.slice(0, 200);
  displayed.forEach((row) => {
    const tr = document.createElement("tr");
    data.columns.forEach((col) => {
      const td = document.createElement("td");
      td.textContent = row[col] ?? "";
      tr.appendChild(td);
    });
    csvTbody.appendChild(tr);
  });

  csvResults.classList.remove("hidden");
}

// -------------------------------------------------------
// Helpers
// -------------------------------------------------------

function setStatus(elementId, message, isError = false) {
  const el = document.getElementById(elementId);
  el.textContent = message;
  el.className = "status-msg " + (isError ? "error" : "success");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

// -------------------------------------------------------
// POST — Create a new expense
// -------------------------------------------------------

document.getElementById("add-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const body = {
    description: document.getElementById("description").value.trim(),
    amount: parseFloat(document.getElementById("amount").value),
    category: document.getElementById("category").value.trim(),
  };

  try {
    const res = await fetch(API_BASE, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create expense");
    }

    const data = await res.json();
    setStatus("add-status", `Expense #${data.id} created successfully!`);
    e.target.reset();
  } catch (err) {
    setStatus("add-status", err.message, true);
  }
});

// -------------------------------------------------------
// PUT — Update an existing expense
// -------------------------------------------------------

document.getElementById("update-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const id = document.getElementById("update-id").value;
  const patch = {};
  const desc     = document.getElementById("update-description").value.trim();
  const amount   = document.getElementById("update-amount").value;
  const category = document.getElementById("update-category").value.trim();

  if (desc) patch.description = desc;
  if (amount !== "") patch.amount = parseFloat(amount);
  if (category) patch.category = category;

  try {
    const res = await fetch(`${API_BASE}/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to update expense");
    }

    const data = await res.json();
    setStatus("update-status", `Expense #${data.id} updated successfully!`);
    e.target.reset();
  } catch (err) {
    setStatus("update-status", err.message, true);
  }
});

// -------------------------------------------------------
// GET — Load all expenses
// -------------------------------------------------------

document.getElementById("load-btn").addEventListener("click", async () => {
  const tbody   = document.getElementById("expense-tbody");
  const table   = document.getElementById("expense-table");
  const emptyMsg = document.getElementById("empty-msg");

  try {
    const res = await fetch(API_BASE);
    if (!res.ok) throw new Error("Failed to fetch expenses");

    const data = await res.json();
    const list = data.expenses;

    tbody.innerHTML = "";

    if (list.length === 0) {
      table.classList.add("hidden");
      emptyMsg.classList.remove("hidden");
      return;
    }

    emptyMsg.classList.add("hidden");
    table.classList.remove("hidden");

    list.forEach((exp) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${exp.id}</td>
        <td>${escapeHtml(exp.description)}</td>
        <td>$${exp.amount.toFixed(2)}</td>
        <td>${escapeHtml(exp.category)}</td>
      `;
      tbody.appendChild(row);
    });
  } catch (err) {
    emptyMsg.textContent = err.message;
    emptyMsg.className = "status-msg error";
    emptyMsg.classList.remove("hidden");
    table.classList.add("hidden");
  }
});

