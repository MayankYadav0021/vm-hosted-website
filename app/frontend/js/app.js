const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

const navItems = document.querySelectorAll(".nav-item");
const sections = document.querySelectorAll(".page-section");

function showSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (!section) return;

    document.querySelectorAll(".nav-item").forEach(item => {
        item.classList.toggle(
            "active",
            item.dataset.section === sectionId
        );
    });

    section.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

navItems.forEach(item => {
    item.addEventListener("click", () => {
        showSection(item.dataset.section);
    });
});

// Keep the sidebar highlight synchronized with the visible section.
if ("IntersectionObserver" in window) {
    const sectionObserver = new IntersectionObserver(entries => {
        const visible = entries
            .filter(entry => entry.isIntersecting)
            .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

        if (!visible) return;

        const sectionId = visible.target.id;
        const navSection = ["phase1", "phase2", "phase3"].includes(sectionId)
            ? "phase1"
            : sectionId;

        navItems.forEach(item => {
            item.classList.toggle("active", item.dataset.section === navSection);
        });
    }, {
        rootMargin: "-18% 0px -65% 0px",
        threshold: [0, 0.1, 0.25, 0.5]
    });

    sections.forEach(section => sectionObserver.observe(section));
}

function showPhase1Tab(tabName) {
    document.querySelectorAll(".phase1-content").forEach(content => content.classList.add("hidden"));
    document.querySelectorAll(".tab").forEach(tab => tab.classList.remove("active-tab"));

    const selected = document.getElementById(`phase1-${tabName}`);
    if (selected) selected.classList.remove("hidden");

    const tabs = document.querySelectorAll(".tab");
    const index = { models: 0, workloads: 1, comparison: 2 }[tabName];
    if (index !== undefined && tabs[index]) tabs[index].classList.add("active-tab");
}

async function fetchResults() {
    const indicator = document.getElementById("api-status");

    try {
        const response = await fetch(`${API_BASE}/api/results`);
        if (!response.ok) throw new Error(`API returned ${response.status}`);

        const data = await response.json();
        window.benchmarkResults = data;

        if (indicator) {
            indicator.textContent = "API Connected · Live Results";
            indicator.classList.add("api-connected");
        }

        updateDashboard(data);
    } catch (error) {
        console.error("Unable to load benchmark results:", error);
        if (indicator) indicator.textContent = "API Offline · Start the backend to load results";
    }
}

function number(value, digits = 2) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed.toFixed(digits) : "—";
}

function addMetric(container, label, value, detail = "") {
    const card = document.createElement("article");
    card.className = "live-metric-card";

    const heading = document.createElement("div");
    heading.className = "live-metric-label";
    heading.textContent = label;

    const numberElement = document.createElement("div");
    numberElement.className = "live-metric-value";
    numberElement.textContent = value;

    const footnote = document.createElement("div");
    footnote.className = "live-metric-detail";
    footnote.textContent = detail;

    card.append(heading, numberElement, footnote);
    container.appendChild(card);
}

