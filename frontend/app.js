const apiUrl = "http://localhost:8000/v1/analyze";
const status = document.querySelector("#status");
const results = document.querySelector("#results");

document.querySelector("#analyze").addEventListener("click", async () => {
  const file = document.querySelector("#image").files[0];
  if (!file) return (status.textContent = "请先选择一张图片。");
  status.textContent = "正在分析…";
  const body = new FormData(); body.append("image", file);
  const apiKey = document.querySelector("#api-key").value;
  try {
    const headers = apiKey ? { "X-API-Key": apiKey } : {};
    const response = await fetch(apiUrl, { method: "POST", body, headers });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "分析失败");
    renderFacts(data.analysis);
    renderCandidates(data.candidates);
    results.hidden = false; status.textContent = "分析完成。";
  } catch (error) { status.textContent = error.message; }
});

function renderFacts(analysis) {
  const container = document.querySelector("#analysis");
  container.replaceChildren();
  Object.entries(analysis).forEach(([key, value]) => {
    const fact = document.createElement("div");
    const label = document.createElement("span");
    const valueElement = document.createElement("strong");
    label.textContent = key.replaceAll("_", " ");
    valueElement.textContent = String(value);
    fact.append(label, valueElement); container.append(fact);
  });
}

function renderCandidates(candidates) {
  const container = document.querySelector("#candidates");
  container.replaceChildren();
  candidates.forEach(candidate => {
    const article = document.createElement("article");
    const model = document.createElement("h3");
    const rationale = document.createElement("p");
    const prompt = document.createElement("p");
    const parameters = document.createElement("pre");
    model.textContent = candidate.model;
    rationale.textContent = candidate.selection_rationale;
    prompt.textContent = candidate.prompt;
    parameters.textContent = JSON.stringify(candidate.parameters, null, 2);
    article.append(model, rationale, prompt, parameters); container.append(article);
  });
}
