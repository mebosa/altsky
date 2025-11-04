#!/usr/bin/env node

import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const frontendDir = resolve(__dirname, "..");

const defaultPort = 5173;

const argMap = new Map(
  process.argv
    .slice(2)
    .filter((arg) => arg.startsWith("--"))
    .map((arg) => {
      const [key, value] = arg.replace(/^--/, "").split("=", 2);
      return [key, value ?? "true"];
    }),
);

const port = Number(argMap.get("port") ?? process.env.VITE_DEV_PORT ?? defaultPort);
if (!Number.isFinite(port)) {
  console.error(`[ngrok] Invalid port value provided: ${argMap.get("port")}`);
  process.exit(1);
}

const addr = argMap.get("addr") ?? `http://127.0.0.1:${port}`;
const host = argMap.get("host") ?? "0.0.0.0";

const viteCli = resolve(frontendDir, "node_modules/vite/bin/vite.js");
const viteArgs = [viteCli, "dev", "--host", host, "--port", String(port)];

console.log(`[vite] Starting dev server on ${host}:${port} ...`);
const viteProcess = spawn(process.execPath, viteArgs, {
  cwd: frontendDir,
  stdio: ["ignore", "pipe", "inherit"],
  env: { ...process.env, VITE_DEV_PORT: String(port) },
});

viteProcess.stdout.setEncoding("utf-8");
viteProcess.stdout.on("data", (chunk) => {
  chunk
    .split(/\r?\n/)
    .filter(Boolean)
    .forEach((line) => {
      console.log(`[vite] ${line}`);
    });
});

const ngrokArgs = ["http", addr, "--log=stdout", "--log-format=json"];
console.log(`[ngrok] Opening tunnel for ${addr} ...`);
const ngrokProcess = spawn("ngrok", ngrokArgs, {
  cwd: frontendDir,
  stdio: ["ignore", "pipe", "inherit"],
  env: process.env,
});

let tunnelUrl = null;

const rl = createInterface({ input: ngrokProcess.stdout });
rl.on("line", (line) => {
  let payload;
  try {
    payload = JSON.parse(line);
  } catch {
    return;
  }

  if (!tunnelUrl && payload.msg === "started tunnel" && payload.url?.startsWith("https://")) {
    tunnelUrl = payload.url;
    console.log(`[ngrok] Tunnel ready: ${tunnelUrl}`);
    console.log(`[ngrok] Share this URL to expose the Vite dev server.`);
  }

  if (payload.msg && !payload.msg.startsWith("started tunnel")) {
    console.log(`[ngrok] ${payload.msg}`);
  }
});

let shuttingDown = false;
function shutdown() {
  if (shuttingDown) {
    return;
  }
  shuttingDown = true;
  console.log("\n[dev-ngrok] Shutting down...");
  rl.close();
  if (ngrokProcess.exitCode === null) {
    ngrokProcess.kill("SIGINT");
  }
  if (viteProcess.exitCode === null) {
    viteProcess.kill("SIGINT");
  }
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
process.on("exit", () => {
  if (ngrokProcess.exitCode === null) {
    ngrokProcess.kill("SIGINT");
  }
  if (viteProcess.exitCode === null) {
    viteProcess.kill("SIGINT");
  }
});

const onExit = (name) => (code) => {
  if (code !== null && code !== 0) {
    console.error(`[${name}] exited with code ${code}`);
  }
  shutdown();
  process.exit(code ?? 0);
};

viteProcess.on("exit", onExit("vite"));
ngrokProcess.on("exit", onExit("ngrok"));
