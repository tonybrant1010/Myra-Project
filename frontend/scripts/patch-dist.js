const fs = require("fs");
const path = require("path");

const distDir = path.join(__dirname, "../dist");

function copyDir(src, dst) {
  if (!fs.existsSync(src)) return false;
  fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const dstPath = path.join(dst, entry.name);
    if (entry.isDirectory()) copyDir(srcPath, dstPath);
    else fs.copyFileSync(srcPath, dstPath);
  }
  return true;
}


const ICONS_SRC = path.join(__dirname, "../web-icons");
const iconFiles = [
  "apple-touch-icon.png",
  "favicon.ico",
  "favicon-32x32.png",
  "favicon-16x16.png",
  "android-chrome-192x192.png",
  "android-chrome-512x512.png",
  "site.webmanifest",
];
for (const f of iconFiles) {
  const src = path.join(ICONS_SRC, f);
  const dst = path.join(distDir, f);
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, dst);
    console.log(`OK ${f} copied to dist/`);
  } else {
    console.warn(`WARN missing: ${src}`);
  }
}


const nodeAssetSrc = path.join(distDir, "assets/node_modules");
const vendorAssetDst = path.join(distDir, "vendor-assets");
if (copyDir(nodeAssetSrc, vendorAssetDst)) {
  const jsDir = path.join(distDir, "_expo/static/js/web");
  for (const f of fs.readdirSync(jsDir)) {
    if (!f.endsWith(".js")) continue;
    const jsPath = path.join(jsDir, f);
    const before = fs.readFileSync(jsPath, "utf8");
    const after = before.replaceAll("/assets/node_modules/", "/vendor-assets/");
    if (after !== before) fs.writeFileSync(jsPath, after, "utf8");
  }
  console.log("OK font and icon assets moved to dist/vendor-assets/");
}


const indexPath = path.join(distDir, "index.html");
let html;
let retries = 5;
while (retries > 0) {
  try {
    html = fs.readFileSync(indexPath, "utf8");
    break;
  } catch (e) {
    if (e.code === "ENOENT" && retries > 1) {
      console.log("Waiting for index.html to be written (Windows filesystem delay)...");
      const start = Date.now();
      while (Date.now() - start < 500) {}
      retries--;
    } else {
      throw e;
    }
  }
}


html = html.replace(
  /(<meta\s+name="viewport"\s+content=")[^"]*"/,
  '$1width=device-width, initial-scale=1, maximum-scale=1"'
);


html = html.replace(/<title>[^<]*<\/title>/, "<title>Myra Project</title>");

const iosTags = [
  '<meta name="mobile-web-app-capable" content="yes">',
  '<meta name="apple-mobile-web-app-capable" content="yes">',
  '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">',
  '<meta name="apple-mobile-web-app-title" content="Myra Project">',
  '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">',
  '<link rel="apple-touch-icon-precomposed" sizes="180x180" href="/apple-touch-icon.png">',
  '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">',
  '<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">',
  '<link rel="manifest" href="/site.webmanifest">',
].join("");

let indexChanged = false;

if (!html.includes("mobile-web-app-capable")) {
  html = html.replace('<link rel="icon" href="/favicon.ico" />', iosTags + '<link rel="icon" href="/favicon.ico" />');
  indexChanged = true;
}


const themeCssPath = path.join(__dirname, "theme-tokens.css");
const themeBoot =
  'try{if(localStorage.getItem("myra.theme.mode")==="night")' +
  'document.documentElement.setAttribute("data-theme","night")}catch(e){}';

if (!html.includes("--myra-bg")) {
  if (!fs.existsSync(themeCssPath)) {
    throw new Error(
      "Hianyzik a scripts/theme-tokens.css. Enelkul minden szin feloldatlan " +
      "var(--myra-*) maradna, vagyis az oldal szinek nelkul menne ki."
    );
  }
  const themeCss = fs.readFileSync(themeCssPath, "utf8");
  const themeBlock =
    "<style id=\"myra-theme-tokens\">" + themeCss + "</style>" +
    "<script>" + themeBoot + "</script>";

  if (!html.includes("</head>")) {
    throw new Error("Nem talalom a </head> zaro tagot a dist/index.html-ben.");
  }
  html = html.replace("</head>", themeBlock + "</head>");
  indexChanged = true;
}

if (indexChanged) {
  fs.writeFileSync(indexPath, html, "utf8");
  console.log("OK dist/index.html patched (ikonok + nappali/ejszakai paletta)");
} else {
  console.log("OK dist/index.html already patched");
}


const vegleges = fs.readFileSync(indexPath, "utf8");
if (!vegleges.includes("--myra-bg") || !vegleges.includes("myra.theme.mode")) {
  throw new Error("A paletta nem kerult be a dist/index.html-be - a deploy leall.");
}
console.log("OK paletta ellenorizve a dist/index.html-ben");
