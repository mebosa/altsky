#!/usr/bin/env node

import { spawn } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const frontendDir = resolve(__dirname, "..");
const envPath = resolve(frontendDir, ".env.local");

const defaultPort = 8000;
const args = new Map(
  process.argv
    .slice(2)
    .filter((arg) => arg.startsWith("--"))
    .map((arg) => {
      const [key, value] = arg.replace(/^--/, "").split("=", 2);
      return [key, value ?? "true"];
    }),
);

const port = Number(args.get("port") ?? defaultPort);
if (!Number.isFinite(port)) {
  console.error(`[ngrok] Invalid port value: ${args.get("port")}`);
  process.exit(1);
}

const addr = args.get("addr") ?? `http://127.0.0.1:${port}`;

function updateEnvFile(url) {
  const envKey = "VITE_API_BASE";
  const line = `${envKey}=${url}`;
  let lines = [];

  if (existsSync(envPath)) {
    const content = readFileSync(envPath, "utf-8").replace(/^\uFEFF/, "");
    lines = content
      .split(/\r?\n/)
      .filter((entry) => entry.trim().length > 0);
  }

  const idx = lines.findIndex((entry) => entry.startsWith(`${envKey}=`));
  if (idx >= 0) {
    lines[idx] = line;
  } else {
    lines.push(line);
  }

  writeFileSync(envPath, `${lines.join("\n")}\n`, "utf-8");
}

const ngrokArgs = ["http", addr, "--log=stdout", "--log-format=json"];
console.log(`[ngrok] Starting tunnel for ${addr} ...`);

const ngrokProcess = spawn("ngrok", ngrokArgs, {
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
    updateEnvFile(tunnelUrl);
    console.log(`[ngrok] Tunnel ready: ${tunnelUrl}`);
    console.log(`[ngrok] Updated ${envPath} with VITE_API_BASE=${tunnelUrl}`);
    console.log(`[ngrok] Keep this process running while you develop.`);
  }

  if (payload.msg && !payload.msg.startsWith("started tunnel")) {
    console.log(`[ngrok] ${payload.msg}`);
  }
});

const terminate = () => {
  console.log("\n[ngrok] Shutting down...");
  rl.close();
  ngrokProcess.kill("SIGINT");
};

process.on("SIGINT", terminate);
process.on("SIGTERM", terminate);
process.on("exit", () => {
  if (ngrokProcess.exitCode === null) {
    ngrokProcess.kill("SIGINT");
  }
});

ngrokProcess.on("exit", (code) => {
  if (code !== null && code !== 0) {
    console.error(`[ngrok] Process exited with code ${code}`);
  }
  process.exit(code ?? 0);
});
