const notes = [];
const questions = [];

const notesInput = document.getElementById("notesInput");
const questionsInput = document.getElementById("questionsInput");

const notesDrop = document.getElementById("notesDrop");
const questionsDrop = document.getElementById("questionsDrop");

const notesList = document.getElementById("notesList");
const questionsList = document.getElementById("questionsList");

const notesTitle = document.getElementById("notesTitle");
const questionsTitle = document.getElementById("questionsTitle");

const outputBox = document.getElementById("outputBox");
const outputPlaceholder = document.getElementById("outputPlaceholder");
const outputList = document.getElementById("outputList");

const terminal = document.getElementById("terminal");
const generateButton = document.getElementById("generateButton");

function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function addFiles(target, files) {
    for (const file of files) {
        const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
        if (!isPdf) continue;

        // Avoid adding the same file twice.
        const alreadyAdded = target.some(
            existing => existing.name === file.name && existing.size === file.size
        );

        if (!alreadyAdded) {
            target.push(file);
        }
    }

    renderFiles();
}

function renderFiles() {
    notesTitle.textContent = `Added Notes (${notes.length})`;
    notesList.innerHTML = "";

    if (notes.length === 0) {
        notesList.innerHTML = `<div class="empty-note">No notes added yet.</div>`;
    } else {
        notes.forEach((file, index) => {
            notesList.appendChild(createFileItem(file, index, "notes"));
        });
    }

    questionsTitle.textContent = `Added Questions (${questions.length})`;
    questionsList.innerHTML = "";

    if (questions.length === 0) {
        questionsList.innerHTML = `<div class="empty-note">No question papers added yet.</div>`;
    } else {
        questions.forEach((file, index) => {
            questionsList.appendChild(createFileItem(file, index, "questions"));
        });
    }
}

function createFileItem(file, index, type) {
    const item = document.createElement("div");
    item.className = "file-item";

    item.innerHTML = `
        <div class="file-icon">▱</div>
        <div class="file-info">
            <div class="file-name" title="${escapeHtml(file.name)}">
                ${escapeHtml(file.name)}
            </div>
            <div class="file-size">${formatSize(file.size)}</div>
        </div>
        <button class="remove-file" type="button" title="Remove">×</button>
    `;

    item.querySelector(".remove-file").addEventListener("click", () => {
        if (type === "notes") {
            notes.splice(index, 1);
        } else {
            questions.splice(index, 1);
        }
        renderFiles();
    });

    return item;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

notesInput.addEventListener("change", () => {
    addFiles(notes, [...notesInput.files]);
    notesInput.value = "";
});

questionsInput.addEventListener("change", () => {
    addFiles(questions, [...questionsInput.files]);
    questionsInput.value = "";
});

function setupDropZone(zone, target) {
    zone.addEventListener("dragover", (event) => {
        event.preventDefault();
        zone.classList.add("dragging");
    });

    zone.addEventListener("dragleave", () => {
        zone.classList.remove("dragging");
    });

    zone.addEventListener("drop", (event) => {
        event.preventDefault();
        zone.classList.remove("dragging");
        addFiles(target, [...event.dataTransfer.files]);
    });
}

setupDropZone(notesDrop, notes);
setupDropZone(questionsDrop, questions);

document.getElementById("showKey").addEventListener("click", () => {
    const key = document.getElementById("apiKey");
    key.type = key.type === "password" ? "text" : "password";
});

// ---- Activity log ----

function log(message, active = false) {
    const line = document.createElement("div");
    line.className = `terminal-line${active ? " active" : ""}`;
    line.textContent = message;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
}

// ---- Output list ----
// Call this with an array of { name, blob } (or { name, url }) once the
// backend actually returns generated PDFs. Each entry gets its own
// download button. Re-calling replaces the previous output list.

function renderOutputFiles(files) {
    outputList.innerHTML = "";

    if (!files || files.length === 0) {
        outputList.classList.remove("visible");
        outputPlaceholder.style.display = "flex";
        return;
    }

    outputPlaceholder.style.display = "none";
    outputList.classList.add("visible");

    files.forEach((file) => {
        const row = document.createElement("div");
        row.className = "output-file";

        row.innerHTML = `
            <div class="file-icon">▤</div>
            <div class="output-file-name" title="${escapeHtml(file.name)}">
                ${escapeHtml(file.name)}
            </div>
            <button class="download-button" type="button" title="Download">⬇</button>
        `;

        row.querySelector(".download-button").addEventListener("click", () => {
            downloadFile(file);
        });

        outputList.appendChild(row);
    });
}

function downloadFile(file) {
    // file.url: already-hosted URL from the backend.
    // file.blob: a Blob returned directly from the backend response.
    const href = file.url || (file.blob ? URL.createObjectURL(file.blob) : null);
    if (!href) return;

    const link = document.createElement("a");
    link.href = href;
    link.download = file.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// ---- Generate ----

generateButton.addEventListener("click", () => {
    if (notes.length === 0) {
        log("No notes selected.");
        return;
    }

    if (questions.length === 0) {
        log("No question papers selected.");
        return;
    }

    const apiKey = document.getElementById("apiKey").value.trim();
    if (!apiKey) {
        log("Gemini API key is required.");
        return;
    }

    const rpm = document.getElementById("rpm").value;
    const model = document.getElementById("model").value;

    log(`Ready to process ${notes.length} note file(s) and ${questions.length} question file(s).`);
    log(`Model: ${model} | RPM: ${rpm}`);

    // ---------------------------------------------------------------
    // Backend integration point.
    //
    // Wire the actual pipeline call here. Suggested shape:
    //
    //   generateButton.disabled = true;
    //   const result = await runPipeline({ notes, questions, apiKey, model, rpm, onLog: log });
    //   renderOutputFiles(result.files);
    //   generateButton.disabled = false;
    //
    // Use log("...") to stream pipeline progress into the Activity box,
    // e.g. log("loaded 121 chunks"), log("processing dbms1.pdf").
    // ---------------------------------------------------------------
    log("Backend connection is not configured yet.");
});

renderFiles();