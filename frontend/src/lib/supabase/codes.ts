import { createHash, randomBytes } from "node:crypto";

const CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";

export function normalizeRedeemCode(code: string) {
  return code.replace(/\s/g, "").toUpperCase();
}

export function hashRedeemCode(code: string) {
  return createHash("sha256").update(code, "utf8").digest("hex");
}

export function generateRedeemCode() {
  const bytes = randomBytes(8);
  const token = Array.from(bytes, (byte) => CODE_ALPHABET[byte % CODE_ALPHABET.length]).join("");
  return `JYOTISH-${token.slice(0, 4)}-${token.slice(4)}`;
}

export function maskRedeemCode(code: string) {
  return `JYOTISH-****-${code.slice(-4)}`;
}