function makeTable(container, columns, rows) {
    const table = document.createElement("table");
    table.className = "live-results-table";

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    columns.forEach(column => {
        const th = document.createElement("th");
        th.textContent = column.label;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    rows.forEach(row => {
        const tr = document.createElement("tr");

        columns.forEach(column => {
            const td = document.createElement("td");
            const value = row[column.key];
            td.textContent = value === undefined || value === null || value === "" ? "—" : String(value);
            tr.appendChild(td);
        });

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.replaceChildren(table);
}

function updateDashboard(data) {
    const phase1 = data.phase1_model_comparison || data.phase1 || [];
    const latestPhase1 = data.phase1 || [];
    const precision = data.phase2_precision || [];
    const batching = data.phase2_batching || [];
    const lora = data.phase3_lora || [];
// Update quantitative results dynamically

const throughputRows = [
    ...phase1,
    ...precision,
    ...batching
].filter(row =>
    row.status === "success" &&
    Number.isFinite(Number(row.avg_tokens_per_sec))
);

const bestThroughput = throughputRows.length
    ? throughputRows.reduce((best, row) =>
        Number(row.avg_tokens_per_sec) >
        Number(best.avg_tokens_per_sec) ? row : best
    )
    : null;

const modelsWithSize = latestPhase1.filter(row =>
    Number.isFinite(Number(row.parameters_millions)) &&
    Number(row.parameters_millions) > 0
);

const largestModel = modelsWithSize.length
    ? modelsWithSize.reduce((largest, row) =>
        Number(row.parameters_millions) >
        Number(largest.parameters_millions) ? row : largest
    )
    : null;

// Compare Phase 1 model peak RAM only.
// Phase 2 and Phase 3 use different process-memory measurements.
const ramRows = latestPhase1
    .filter(row =>
        row.status === "success" &&
        Number.isFinite(Number(row.peak_ram_gb))
    )
    .map(row => ({
        ram: Number(row.peak_ram_gb),
        model: row.model
    }));

const highestRam = ramRows.length
    ? ramRows.reduce((highest, row) =>
        row.ram > highest.ram ? row : highest
    )
    : null;

const setResult = (id, value) => {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
};

setResult(
    "result-best-throughput",
    bestThroughput ? Number(bestThroughput.avg_tokens_per_sec).toFixed(2) : "—"
);

setResult(
    "result-best-model",
    bestThroughput ? bestThroughput.model : "No results"
);

setResult(
    "result-largest-model",
    largestModel
        ? `${Number(largestModel.parameters_millions).toFixed(2)}M`
        : "—"
);

setResult(
    "result-largest-name",
    largestModel ? largestModel.model : "No results"
);

setResult(
    "result-highest-ram",
    highestRam ? `${Number(highestRam.ram).toFixed(2)} GB` : "—"
);

setResult(
    "result-ram-model",
    highestRam ? highestRam.model : "No results"
);

    const successfulModels = phase1.filter(row => row.status === "success").length;
    const totalRequests = phase1.reduce((sum, row) => sum + Number(row.total_requests || 0), 0);
    const successfulRequests = phase1.reduce((sum, row) => sum + Number(row.successful_requests || 0), 0);

    const metricContainer = document.getElementById("live-overview-metrics");
    if (metricContainer) {
        metricContainer.replaceChildren();
        addMetric(metricContainer, "Benchmarked Models", String(successfulModels), "Successful model benchmarks");
        addMetric(metricContainer, "Benchmark Requests", `${successfulRequests}/${totalRequests}`, "Successful recorded requests");
        addMetric(metricContainer, "Precision Tests", String(precision.length), "FP32 and FP16 runs");
        addMetric(metricContainer, "Batching Tests", String(batching.length), "Batch sizes tested");
        addMetric(metricContainer, "LoRA Runs", String(lora.length), lora.length ? "Recorded LoRA experiments" : "No runs recorded");
    }

    const p1Table = document.getElementById("live-phase1-table");
    if (p1Table) makeTable(p1Table, [
        { key: "model", label: "Model" },
        { key: "parameters_millions", label: "Parameters (M)" },
        { key: "load_time_sec", label: "Load (s)" },
        { key: "avg_inference_time_sec", label: "Avg Inference (s)" },
        { key: "avg_tokens_per_sec", label: "Tokens/s" },
        { key: "peak_ram_gb", label: "Peak RAM (GB)" },
        { key: "successful_requests", label: "Successful" }
    ], latestPhase1.map(row => ({
        ...row,
        parameters_millions: number(row.parameters_millions, 1),
        load_time_sec: number(row.load_time_sec, 2),
        avg_inference_time_sec: number(row.avg_inference_time_sec, 3),
        avg_tokens_per_sec: number(row.avg_tokens_per_sec, 2),
        peak_ram_gb: number(row.peak_ram_gb, 2),
        successful_requests: `${row.successful_requests || 0}/${row.total_requests || 0}`
    })));

    const precisionTable = document.getElementById("live-precision-table");
    if (precisionTable) makeTable(precisionTable, [
        { key: "precision", label: "Precision" },
        { key: "status", label: "Status" },
        { key: "avg_inference_time_sec", label: "Avg Inference (s)" },
        { key: "avg_tokens_per_sec", label: "Tokens/s" },
        { key: "peak_process_ram_gb", label: "Peak RAM (GB)" },
        { key: "successful_requests", label: "Successful" }
    ], precision.map(row => ({
        ...row,
        avg_inference_time_sec: number(row.avg_inference_time_sec, 3),
        avg_tokens_per_sec: number(row.avg_tokens_per_sec, 2),
        peak_process_ram_gb: number(row.peak_process_ram_gb, 2),
        successful_requests: `${row.successful_requests || 0}/${row.total_requests || 0}`
    })));

    const batchingTable = document.getElementById("live-batching-table");
    if (batchingTable) makeTable(batchingTable, [
        { key: "batch_size", label: "Batch Size" },
        { key: "status", label: "Status" },
        { key: "avg_batch_latency_sec", label: "Batch Latency (s)" },
        { key: "total_inference_time_sec", label: "Total Time (s)" },
        { key: "avg_tokens_per_sec", label: "Tokens/s" },
        { key: "peak_process_ram_gb", label: "Peak RAM (GB)" },
        { key: "successful_requests", label: "Successful" }
    ], batching.map(row => ({
        ...row,
        avg_batch_latency_sec: number(row.avg_batch_latency_sec, 3),
        total_inference_time_sec: number(row.total_inference_time_sec, 3),
        avg_tokens_per_sec: number(row.avg_tokens_per_sec, 2),
        peak_process_ram_gb: number(row.peak_process_ram_gb, 2),
        successful_requests: `${row.successful_requests || 0}/${row.total_requests || 0}`
    })));

    const loraTable = document.getElementById("live-lora-table");
    if (loraTable) {
        loraTable.replaceChildren();

        if (lora.length) {
            const row = lora[0];

            const heading = document.createElement("h3");
            heading.className = "lora-results-heading";
            heading.textContent = "Recorded training run";
            loraTable.appendChild(heading);

            const note = document.createElement("p");
            note.className = "lora-results-note";
            note.textContent =
                "One CPU-based LoRA run. Training completed; output-quality comparison remains pending.";
            loraTable.appendChild(note);

            const metrics = [
                ["Base model", row.model || "distilbert/distilgpt2"],
                ["Device", row.device || "CPU"],
                ["Training examples", row.training_examples],
                ["Epochs", row.epochs],
                ["Trainable parameters", Number(row.trainable_parameters || 0).toLocaleString()],
                ["Trainable parameter share", `${number(row.trainable_parameter_percent, 4)}% of total`],
                ["Training time", `${number(row.training_time_sec, 3)} s`],
                ["Evaluation time", `${number(row.evaluation_time_sec, 3)} s`],
                ["Average generation time", `${number(row.avg_generation_time_sec, 4)} s`],
                ["Reported process RAM", `${number(row.peak_process_ram_gb, 4)} GB`],
                ["Run status", row.status || "Recorded"]
            ];

            const grid = document.createElement("div");
            grid.className = "lora-results-grid";

            for (const [label, value] of metrics) {
                const card = document.createElement("div");
                card.className = "lora-result-item";

                const labelEl = document.createElement("span");
                labelEl.className = "lora-result-label";
                labelEl.textContent = label;

                const valueEl = document.createElement("strong");
                valueEl.className = "lora-result-value";
                valueEl.textContent = value === undefined || value === null ? "—" : String(value);

                card.append(labelEl, valueEl);
                grid.appendChild(card);
            }

            loraTable.appendChild(grid);

            if (Array.isArray(row.evaluation_outputs) && row.evaluation_outputs.length) {
                const outputHeading = document.createElement("h3");
                outputHeading.className = "lora-results-heading";
                outputHeading.textContent = "Sample generated responses";
                loraTable.appendChild(outputHeading);

                const outputList = document.createElement("div");
                outputList.className = "lora-output-list";

                for (const item of row.evaluation_outputs) {
                    const block = document.createElement("article");
                    block.className = "lora-output-item";

                    const prompt = document.createElement("h4");
                    prompt.textContent = item.prompt || "Evaluation prompt";

                    const generated = document.createElement("p");
                    generated.textContent = item.generated_text || "No generated text recorded.";

                    const timing = document.createElement("small");
                    timing.textContent =
                        `Generation time: ${number(item.generation_time_sec, 4)} s`;

                    block.append(prompt, generated, timing);
                    outputList.appendChild(block);
                }

                loraTable.appendChild(outputList);
            }

            const caveat = document.createElement("p");
            caveat.className = "lora-results-note";
            caveat.textContent =
                "Interpretation: this run confirms that the LoRA training pipeline executed. " +
                "A baseline-versus-adapter comparison and a formal text-quality metric have not yet been recorded.";
            loraTable.appendChild(caveat);
        } else {
            loraTable.textContent = "No LoRA benchmark results have been recorded yet.";
        }
    }

    const timestamp = document.getElementById("last-updated");
    if (timestamp) timestamp.textContent = `Last refreshed: ${new Date().toLocaleString()}`;

    drawBarChart("live-phase1-chart", phase1, "model", "avg_tokens_per_sec", "Tokens per second");
    drawBarChart("live-precision-chart", precision, "precision", "avg_tokens_per_sec", "Tokens per second");
    drawBarChart("live-batching-chart", batching, "batch_size", "avg_tokens_per_sec", "Tokens per second");
}

function drawBarChart(canvasId, rows, labelKey, valueKey, title) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const cssWidth = Math.max(canvas.clientWidth || 600, 320);
    const height = 260;
    const dpr = window.devicePixelRatio || 1;

    canvas.width = Math.round(cssWidth * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const width = cssWidth;
    ctx.clearRect(0, 0, width, height);

    const left = 44;
    const right = 18;
    const top = 38;
    const bottom = 64;
    const chartWidth = width - left - right;
    const chartHeight = height - top - bottom;

    ctx.font = "12px sans-serif";
    ctx.fillStyle = "#252a2e";
    ctx.textAlign = "left";
    ctx.fillText(title, 12, 20);

    const validRows = rows.filter(row =>
        row[valueKey] !== null &&
        row[valueKey] !== undefined &&
        Number.isFinite(Number(row[valueKey]))
    );

    if (!validRows.length) {
        ctx.fillStyle = "#69727a";
        ctx.fillText("No benchmark data available", 12, 52);
        return;
    }

    const maxValue = Math.max(...validRows.map(row => Number(row[valueKey])), 1);
    const gridMax = maxValue * 1.15;

    // Draw a readable vertical scale and horizontal grid lines.
    ctx.strokeStyle = "#d9dedf";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#69727a";
    ctx.font = "11px sans-serif";
    ctx.textAlign = "right";

    for (let i = 0; i <= 4; i++) {
        const y = top + chartHeight - (chartHeight * i / 4);
        const scaleValue = gridMax * i / 4;

        ctx.beginPath();
        ctx.moveTo(left, y);
        ctx.lineTo(width - right, y);
        ctx.stroke();

        ctx.fillText(scaleValue.toFixed(1), left - 8, y + 4);
    }

    const slot = chartWidth / validRows.length;
    const barWidth = Math.min(70, slot * 0.55);

    validRows.forEach((row, index) => {
        const value = Number(row[valueKey]);
        const barHeight = Math.max(2, (value / gridMax) * chartHeight);
        const x = left + slot * index + (slot - barWidth) / 2;
        const y = top + chartHeight - barHeight;

        ctx.fillStyle = "#54745f";
        ctx.fillRect(x, y, barWidth, barHeight);

        ctx.fillStyle = "#252a2e";
        ctx.font = "12px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(value.toFixed(1), x + barWidth / 2, Math.max(top - 3, y - 7));

        let label = String(row[labelKey] ?? "");
        if (label.length > 16) label = label.slice(0, 14) + "…";

        ctx.fillStyle = "#69727a";
        ctx.font = "11px sans-serif";
        ctx.fillText(label, x + barWidth / 2, top + chartHeight + 19);
    });

    ctx.textAlign = "left";
}

window.addEventListener("resize", () => {
    if (window.benchmarkResults) {
        const data = window.benchmarkResults;
        drawBarChart("live-phase1-chart", data.phase1_model_comparison || data.phase1 || [], "model", "avg_tokens_per_sec", "Tokens per second");
        drawBarChart("live-precision-chart", data.phase2_precision || [], "precision", "avg_tokens_per_sec", "Tokens per second");
        drawBarChart("live-batching-chart", data.phase2_batching || [], "batch_size", "avg_tokens_per_sec", "Tokens per second");
    }
});


function formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    return `${days}d ${hours}h ${minutes}m`;
}

function updateSystemMetric(id, barId, value) {
    const element = document.getElementById(id);
    const bar = document.getElementById(barId);

    if (element) element.textContent = `${number(value, 1)}%`;
    if (bar) bar.style.width = `${Math.min(100, Math.max(0, Number(value)))}%`;
}

async function fetchSystemMetrics() {
    const status = document.getElementById("system-api-status");

    try {
        const response = await fetch(`${API_BASE}/api/system`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();

        updateSystemMetric("system-cpu", "system-cpu-bar", data.cpu_percent);
        updateSystemMetric("system-memory", "system-memory-bar", data.memory_percent);
        updateSystemMetric("system-disk", "system-disk-bar", data.disk_percent);

        const memoryDetail = document.getElementById("system-memory-detail");
        if (memoryDetail) {
            memoryDetail.textContent =
                `${data.memory_used_gb} GB used of ${data.memory_total_gb} GB · ${data.memory_available_gb} GB available`;
        }

        const diskDetail = document.getElementById("system-disk-detail");
        if (diskDetail) {
            diskDetail.textContent =
                `${data.disk_free_gb} GB free of ${data.disk_total_gb} GB`;
        }

        const cpuDetail = document.getElementById("system-cpu-detail");
        if (cpuDetail) cpuDetail.textContent = `${data.cpu_count} vCPU`;

        const uptime = document.getElementById("system-uptime");
        if (uptime) uptime.textContent = formatUptime(data.uptime_seconds);

        const hostname = document.getElementById("system-hostname");
        if (hostname) hostname.textContent = `Instance: ${data.hostname}`;

        const cores = document.getElementById("system-core-count");
        if (cores) cores.textContent = `${data.cpu_count} vCPU`;

        const updated = document.getElementById("system-updated");
        if (updated) updated.textContent =
            `Updated ${new Date(data.timestamp).toLocaleTimeString()}`;

        if (status) {
            status.textContent = "EC2 Connected";
            status.classList.add("api-connected");
        }
    } catch (error) {
        console.error("System monitoring failed:", error);
        if (status) {
            status.textContent = "Monitoring Offline";
            status.classList.remove("api-connected");
        }
    }
}

// Initialize the dashboard after the HTML has loaded.
document.addEventListener("DOMContentLoaded", () => {
    fetchResults();
    fetchSystemMetrics();
    setInterval(fetchSystemMetrics, 5000);
});
// ======================================
// AWS EXPERIMENT CONTROL CENTER
// ======================================

let activeExperimentId = null;
let experimentPolling = null;

const experimentNames = {
    phase1: "Model Performance Benchmarking",
    phase2_precision: "Precision Optimization",
    phase2_batching: "Batch Optimization",
    phase3_lora: "LoRA Fine-Tuning"
};

async function launchExperiment() {
    const message = document.getElementById("experiment-message");
    if (message) {
        message.textContent =
            "For security, experiments must be launched from the AWS Ubuntu host. " +
            "The public website is read-only for experiment execution.";
    }
}

function updateCurrentExperiment(job) {
    const container = document.getElementById(
        "experiment-current-status"
    );

    if (!container) return;

    container.replaceChildren();

    const details = [
        ["Experiment", experimentNames[job.experiment] || job.experiment],
        ["Model", job.model],
        ["Status", job.status],
        ["Experiment ID", job.id],
        ["Message", job.message]
    ];

    details.forEach(([label, value]) => {
        const row = document.createElement("p");
        const strong = document.createElement("strong");

        strong.textContent = `${label}: `;
        row.append(strong, document.createTextNode(value || "—"));

        container.appendChild(row);
    });
}

async function pollActiveExperiment() {
    if (!activeExperimentId) return;

    try {
        const response = await fetch(
            `${API_BASE}/api/experiments/${activeExperimentId}`
        );

        if (!response.ok) throw new Error("Unable to retrieve status.");

        const job = await response.json();

        updateCurrentExperiment(job);

        if (["completed", "failed"].includes(job.status)) {
            clearInterval(experimentPolling);
            experimentPolling = null;

            document.getElementById(
                "run-experiment-btn"
            ).disabled = false;

            document.getElementById(
                "experiment-message"
            ).textContent = job.message;

            await fetchResults();
            await fetchExperimentHistory();
        }

    } catch (error) {
        console.error("Experiment status error:", error);
    }
}


function addDetailSection(container, title) {
    const section = document.createElement("section");
    section.className = "experiment-detail-section";

    const heading = document.createElement("h4");
    heading.textContent = title;
    section.appendChild(heading);

    container.appendChild(section);
    return section;
}

function renderExperimentTable(section, rows) {
    if (!Array.isArray(rows) || rows.length === 0) {
        section.append("No rows available.");
        return;
    }

    const columns = [...new Set(rows.flatMap(row =>
        row && typeof row === "object" ? Object.keys(row) : []
    ))];

    if (!columns.length) {
        const pre = document.createElement("pre");
        pre.textContent = JSON.stringify(rows, null, 2);
        section.appendChild(pre);
        return;
    }

    const table = document.createElement("table");
    table.className = "live-results-table";

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    columns.forEach(column => {
        const th = document.createElement("th");
        th.textContent = column;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");

    rows.forEach(item => {
        const row = document.createElement("tr");

        columns.forEach(column => {
            const cell = document.createElement("td");
            const value = item?.[column];

            cell.textContent =
                value === null || value === undefined
                    ? "—"
                    : typeof value === "object"
                        ? JSON.stringify(value)
                        : String(value);

            row.appendChild(cell);
        });

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    section.appendChild(table);
}

async function openExperimentDetails(experimentId) {
    const panel = document.getElementById("experiment-details");
    const content = document.getElementById("experiment-details-content");

    panel.hidden = false;
    content.replaceChildren();

    const loading = document.createElement("p");
    loading.textContent = "Loading experiment results...";
    content.appendChild(loading);

    panel.scrollIntoView({ behavior: "smooth", block: "start" });

    try {
        const encodedId = encodeURIComponent(experimentId);

        const [statusResponse, resultsResponse] = await Promise.all([
            fetch(`${API_BASE}/api/experiments/${encodedId}`),
            fetch(`${API_BASE}/api/experiments/${encodedId}/results`)
        ]);

        if (!statusResponse.ok || !resultsResponse.ok) {
            throw new Error("Could not load experiment details.");
        }

        const job = await statusResponse.json();
        const responseData = await resultsResponse.json();

        content.replaceChildren();

        const grid = document.createElement("div");
        grid.className = "experiment-details-grid";

        const details = [
            ["Experiment", job.experiment || job.phase],
            ["Model", job.model],
            ["Status", job.status],
            ["Created", job.created_at
                ? new Date(job.created_at).toLocaleString()
                : "—"],
            ["Started", job.started_at
                ? new Date(job.started_at).toLocaleString()
                : "—"],
            ["Finished", job.finished_at
                ? new Date(job.finished_at).toLocaleString()
                : "—"]
        ];

        details.forEach(([label, value]) => {
            const card = document.createElement("div");
            card.className = "experiment-detail-card";

            const small = document.createElement("small");
            small.textContent = label;

            const strong = document.createElement("strong");
            strong.textContent = value || "—";

            card.append(small, strong);
            grid.appendChild(card);
        });

        content.appendChild(grid);

        const results = responseData.results || {};

        Object.entries(results).forEach(([file, data]) => {
            if (file === "log") return;

            const section = addDetailSection(
                content,
                file.split("/").pop()
            );

            if (file.toLowerCase().endsWith(".csv")) {
                renderExperimentTable(section, data);
            } else {
                const pre = document.createElement("pre");
                pre.textContent = JSON.stringify(data, null, 2);
                section.appendChild(pre);
            }
        });

        const imageFiles = (job.result_files || [])
            .filter(file => /\.(png|jpe?g|webp)$/i.test(file));

        if (imageFiles.length) {
            const section = addDetailSection(content, "Benchmark Graphs");

            imageFiles.forEach(file => {
                const image = document.createElement("img");
                const encodedPath = file.split("/")
                    .map(encodeURIComponent)
                    .join("/");

                image.src = `${API_BASE}/api/experiments/${encodedId}/files/${encodedPath}`;
                image.alt = file.split("/").pop();
                image.loading = "lazy";
                image.className = "experiment-detail-image";

                section.appendChild(image);
            });
        }

        if (results.log) {
            const section = addDetailSection(content, "Experiment Log");
            const pre = document.createElement("pre");
            pre.textContent = results.log;
            section.appendChild(pre);
        }

        if (!Object.keys(results).length && !imageFiles.length) {
            const empty = document.createElement("p");
            empty.textContent = "No result files are available yet.";
            content.appendChild(empty);
        }

    } catch (error) {
        content.replaceChildren();
        const message = document.createElement("p");
        message.textContent = error.message;
        content.appendChild(message);
    }
}

async function fetchExperimentHistory() {
    const container = document.getElementById("experiment-history");

    try {
        const response = await fetch(`${API_BASE}/api/experiments`);

        if (!response.ok) throw new Error("History unavailable.");

        const data = await response.json();
        container.replaceChildren();

        const jobs = data.experiments || [];

        if (!jobs.length) {
            container.textContent = "No experiments have been executed yet.";
            return;
        }

        const table = document.createElement("table");
        table.className = "live-results-table";

        const headers = ["Experiment", "Model", "Status", "Created"];
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");

        headers.forEach(header => {
            const th = document.createElement("th");
            th.textContent = header;
            headerRow.appendChild(th);
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");

        jobs.forEach(job => {
            const row = document.createElement("tr");
            row.className = "experiment-history-row";
            row.tabIndex = 0;
            row.setAttribute("role", "button");
            row.setAttribute("aria-label", `View ${job.experiment || job.phase}`);

            [
                experimentNames[job.experiment] || job.experiment || job.phase,
                job.model,
                job.status,
                job.created_at
                    ? new Date(job.created_at).toLocaleString()
                    : "—"
            ].forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value || "—";
                row.appendChild(cell);
            });

            row.addEventListener("click", () =>
                openExperimentDetails(job.id)
            );

            row.addEventListener("keydown", event => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    openExperimentDetails(job.id);
                }
            });

            tbody.appendChild(row);
        });

        table.appendChild(tbody);
        container.appendChild(table);

    } catch (error) {
        container.textContent = error.message;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const closeDetails = document.getElementById("close-experiment-details");

    if (closeDetails) {
        closeDetails.addEventListener("click", () => {
            document.getElementById("experiment-details").hidden = true;
        });
    }

    const button = document.getElementById("run-experiment-btn");

    if (button) {
        button.addEventListener("click", launchExperiment);
    }

    const refresh = document.getElementById("refresh-experiments");

    if (refresh) {
        refresh.addEventListener("click", fetchExperimentHistory);
    }

    const phaseSelect = document.getElementById("experiment-phase");
    const modelSelect = document.getElementById("experiment-model");

    if (phaseSelect && modelSelect) {
        const updateModelSelection = () => {
            const isBenchmark = phaseSelect.value === "phase1";
            const note = document.getElementById("model-selection-note");

            modelSelect.disabled = !isBenchmark;

            if (!isBenchmark) {
                modelSelect.value = "distilbert/distilgpt2";
                if (note) note.textContent =
                    "This experiment currently supports DistilGPT-2 only.";
            } else {
                if (note) note.textContent =
                    "Choose a model for benchmarking.";
            }
        };

        phaseSelect.addEventListener("change", updateModelSelection);
        updateModelSelection();
    }

    fetchExperimentHistory();
});


// AI Model Advisor frontend
document.addEventListener("DOMContentLoaded", () => {
    const queryInput = document.getElementById("advisor-query");
    const submitButton = document.getElementById("advisor-submit");
    const responsePanel = document.getElementById("advisor-response");
    const responseContent = document.getElementById("advisor-response-content");
    const benchmarkStatus = document.getElementById("advisor-benchmark-status");

    if (!queryInput || !submitButton || !responsePanel || !responseContent) {
        return;
    }

    document.querySelectorAll(".advisor-prompt").forEach(button => {
        button.addEventListener("click", () => {
            queryInput.value = button.dataset.prompt || "";
            queryInput.focus();
        });
    });

    async function loadBenchmarks() {
        const countElement = document.getElementById("benchmark-model-count");
        const latencyElement = document.getElementById("benchmark-average-latency");
        const ramElement = document.getElementById("benchmark-peak-ram");
        const statusElement = document.getElementById("benchmark-coverage-status");

        if (!countElement || !latencyElement || !ramElement || !statusElement) return;

        try {
            const response = await fetch("/api/advisor/benchmarks");
            if (!response.ok) throw new Error("Unable to load benchmark data.");

            const data = await response.json();
            const models = data.models || [];

            countElement.textContent = models.length;

            if (models.length === 0) {
                latencyElement.textContent = "—";
                ramElement.textContent = "—";
                statusElement.textContent = "Awaiting experiments";
                benchmarkStatus.textContent =
                    "No successful benchmark experiments are recorded yet. Run an experiment to populate these metrics.";
                return;
            }

            const averageLatency =
                models.reduce((sum, model) => sum + model.latency, 0) / models.length;

            const highestRam = Math.max(...models.map(model => model.memory));

            latencyElement.textContent = averageLatency.toFixed(3) + " s";
            ramElement.textContent = highestRam.toFixed(2) + " GB";
            statusElement.textContent = "Live benchmark data";

            benchmarkStatus.textContent =
                `${models.length} successfully benchmarked models: ` +
                models.map(model => model.name).join(", ");

        } catch (error) {
            statusElement.textContent = "Data unavailable";
            benchmarkStatus.textContent = error.message;
        }
    }

    function addText(parent, tag, value) {
        const element = document.createElement(tag);
        element.textContent = value;
        parent.appendChild(element);
        return element;
    }

    async function getRecommendations() {
        const query = queryInput.value.trim();

        if (query.length < 5) {
            responsePanel.hidden = false;
            responseContent.textContent = "Please describe your application in more detail.";
            return;
        }

        submitButton.disabled = true;
        submitButton.textContent = "Analysing benchmarks...";
        responsePanel.hidden = false;
        responseContent.textContent = "Understanding your requirements and evaluating suitable models...";

        try {
            const response = await fetch("/api/advisor/recommend", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Recommendation request failed.");
            }


            responseContent.replaceChildren();

            const models = data.recommendations || [];

            if (data.summary) {
                const summary = document.createElement("p");
                summary.className = "advisor-summary";
                summary.textContent = data.summary;
                responseContent.appendChild(summary);
            }

            const best = models[0];

            if (best) {
                const card = document.createElement("div");
                card.className = "advisor-model-card advisor-recommended-card";

                addText(card, "h4", "Recommended model");
                addText(card, "h2", best.name);
                addText(card, "p", best.type + " · " + best.size);

                const status = addText(card, "small", best.benchmark_status);
                status.className = "advisor-benchmark-label";

                addText(card, "h4", "Why this model");

                const reasons = document.createElement("ul");
                (best.reasons || []).forEach(reason => addText(reasons, "li", reason));
                card.appendChild(reasons);

                if (best.benchmark_status === "Benchmark complete") {
                    addText(card, "h4", "Measured performance");

                    const metrics = document.createElement("div");
                    metrics.className = "advisor-metrics";

                    [
                        ["Average latency", best.latency],
                        ["Throughput", best.throughput],
                        ["Peak RAM", best.memory]
                    ].forEach(([label, value], index) => {
                        if (value === null || value === undefined || !Number.isFinite(Number(value))) return;

                        const units = [" seconds", " tokens/sec", " GB"];
                        const metric = document.createElement("div");
                        metric.className = "advisor-metric";
                        addText(metric, "small", label);
                        addText(metric, "strong", Number(value).toFixed(2) + units[index]);
                        metrics.appendChild(metric);
                    });

                    if (best.requests !== null && best.requests !== undefined) {
                        const metric = document.createElement("div");
                        metric.className = "advisor-metric";
                        addText(metric, "small", "Successful requests");
                        addText(metric, "strong", `${best.requests}/${best.total_requests}`);
                        metrics.appendChild(metric);
                    }

                    card.appendChild(metrics);
                } else {
                    addText(card, "p", "This model is recommended for its capabilities. It has not yet been benchmarked on this EC2 instance.");
                }

                responseContent.appendChild(card);

                if (models.length > 1) {
                    const alternatives = document.createElement("div");
                    alternatives.className = "advisor-model-card";
                    addText(alternatives, "h4", "Alternatives considered");

                    models.slice(1, 3).forEach(other => {
                        const section = document.createElement("div");
                        addText(section, "strong", other.name);

                        const reason = (other.reasons || []).slice(0, 2).join("; ");
                        addText(section, "p", reason || "A possible alternative for this application.");

                        const benchmarkText = other.benchmark_status || "Not benchmarked";
                        addText(section, "small", benchmarkText);

                        alternatives.appendChild(section);
                    });

                    responseContent.appendChild(alternatives);
                }
            } else {
                addText(responseContent, "p", "No suitable models were returned. Please try describing your application in more detail.");
            }

            if (data.limitations && data.limitations.length) {
                const note = document.createElement("p");
                note.className = "advisor-note";
                note.textContent = data.limitations[0];
                responseContent.appendChild(note);
            }

        responsePanel.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

        } catch (error) {
            responseContent.textContent = error.message;
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = "Find Best Models";
        }
    }

    submitButton.addEventListener("click", getRecommendations);

    queryInput.addEventListener("keydown", event => {
        if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
            getRecommendations();
        }
    });

    loadBenchmarks();
});
