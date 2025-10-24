import { helpers } from "../dev-handler.mjs";

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function testChunkText() {
  const chunks = helpers.chunkText("a".repeat(2000), 100, 10);
  assert(chunks.length > 0, "chunkText should return chunks");
}

function testClassifyIntent() {
  assert(
    helpers.classifyIntent("Summarize this") === "summary",
    "summary intent failed"
  );
  assert(
    helpers.classifyIntent("Compare X and Y") === "compare",
    "compare intent failed"
  );
  assert(
    helpers.classifyIntent("What is this?") === "qa",
    "qa intent failed"
  );
}

testChunkText();
testClassifyIntent();

console.log("Smoke tests passed ✅");
