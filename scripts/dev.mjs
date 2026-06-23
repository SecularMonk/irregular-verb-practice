import { existsSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { spawn, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const scriptFile = fileURLToPath(import.meta.url);
const rootDir = path.resolve(path.dirname(scriptFile), "..");
const frontendDir = path.join(rootDir, "frontend");
const backendDir = path.join(rootDir, "backend");

function runSync(command, args, cwd, options = {}) {
  const { shell = true, quiet = false } = options;
  const result = spawnSync(command, args, {
    cwd,
    stdio: quiet ? "ignore" : "inherit",
    shell,
    env: process.env,
  });
  return result.status === 0;
}

function pickPythonCommand() {
  if (process.env.PYTHON_CMD) {
    return process.env.PYTHON_CMD;
  }
  return process.platform === "win32" ? "py" : "python3";
}

function ensureFrontendDeps() {
  const nodeModulesPath = path.join(frontendDir, "node_modules");
  if (!existsSync(nodeModulesPath)) {
    console.log("Installing frontend dependencies...");
    const ok = runSync("npm", ["install"], frontendDir);
    if (!ok) {
      throw new Error("Failed to install frontend dependencies.");
    }
  }
}

function ensureBackendDeps(pythonCmd) {
  const importCheck = runSync(
    pythonCmd,
    ["-c", "import fastapi; import sqlalchemy; import httpx"],
    backendDir,
    { shell: false, quiet: true },
  );
  if (!importCheck) {
    console.log("Installing backend dependencies...");
    const ok = runSync(pythonCmd, ["-m", "pip", "install", "-r", "requirements.txt"], backendDir);
    if (!ok) {
      throw new Error("Failed to install backend dependencies.");
    }
  }
}

function seedDatabase(pythonCmd) {
  console.log("Seeding question bank...");
  const seeded = runSync(pythonCmd, ["-m", "app.db.seed_questions"], backendDir);
  if (!seeded) {
    throw new Error("Failed to seed the question bank.");
  }
}

function runProcess(label, command, args, cwd) {
  const child = spawn(command, args, {
    cwd,
    shell: true,
    stdio: "inherit",
    env: process.env,
  });
  child.on("exit", (code) => {
    if (code !== 0) {
      console.error(`${label} exited with code ${code}`);
    }
  });
  return child;
}

function main() {
  try {
    const pythonCmd = pickPythonCommand();
    ensureFrontendDeps();
    ensureBackendDeps(pythonCmd);
    seedDatabase(pythonCmd);

    console.log("Starting backend and frontend...");
    const backend = runProcess(
      "backend",
      pythonCmd,
      ["-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
      backendDir,
    );
    const frontend = runProcess(
      "frontend",
      "npm",
      ["run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"],
      frontendDir,
    );

    const shutdown = () => {
      backend.kill("SIGTERM");
      frontend.kill("SIGTERM");
      process.exit(0);
    };

    process.on("SIGINT", shutdown);
    process.on("SIGTERM", shutdown);
  } catch (error) {
    console.error(error instanceof Error ? error.message : error);
    process.exit(1);
  }
}

main();
