const messageBox = document.querySelector("#message");
const analysisResult = document.querySelector("#analysisResult");
const reportsList = document.querySelector("#reportsList");

document.querySelector("#sampleButton").addEventListener("click", () => {
  messageBox.value =
    "Congratulations! You are selected for a job. " +
    "Pay a registration fee today, send your OTP, and contact us on WhatsApp.";
});

document.querySelector("#analyzeButton").addEventListener("click", async () => {
  const response = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: messageBox.value })
  });

  const data = await response.json();
  analysisResult.hidden = false;
  analysisResult.replaceChildren();

  if (!response.ok) {
    analysisResult.textContent = data.error || "Could not analyze the message.";
    return;
  }

  const heading = document.createElement("h3");
  heading.textContent = `${data.title} — ${data.score}/100`;

  const list = document.createElement("ul");
  data.reasons.forEach(reason => {
    const item = document.createElement("li");
    item.textContent = reason;
    list.appendChild(item);
  });

  analysisResult.append(heading, list);
});

document.querySelector("#reportForm").addEventListener("submit", async event => {
  event.preventDefault();

  const message = document.querySelector("#reportMessage");
  message.textContent = "Saving report…";

  const response = await fetch("/api/reports", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      organization: document.querySelector("#organization").value,
      details: document.querySelector("#details").value
    })
  });

  const data = await response.json();
  message.textContent = data.message || data.error;

  if (response.ok) {
    event.target.reset();
    loadReports();
  }
});

async function loadReports() {
  const response = await fetch("/api/reports");
  const reports = await response.json();

  reportsList.replaceChildren();

  if (!reports.length) {
    reportsList.textContent = "No reports yet.";
    return;
  }

  reports.forEach(report => {
    const article = document.createElement("article");
    article.className = "report";

    const name = document.createElement("b");
    name.textContent = report.organization || "Unspecified sender";

    const details = document.createElement("p");
    details.textContent = report.details;

    const date = document.createElement("small");
    date.textContent = new Date(report.created_at).toLocaleString();

    article.append(name, details, date);
    reportsList.appendChild(article);
  });
}

loadReports().catch(() => {
  reportsList.textContent = "Could not load reports. Check that the Flask server is running.";
});
