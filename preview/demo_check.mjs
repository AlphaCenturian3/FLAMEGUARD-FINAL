// Drive the judge demo in headless Chrome over the DevTools Protocol (Node 22+, no packages).
//   node preview/demo_check.mjs <chrome-path> <preview-url>
// Prints a JSON array: one entry per demo step {title, hash, fixtureBanner, text}.
import { spawn } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [chrome, url] = process.argv.slice(2);
const profile = mkdtempSync(join(tmpdir(), "fg-demo-"));
const proc = spawn(chrome, ["--headless=new", "--disable-gpu", "--no-first-run", `--user-data-dir=${profile}`, "--remote-debugging-port=0", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function devtoolsPort() {
  const file = join(profile, "DevToolsActivePort");
  for (let i = 0; i < 100; i++) {
    if (existsSync(file)) return readFileSync(file, "utf8").split("\n")[0].trim();
    await sleep(100);
  }
  throw new Error("Chrome did not start");
}

try {
  const port = await devtoolsPort();
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const page = targets.find((t) => t.type === "page");
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener("open", r, { once: true }));
  let id = 0;
  const pending = new Map();
  ws.addEventListener("message", (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  });
  const send = (method, params = {}) => new Promise((r) => { const n = ++id; pending.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });
  const evaluate = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result?.result?.value;

  await send("Page.navigate", { url });
  await sleep(2500);
  await evaluate(`document.querySelector(".nav-demo").click()`);
  const steps = [];
  for (let i = 0; i < 5; i++) {
    await sleep(2000);
    steps.push(await evaluate(`({
      title: (document.querySelector(".demo-say strong")?.textContent || "").replace(/\\.\\s*$/, ""),
      hash: location.hash,
      fixtureBanner: document.body.innerText.includes("NOT NASA DATA"),
      shows501: (document.getElementById("main")?.innerText || "").includes("HTTP 501"),
      text: (document.getElementById("main")?.innerText || "").slice(0, 600),
    })`));
    if (i < 4) await evaluate(`document.querySelector('[data-action="next"]').click()`);
  }
  console.log(JSON.stringify(steps));
  ws.close();
} finally {
  proc.kill();
  await sleep(300);
  rmSync(profile, { recursive: true, force: true });
}
