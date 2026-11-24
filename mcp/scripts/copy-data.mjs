// Copy the built static API (../api/v1) and the calculator into the package so it runs with no network.
import { cpSync, mkdirSync } from "node:fs";
const here = new URL("..", import.meta.url);
mkdirSync(new URL("data/", here), { recursive: true });
cpSync(new URL("../api/v1/facts.json", here), new URL("data/facts.json", here));
cpSync(new URL("../tools/calculator.mjs", here), new URL("data/calculator.mjs", here));
console.log("copied facts.json and calculator.mjs into mcp/data/");
