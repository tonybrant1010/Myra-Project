const { test } = require("node:test");
const assert = require("node:assert/strict");
const { validateConfiguration } = require("./build-release");

test("a public build requires the real controller name", () => {
  for (const name of ["", "   ", "[kitöltendő]", "Az adatkezelő neve"]) {
    assert.throws(() => validateConfiguration({ EXPO_PUBLIC_CONTROLLER_NAME: name }));
  }
});

test("same-origin proxy is accepted without a backend URL", () => {
  assert.deepEqual(validateConfiguration({ EXPO_PUBLIC_CONTROLLER_NAME: "Teszt szervezet" }),
    { controller: "Teszt szervezet", backend: "" });
});

test("credentials and unencrypted backend URLs cannot enter a release", () => {
  for (const url of ["http://example.com", "https://user:secret@example.com", "https://example.com?key=secret"]) {
    assert.throws(() => validateConfiguration({ EXPO_PUBLIC_CONTROLLER_NAME: "Teszt", EXPO_PUBLIC_BACKEND_URL: url }));
  }
});
