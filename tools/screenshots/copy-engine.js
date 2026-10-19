// Copy the simulator bundles next to index.html (www/lib, www/assets).
const fs = require("node:fs");
const path = require("node:path");
const www = path.join(__dirname, "www");
const copy = (from, to) => {
  fs.mkdirSync(path.dirname(to), { recursive: true });
  fs.copyFileSync(require.resolve(from), to);
};
copy("brs-engine/lib/brs.api.js", path.join(www, "lib/brs.api.js"));
copy("brs-engine/lib/brs.worker.js", path.join(www, "lib/brs.worker.js"));
copy("brs-scenegraph/lib/brs-sg.js", path.join(www, "lib/brs-sg.js"));
// The SceneGraph extension's common.zip is a superset of the core one (fonts, dialogs).
copy("brs-scenegraph/assets/common.zip", path.join(www, "assets/common.zip"));
console.log("Simulator copied to", www);
