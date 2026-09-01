const notes = [];
const questions = [];

const notesInput = document.getElementById("notesInput");
const questionsInput = document.getElementById("questionsInput");

const notesList = document.getElementById("notesList");
const questionsList = document.getElementById("questionsList");

const notesEmpty = document.getElementById("notesEmpty");
const questionsEmpty = document.getElementById("questionsEmpty");

const outputPlaceholder = document.getElementById("outputPlaceholder");
const outputList = document.getElementById("outputList");

const terminal = document.getElementById("terminal");
const generateButton = document.getElementById("generateButton");

function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function addFiles(target, files) {
    for (const file of files) {
        const isPdf =
            file.type === "application/pdf" ||
            file.name.toLowerCase().endsWith(".pdf");

        if (!isPdf) continue;

        const alreadyAdded = target.some(
            existing =>
                existing.name === file.name &&
                existing.size === file.size
        );

        if (!alreadyAdded) {
            target.push(file);
        }
    }

    renderFiles();
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

            <div class="file-size">
                ${formatSize(file.size)}
            </div>
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

function renderFiles() {
    notesList.innerHTML = "";
    questionsList.innerHTML = "";

    if (notes.length === 0) {
        notesEmpty.style.display = "flex";
        notesList.classList.remove("visible");
    } else {
        notesEmpty.style.display = "none";
        notesList.classList.add("visible");

        notes.forEach((file, index) => {
            notesList.appendChild(
                createFileItem(file, index, "notes")
            );
        });
    }

    if (questions.length === 0) {
        questionsEmpty.style.display = "flex";
        questionsList.classList.remove("visible");
    } else {
        questionsEmpty.style.display = "none";
        questionsList.classList.add("visible");

        questions.forEach((file, index) => {
            questionsList.appendChild(
                createFileItem(file, index, "questions")
            );
        });
    }
}

/* Buttons only — no drag and drop */
document.getElementById("addNotesButton").addEventListener("click", () => {
    notesInput.click();
});

document.getElementById("addQuestionsButton").addEventListener("click", () => {
    questionsInput.click();
});

notesInput.addEventListener("change", () => {
    addFiles(notes, [...notesInput.files]);
    notesInput.value = "";
});

questionsInput.addEventListener("change", () => {
    addFiles(questions, [...questionsInput.files]);
    questionsInput.value = "";
});


/* API key visibility */
document.getElementById("showKey").addEventListener("click", () => {
    const key = document.getElementById("apiKey");

    key.type =
        key.type === "password"
            ? "text"
            : "password";
});


/*
 * Activity
 *
 * Only ONE message exists at a time.
 * Calling log() replaces the previous message instead of
 * adding another line or growing the Activity card.
 */
function log(message) {
    terminal.innerHTML = "";

    const line = document.createElement("div");
    line.className = "terminal-line";
    line.textContent = message;

    terminal.appendChild(line);
}


/* Output list */
function renderOutputFiles(files) {
    outputList.innerHTML = "";

    if (!files || files.length === 0) {
        outputList.classList.remove("visible");
        outputPlaceholder.style.display = "block";
        return;
    }

    outputPlaceholder.style.display = "none";
    outputList.classList.add("visible");

    files.forEach((file) => {
        const row = document.createElement("div");
        row.className = "output-file";

        row.innerHTML = `
            <div class="file-icon">▤</div>

            <div class="output-file-name"
                 title="${escapeHtml(file.name)}">
                ${escapeHtml(file.name)}
            </div>

            <button class="download-button"
                    type="button"
                    title="Download">⬇</button>
        `;

        row.querySelector(".download-button")
            .addEventListener("click", () => {
                downloadFile(file);
            });

        outputList.appendChild(row);
    });
}

function downloadFile(file) {
    const href =
        file.url ||
        (file.blob ? URL.createObjectURL(file.blob) : null);

    if (!href) return;

    const link = document.createElement("a");
    link.href = href;
    link.download = file.name;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    if (file.blob) {
        URL.revokeObjectURL(href);
    }
}


/* Generate */
generateButton.addEventListener("click", () => {

    if (notes.length === 0) {
        log("No notes selected.");
        return;
    }

    if (questions.length === 0) {
        log("No question papers selected.");
        return;
    }

    const apiKey =
        document.getElementById("apiKey").value.trim();

    if (!apiKey) {
        log("Gemini API key is required.");
        return;
    }

    const rpm =
        document.getElementById("rpm").value;

    const model =
        document.getElementById("model").value;

    log(
        `Ready to process ${notes.length} note file(s) and ${questions.length} question file(s).`
    );

    /*
     * Backend integration point.
     *
     * Later this becomes something like:
     *
     * generateButton.disabled = true;
     *
     * const result = await runPipeline({
     *     notes,
     *     questions,
     *     apiKey,
     *     model,
     *     rpm,
     *     onLog: log
     * });
     *
     * renderOutputFiles(result.files);
     *
     * generateButton.disabled = false;
     */
});

renderFiles();