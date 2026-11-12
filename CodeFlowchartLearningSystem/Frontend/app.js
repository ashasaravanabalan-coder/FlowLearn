const $ = (id) => document.getElementById(id);
const MODES = { python: "python", javascript: "javascript", java: "text/x-java", c: "text/x-csrc", cpp: "text/x-c++src" };
let token = localStorage.getItem("fl_token"), registering = false, view = "c2f";
let current = null;
const dark = matchMedia("(prefers-color-scheme: dark)").matches;
mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "base", themeVariables: {
  background: "transparent", primaryColor: "#2a2f7a", primaryTextColor: "#eef1ff", primaryBorderColor: "#7aa2ff",
  lineColor: "#9db4ff", secondaryColor: "#3b2a7a", tertiaryColor: "#14205a", edgeLabelBackground: "#0d1550",
  fontFamily: "Source Sans 3, sans-serif" } });

const editor = CodeMirror.fromTextArea($("editor"), { lineNumbers: true, mode: "python", indentUnit: 4, theme: "neat" });
const outCode = CodeMirror.fromTextArea($("outCode"), { lineNumbers: true, readOnly: true, mode: "python", theme: "neat" });

async function api(path, method = "GET", body) {
  const r = await fetch("/api/" + path, { method, headers: { "Content-Type": "application/json", Authorization: "Bearer " + token }, body: body && JSON.stringify(body) });
  if (r.status === 401 && token) { logout(); }
  const data = r.status === 204 ? {} : await r.json();
  if (!r.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

/* ---------- auth ---------- */
/* ---------- auth ---------- */
function showApp(name) {
  $("auth").hidden = true; $("app").hidden = false; $("nav").hidden = false;
  $("who").textContent = name || localStorage.getItem("fl_user");
  setView("c2f");
}
function logout() {
  token = null; localStorage.clear();
  $("auth").hidden = false; $("app").hidden = true; $("nav").hidden = true;
}
$("logout").onclick = logout;
$("authSwitch").onclick = () => {
  registering = !registering;
  $("authTitle").textContent = $("authBtn").textContent = registering ? "Create account" : "Log in";
  $("authSwitch").textContent = registering ? "I already have an account" : "Create an account";
  $("confirmWrap").hidden = !registering;
  $("p2").value = "";
  $("authErr").textContent = "";
};
$("authBtn").onclick = async () => {
  if (registering && $("p").value !== $("p2").value) {
    $("authErr").textContent = "Passwords do not match.";
    return;
  }
  try {
    const d = await api(registering ? "register" : "login", "POST", { username: $("u").value, password: $("p").value });
    token = d.token; localStorage.setItem("fl_token", token); localStorage.setItem("fl_user", d.username);
    $("authErr").textContent = ""; showApp(d.username);
  } catch (e) { $("authErr").textContent = e.message; }
};
["p", "p2"].forEach((id) => $(id).addEventListener("keydown", (e) => e.key === "Enter" && $("authBtn").click()));
/* ---------- views ---------- */
function setView(v) {
  view = v;
  document.querySelectorAll("nav [data-view]").forEach((b) => b.classList.toggle("on", b.dataset.view === v));
  $("workspace").hidden = v === "history"; $("history").hidden = v !== "history";
  if (v === "history") return loadHistory();
  const c2f = v === "c2f";
  $("inTitle").textContent = c2f ? "Your code" : "Your flowchart (Mermaid or plain steps)";
  $("run").textContent = c2f ? "Generate flowchart" : "Generate code";
  $("outTitle").textContent = c2f ? "Flowchart" : "Generated code";
  $("saveImg").hidden = !c2f; $("chart").hidden = !c2f; $("codeOut").hidden = c2f; $("badge").hidden = true; $("explain").innerHTML = "";
  setMode(c2f ? $("lang").value : null);
  editor.setValue(""); editor.setOption("placeholder", c2f ? "" : "");
  if (!c2f) editor.setValue('flowchart TD\n  A([Start]) --> B[/"Read number n"/]\n  B --> C{"n > 0?"}\n  C -->|Yes| D["Print Positive"]\n  C -->|No| E["Print Not positive"]\n  D --> F([End])\n  E --> F');
  setTimeout(() => { editor.refresh(); outCode.refresh(); }, 0);
}
document.querySelectorAll("nav [data-view]").forEach((b) => (b.onclick = () => setView(b.dataset.view)));
function setMode(lang) { editor.setOption("mode", lang ? MODES[lang] : "text/plain"); outCode.setOption("mode", MODES[$("lang").value]); }
$("lang").onchange = () => { setMode(view === "c2f" ? $("lang").value : null); outCode.setOption("mode", MODES[$("lang").value]); };

/* ---------- generation ---------- */
async function drawChart(src) {
  try {
    const { svg } = await mermaid.render("m" + Date.now(), src);
    $("chart").innerHTML = svg;
  } catch { $("chart").innerHTML = '<p class="error">The flowchart could not be drawn. Try generating again.</p>'; }
}
function showResult(r) {
  current = r;
  if (r.logic_type) {
    $("badge").hidden = false;
    $("badge").innerHTML = `<b>${r.logic_type} logic</b><small>Decision Tree confidence ${(r.confidence * 100).toFixed(0)}%</small>`;
  }
  $("explain").innerHTML = `<h3>Step by step</h3><ol>${(r.explanation || []).map((s) => `<li>${esc(s)}</li>`).join("")}</ol><p class="summary">${esc(r.summary || "")}</p>`;
  if (view === "c2f") drawChart(r.mermaid);
  else { outCode.setValue(r.code || ""); outCode.refresh(); }
}
$("run").onclick = async () => {
  const text = editor.getValue().trim();
  if (!text) { $("status").textContent = view === "c2f" ? "Enter some code first." : "Enter a flowchart first."; return; }
  $("run").disabled = true; $("status").textContent = "Working. This takes a few seconds...";
  try {
    const r = view === "c2f"
      ? await api("code-to-flowchart", "POST", { code: text, language: $("lang").value })
      : await api("flowchart-to-code", "POST", { flowchart: text, language: $("lang").value });
    $("status").textContent = "Saved to your history."; showResult(r);
  } catch (e) { $("status").textContent = e.message; }
  $("run").disabled = false;
};
$("saveImg").onclick = () => {
  const svg = $("chart").querySelector("svg"); if (!svg) return;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([svg.outerHTML], { type: "image/svg+xml" })); a.download = "flowchart.svg"; a.click();
};

/* ---------- history ---------- */
async function loadHistory() {
  const { sessions, stats } = await api("sessions");
  $("stats").innerHTML = `<div><b>${sessions.length}</b>sessions</div>` + Object.entries(stats).map(([k, v]) => `<div><b>${v}</b>${k}</div>`).join("");
  $("list").innerHTML = sessions.length ? sessions.map((s) => `
    <div class="item"><div class="t"><pre>${esc(s.source.split("\n")[0])}</pre>
    <small>${s.direction === "code_to_flow" ? "Code to flowchart" : "Flowchart to code"} · ${s.language} · ${s.logic_type || "unclassified"} · ${new Date(s.created_at + "Z").toLocaleString()}</small></div>
    <button data-open="${s.id}">Open</button><button class="ghost" data-del="${s.id}">Delete</button></div>`).join("")
    : '<p class="empty">No sessions yet. Generate a flowchart and it will appear here.</p>';
  $("list").onclick = async (e) => {
    const del = e.target.dataset.del, open = e.target.dataset.open;
    if (del) { await api("sessions/" + del, "DELETE"); loadHistory(); }
    if (open) {
      const s = sessions.find((x) => x.id == open);
      setView(s.direction === "code_to_flow" ? "c2f" : "f2c");
      $("lang").value = s.language; setMode(view === "c2f" ? s.language : null);
      editor.setValue(s.source); showResult(s);
    }
  };
}
const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

if (token) showApp();
