// Runs tests/main.test.brs against the pure helper scripts with the brs-node simulator.
const { spawnSync } = require("node:child_process");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const files = ["components/common/SeekMath.brs", "components/common/Utils.brs", "tests/main.test.brs"];
const cli = require.resolve("brs-node/bin/brs.cli.js");
const result = spawnSync(process.execPath, [cli, "--no-sg", ...files], { cwd: root, encoding: "utf8" });
const output = `${result.stdout}${result.stderr}`;
const lines = output.split("\n").filter((l) => /TESTS|FAIL/.test(l));
console.log(lines.join("\n"));
process.exit(/TESTS PASSED/.test(output) && !/FAIL/.test(output) ? 0 : 1);
