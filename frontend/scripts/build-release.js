const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

function validateConfiguration(environment) {
  const controller = (environment.EXPO_PUBLIC_CONTROLLER_NAME || "").trim();
  if (!controller || controller.startsWith("[") || /kitöltendő|adatkezelő neve/i.test(controller)) {
    throw new Error("Set EXPO_PUBLIC_CONTROLLER_NAME to the real public controller name before building a release.");
  }
  const backend = (environment.EXPO_PUBLIC_BACKEND_URL || "").trim();
  if (backend) {
    const url = new URL(backend);
    if (url.protocol !== "https:" || url.username || url.password || url.search || url.hash) {
      throw new Error("A release backend URL must use HTTPS without credentials, query or fragment. Leave it empty for the same-origin Caddy proxy.");
    }
  }
  return { controller, backend };
}

function main() {
  const root = path.resolve(__dirname, "..");
  process.env.NODE_ENV = "production";
  require("@expo/env").load(root);
  const config = validateConfiguration(process.env);
  const expoPackage = require.resolve("expo/package.json");
  const expoCli = path.resolve(path.dirname(expoPackage), require(expoPackage).bin.expo);
  execFileSync(process.execPath, [expoCli, "export", "--platform", "web", "--clear"], { cwd: root, stdio: "inherit" });
  execFileSync(process.execPath, [path.join(__dirname, "patch-dist.js")], { cwd: root, stdio: "inherit" });
  fs.writeFileSync(path.join(root, "dist/build-info.json"), JSON.stringify({
    built_at: new Date().toISOString(), controller_name: config.controller, backend_origin: config.backend,
  }, null, 2) + "\n");
  console.log("Release build and theme patch completed.");
}

module.exports = { validateConfiguration };
if (require.main === module) main();
