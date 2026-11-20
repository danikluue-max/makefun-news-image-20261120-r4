// news-image-20261120 round 4 — entrypoint (Node 22, standard library only).
//
// The entry is the rendered front page beside this file. Before anything
// is copied the program validates the file end to end: it must be a real
// PNG (signature + IHDR + IEND trailer), exactly 1024x1024, and at most
// 1 MiB. A render that fails any of those checks fails loudly here
// instead of shipping a broken image to the grader.
//
// The copy is byte for byte: the file that lands in the grader's output
// directory is the exact file committed in the repo, verified by a
// SHA-256 digest printed on every run.
//
// Run locally the same way the grader does:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { createHash } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ENTRY_NAME = 'entry.png';
const MAX_BYTES = 1024 * 1024;
const EXPECTED_SIDE = 1024;
const PNG_MAGIC = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const IEND_TAIL = Buffer.from([
  0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4e, 0x44,
  0xae, 0x42, 0x60, 0x82,
]);

function fail(message) {
  throw new Error(`entry check failed: ${message}`);
}

function digestHex(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function checkPng(bytes, path) {
  if (bytes.length < PNG_MAGIC.length + 25 + IEND_TAIL.length) {
    fail(`${path} is too short to be a PNG (${bytes.length} bytes)`);
  }
  if (!bytes.subarray(0, PNG_MAGIC.length).equals(PNG_MAGIC)) {
    fail(`${path} does not start with the PNG signature`);
  }
  if (bytes.toString('ascii', 12, 16) !== 'IHDR') {
    fail(`${path} has no IHDR chunk first`);
  }
  const width = bytes.readUInt32BE(16);
  const height = bytes.readUInt32BE(20);
  if (width !== EXPECTED_SIDE || height !== EXPECTED_SIDE) {
    fail(`${path} must be ${EXPECTED_SIDE}x${EXPECTED_SIDE}, got ${width}x${height}`);
  }
  if (bytes.length > MAX_BYTES) {
    fail(`${path} must be at most 1 MiB, got ${bytes.length} bytes`);
  }
  if (!bytes.subarray(bytes.length - IEND_TAIL.length).equals(IEND_TAIL)) {
    fail(`${path} is truncated: no IEND trailer`);
  }
  return { width, height, sha256: digestHex(bytes) };
}

function main() {
  const root = dirname(fileURLToPath(import.meta.url));
  const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
  const entryPath = join(root, ENTRY_NAME);
  if (!existsSync(entryPath)) {
    fail(`missing ${entryPath}`);
  }
  const bytes = readFileSync(entryPath);
  const info = checkPng(bytes, entryPath);
  mkdirSync(outDir, { recursive: true });
  const dest = join(outDir, ENTRY_NAME);
  copyFileSync(entryPath, dest);
  const written = statSync(dest).size;
  if (written !== bytes.length) {
    fail(`copy mismatch: wrote ${written} bytes, expected ${bytes.length}`);
  }
  const again = digestHex(readFileSync(dest));
  if (again !== info.sha256) {
    fail(`digest mismatch after copy: ${again} != ${info.sha256}`);
  }
  console.log(
    `${ENTRY_NAME} ${info.width}x${info.height} ${bytes.length} bytes ` +
    `sha256=${info.sha256} -> ${dest}`,
  );
}

main();
