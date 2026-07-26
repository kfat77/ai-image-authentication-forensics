const apiUrl = "http://localhost:8000/analyze";
const status = document.querySelector("#status");
const results = document.querySelector("#results");

document.querySelector("#analyze").addEventListener("click", async () => {
  const file = document.querySelector("#image").files[0];
  if (!file) return (status.textContent = "请先选择一张图片。");
  status.textContent = "正在分析…";
  const body = new FormData(); body.append("image", file);
  try {
    const response = await fetch(apiUrl, { method: "POST", body });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "分析失败");
    document.querySelector("#analysis").innerHTML = Object.entries(data.analysis)
      .map(([key, value]) => `<div><span>${key.replaceAll("_", " ")}</span><strong>${value}</strong></div>`).join("");
    document.querySelector("#candidates").innerHTML = data.candidates.map(candidate => `
      <article><div class="model"><h3>${candidate.model}</h3><span>${Math.round(candidate.confidence * 100)}% 适配度</span></div>
      <p>${candidate.prompt}</p><pre>${JSON.stringify(candidate.parameters, null, 2)}</pre></article>`).join("");
    results.hidden = false; status.textContent = "分析完成。";
  } catch (error) { status.textContent = error.message; }
});
