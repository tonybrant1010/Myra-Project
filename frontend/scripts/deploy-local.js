#!/usr/bin/env node

const { execFileSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const HOST = process.env.MYRA_DEPLOY_HOST || "<user>@<backend-ip>";
const CEL = process.env.MYRA_DEPLOY_DIR || "/srv/frontend/dist";
const GYOKER = path.join(__dirname, "..");
const DIST = path.join(GYOKER, "dist");
const TAR = path.join(GYOKER, "myra_dist.tgz");
const PUBLISHER = path.join(GYOKER, "..", "ops", "publish_frontend.py");
const releaseId = require("node:crypto").randomUUID();
const remoteArchive = `/tmp/myra-frontend-${releaseId}.tgz`;
const remotePublisher = `/tmp/myra-publish-${releaseId}.py`;
const quote = (value) => `'${value.replace(/'/g, `'"'"'`)}'`;

if (HOST.includes("<") || HOST.startsWith("-") || /\s/.test(HOST)) {
  throw new Error("Set MYRA_DEPLOY_HOST to the intended SSH destination before deploying.");
}

function fut(parancs, args) {
  console.log(`$ ${parancs} ${args.join(" ")}`);
  execFileSync(parancs, args, { stdio: "inherit" });
}

if (!fs.existsSync(path.join(DIST, "index.html"))) {
  console.error("HIBA: nincs kesz dist/ (index.html). Elotte: npm run release:web");
  process.exit(1);
}

const buildInfo = JSON.parse(fs.readFileSync(path.join(DIST, "build-info.json"), "utf8"));
require("./build-release.js").validateConfiguration({
  EXPO_PUBLIC_CONTROLLER_NAME: buildInfo.controller_name,
  EXPO_PUBLIC_BACKEND_URL: buildInfo.backend_origin,
});

fut("tar", ["-czf", TAR, "-C", DIST, "."]);
fut("scp", [TAR, `${HOST}:${remoteArchive}`]);
fut("scp", [PUBLISHER, `${HOST}:${remotePublisher}`]);
fut("ssh", [
  HOST,
  `python3 ${quote(remotePublisher)} ${quote(remoteArchive)} --target ${quote(CEL)}`,
]);
console.log("Kesz: a frontend a szerveren fut (Caddy szolgalja ki).");
