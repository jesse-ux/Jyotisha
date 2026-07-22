import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { Pool } from "pg";

class SafeImportError extends Error {}

function requiredDate(value, field) {
  const date = new Date(value);
  if (!value || !Number.isFinite(date.getTime())) {
    throw new SafeImportError(`source contains an invalid ${field}`);
  }
  return date;
}

function optionalDate(value, field) {
  if (value === null || value === undefined || value === "") return null;
  return requiredDate(value, field);
}

function metadataValue(metadata, key) {
  if (!metadata || typeof metadata !== "object" || Array.isArray(metadata)) {
    return null;
  }
  const value = metadata[key];
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

export function normalizeSupabaseUsers(source) {
  if (!Array.isArray(source)) {
    throw new SafeImportError("source must be a JSON array of auth users");
  }

  const emails = new Set();
  return source.map((record) => {
    if (!record || typeof record !== "object" || Array.isArray(record)) {
      throw new SafeImportError("source contains an invalid auth user");
    }

    const id = typeof record.id === "string" ? record.id.trim().toLowerCase() : "";
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(id)) {
      throw new SafeImportError("source contains an invalid user id");
    }
    const email =
      typeof record.email === "string" ? record.email.trim().toLowerCase() : "";
    if (!/^[^\s@]+@[^\s@]+$/.test(email)) {
      throw new SafeImportError("source contains an invalid user email");
    }
    if (emails.has(email)) {
      throw new SafeImportError("source contains duplicate canonical emails");
    }
    emails.add(email);

    const emailVerifiedAt = optionalDate(
      record.email_confirmed_at,
      "email confirmation timestamp",
    );
    const metadata = record.raw_user_meta_data;
    const name =
      metadataValue(metadata, "full_name") ??
      metadataValue(metadata, "name") ??
      email.slice(0, email.indexOf("@"));

    return {
      id,
      email,
      emailVerified: emailVerifiedAt !== null,
      emailVerifiedAt,
      name,
      image:
        metadataValue(metadata, "avatar_url") ??
        metadataValue(metadata, "picture"),
      createdAt: requiredDate(record.created_at, "creation timestamp"),
      updatedAt: requiredDate(record.updated_at, "update timestamp"),
    };
  });
}

export async function applyIdentityUsers(client, users) {
  await client.query("BEGIN");
  try {
    for (const user of users) {
      await client.query(
        `
          insert into identity.users (
            id, name, email, email_verified, email_verified_at, image,
            created_at, updated_at
          ) values ($1, $2, $3, $4, $5, $6, $7, $8)
          on conflict (id) do update set
            name = excluded.name,
            email = excluded.email,
            email_verified = excluded.email_verified,
            email_verified_at = excluded.email_verified_at,
            image = excluded.image,
            created_at = excluded.created_at,
            updated_at = excluded.updated_at
        `,
        [
          user.id,
          user.name,
          user.email,
          user.emailVerified,
          user.emailVerifiedAt,
          user.image,
          user.createdAt,
          user.updatedAt,
        ],
      );
    }
    await client.query("COMMIT");
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  }
}

function parseArguments(arguments_) {
  const apply = arguments_.includes("--apply");
  const positional = arguments_.filter((argument) => argument !== "--apply");
  if (positional.length !== 1 || arguments_.some((argument) => argument.startsWith("--") && argument !== "--apply")) {
    throw new SafeImportError(
      "usage: node scripts/import-supabase-auth-users.mjs <export.json> [--apply]",
    );
  }
  return { apply, sourcePath: positional[0] };
}

async function loadUsers(sourcePath) {
  let contents;
  try {
    contents = await readFile(sourcePath, "utf8");
  } catch {
    throw new SafeImportError("unable to read source file");
  }

  try {
    return normalizeSupabaseUsers(JSON.parse(contents));
  } catch (error) {
    if (error instanceof SafeImportError) throw error;
    throw new SafeImportError("source file is not valid JSON");
  }
}

export async function main(arguments_, env) {
  const { apply, sourcePath } = parseArguments(arguments_);
  const users = await loadUsers(sourcePath);
  const summary = {
    mode: apply ? "apply" : "dry-run",
    users: users.length,
    verified: users.filter((user) => user.emailVerified).length,
  };

  if (!apply) {
    process.stdout.write(`${JSON.stringify(summary)}\n`);
    return;
  }

  const databaseUrl = env.IDENTITY_DATABASE_URL?.trim();
  if (!databaseUrl) {
    throw new SafeImportError("IDENTITY_DATABASE_URL is required for --apply");
  }
  if (!databaseUrl.startsWith("postgresql://")) {
    throw new SafeImportError("IDENTITY_DATABASE_URL must be a PostgreSQL URL");
  }

  const pool = new Pool({
    connectionString: databaseUrl,
    options: "-c search_path=identity,pg_catalog",
    application_name: "jyotisha-identity-import",
    max: 1,
  });
  try {
    const client = await pool.connect();
    try {
      await applyIdentityUsers(client, users);
    } finally {
      client.release();
    }
  } catch {
    throw new SafeImportError("identity user import failed");
  } finally {
    await pool.end();
  }
  process.stdout.write(`${JSON.stringify(summary)}\n`);
}

const invokedPath = process.argv[1] ? pathToFileURL(resolve(process.argv[1])).href : "";
if (import.meta.url === invokedPath) {
  main(process.argv.slice(2), process.env).catch((error) => {
    const message =
      error instanceof SafeImportError ? error.message : "identity user import failed";
    process.stderr.write(`${message}\n`);
    process.exitCode = 1;
  });
}
