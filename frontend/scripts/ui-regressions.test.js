const assert = require("node:assert/strict");
const test = require("node:test");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require("typescript");

function loadUtility(name, reactNative = {}) {
  const source = fs.readFileSync(path.join(__dirname, "../src/utils", name), "utf8");
  const javascript = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
  const exports = {};
  vm.runInNewContext(javascript, { exports, require: () => reactNative, window: {
    confirm: () => false, alert: () => {},
  } });
  return exports;
}

test("manual/missing values are excluded while a genuine zero measurement is retained", () => {
  const { hasMeasuredNorms } = loadUtility("measurement.ts");
  assert.equal(hasMeasuredNorms({ source: "manual_code" }), false);
  assert.equal(hasMeasuredNorms({ a: 0, p: 0, h: 0 }), false);
  assert.equal(hasMeasuredNorms({ a: 0, p: 0, h: 0, c: 0 }), true);
});

test("game board fits a landscape viewport and follows resized window dimensions", () => {
  let dimensions = { width: 1920, height: 1080 };
  const { useGameBoardSize } = loadUtility("useGameBoardSize.ts", { useWindowDimensions: () => dimensions });
  const wide = useGameBoardSize(420);
  assert.ok(wide <= 660 && wide <= 560);
  dimensions = { width: 360, height: 800 };
  assert.ok(useGameBoardSize(420) <= 328);
  assert.notEqual(useGameBoardSize(420), wide);
});

test("web confirmation cancellation resolves false without native Alert callbacks", async () => {
  const { confirmAction } = loadUtility("dialog.ts", { Platform: { OS: "web" },
    Alert: { alert: () => assert.fail("native dialog used on web") } });
  assert.equal(await confirmAction("Title", "Message", "Delete"), false);
});
