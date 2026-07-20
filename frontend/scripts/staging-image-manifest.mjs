import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const shaPattern = /^[0-9a-f]{40}$/;
const digestPattern = /^sha256:[0-9a-f]{64}$/;
const expectedKeys = ["git_sha", "api_digest", "web_digest"];

export function parseStagingImageManifest(text, expectedSha) {
  if (!shaPattern.test(expectedSha)) {
    throw new Error("invalid expected staging revision");
  }

  const lines = text.endsWith("\n") ? text.slice(0, -1).split("\n") : text.split("\n");
  if (lines.length !== expectedKeys.length) {
    throw new Error("invalid staging image manifest");
  }

  const values = new Map();
  for (const line of lines) {
    const separator = line.indexOf("=");
    if (separator <= 0) throw new Error("invalid staging image manifest");
    const key = line.slice(0, separator);
    const value = line.slice(separator + 1);
    if (!expectedKeys.includes(key) || values.has(key)) {
      throw new Error("invalid staging image manifest");
    }
    values.set(key, value);
  }

  if (values.get("git_sha") !== expectedSha) {
    throw new Error("staging image manifest revision mismatch");
  }
  for (const key of ["api_digest", "web_digest"]) {
    if (!digestPattern.test(values.get(key) ?? "")) {
      throw new Error("invalid staging image digest");
    }
  }

  return {
    gitSha: expectedSha,
    apiDigest: values.get("api_digest"),
    webDigest: values.get("web_digest"),
    apiImage: `ghcr.io/jesse-ux/jyotisha-api@${values.get("api_digest")}`,
    webImage: `ghcr.io/jesse-ux/jyotisha-web@${values.get("web_digest")}`,
  };
}

const invokedPath = process.argv[1]
  ? pathToFileURL(resolve(process.argv[1])).href
  : undefined;

if (invokedPath === import.meta.url) {
  try {
    const [manifestPath, expectedSha] = process.argv.slice(2);
    if (!manifestPath || !expectedSha) {
      throw new Error("manifest path and expected revision are required");
    }
    const manifest = parseStagingImageManifest(
      await readFile(manifestPath, "utf8"),
      expectedSha,
    );
    process.stdout.write(
      [
        `git_sha=${manifest.gitSha}`,
        `api_image=${manifest.apiImage}`,
        `web_image=${manifest.webImage}`,
      ].join("\n") + "\n",
    );
  } catch {
    console.error("invalid staging image manifest");
    process.exitCode = 1;
  }
}
