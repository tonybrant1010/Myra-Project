#!/usr/bin/env node

const { execFileSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const HOST = process.env.MYRA_DEPLOY_HOST || "<user>@<backend-ip>";
const CEL = process.env.MYRA_DEPLOY_DIR || "/srv/myra";
const GYOKER = path.join(__dirname, "..");
const DIST = path.join(GYOKER, "dist");
const TAR = path.join(GYOKER, "myra_dist.tgz");

function fut(parancs, args) {
  console.log(`$ ${parancs} ${args.join(" ")}`);
  execFileSync(parancs, args, { stdio: "inherit" });
}

if (!fs.existsSync(path.join(DIST, "index.html"))) {
  console.error("HIBA: nincs kesz dist/ (index.html). Elotte: npm run export && npm run patch-dist");
  process.exit(1);
}

fut("tar", ["-czf", TAR, "-C", DIST, "."]);
fut("scp", [TAR, `${HOST}:/tmp/myra_dist.tgz`]);
fut("ssh", [
  HOST,
  `tar -xzf /tmp/myra_dist.tgz -C ${CEL} && rm -f /tmp/myra_dist.tgz && echo DEPLOY-OK: ${CEL}`,
]);
console.log("Kesz: a frontend a szerveren fut (Caddy szolgalja ki).");
