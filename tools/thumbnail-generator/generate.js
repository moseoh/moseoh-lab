#!/usr/bin/env node

import { AutoThumbnailGenerator } from "./auto-generator.js";

const configPaths = ["./config/logo.json", "./config/book-cover.json"];

for (const configPath of configPaths) {
  const generator = new AutoThumbnailGenerator(configPath);
  await generator.generateAll();
  console.log();
  console.log("============================");
  console.log();
}
