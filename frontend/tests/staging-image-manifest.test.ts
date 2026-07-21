import assert from "node:assert/strict";
import { test } from "node:test";
import { parseStagingImageManifest } from "../scripts/staging-image-manifest.mjs";

const gitSha = "0123456789abcdef0123456789abcdef01234567";
const apiDigest = `sha256:${"a".repeat(64)}`;
const webDigest = `sha256:${"b".repeat(64)}`;

function validManifest(): string {
  return [
    `git_sha=${gitSha}`,
    `api_digest=${apiDigest}`,
    `web_digest=${webDigest}`,
    "",
  ].join("\n");
}

test("manifest produces immutable GHCR digest references", () => {
  assert.deepEqual(parseStagingImageManifest(validManifest(), gitSha), {
    gitSha,
    apiDigest,
    webDigest,
    apiImage: `ghcr.io/jesse-ux/jyotisha-api@${apiDigest}`,
    webImage: `ghcr.io/jesse-ux/jyotisha-web@${webDigest}`,
  });
});

test("manifest rejects revision drift, mutable tags, duplicates, extras, and malformed digests", () => {
  const invalid = [
    validManifest().replace(gitSha, "f".repeat(40)),
    validManifest().replace(apiDigest, `${gitSha}`),
    validManifest().replace(apiDigest, `sha256:${"A".repeat(64)}`),
    validManifest().replace(
      `web_digest=${webDigest}`,
      `api_digest=${apiDigest}`,
    ),
    `${validManifest()}extra=value\n`,
    validManifest().replace("api_digest=", "api_image=ghcr.io/example:"),
  ];

  for (const contents of invalid) {
    assert.throws(() => parseStagingImageManifest(contents, gitSha));
  }
});
