import { Pool, type PoolClient } from "pg";

type LocalIdentity = Readonly<{ id: string; email: string | null }> | null;
export type LocalDatabaseRole = "authenticated" | "service_role";
type PostgresError = Error & { code?: string };
type QueryError = Readonly<{ message: string; code?: string }>;
type QueryResult = Readonly<{
  data: unknown;
  error: QueryError | null;
  count?: number | null;
}>;

type Filter =
  | Readonly<{ kind: "eq"; column: string; value: unknown }>
  | Readonly<{ kind: "in"; column: string; value: readonly unknown[] }>
  | Readonly<{ kind: "is"; column: string; value: unknown }>
  | Readonly<{ kind: "notContains"; column: string; value: unknown }>;

type Mutation =
  | Readonly<{ kind: "insert"; rows: readonly Record<string, unknown>[] }>
  | Readonly<{ kind: "update"; values: Record<string, unknown> }>
  | Readonly<{ kind: "upsert"; rows: readonly Record<string, unknown>[]; conflict: readonly string[] }>
  | Readonly<{ kind: "delete"; exactCount: boolean }>;

const identifierPattern = /^[a-z_][a-z0-9_]*$/;

function identifier(value: string): string {
  const normalized = value.trim();
  if (!identifierPattern.test(normalized)) throw new Error("unsafe database identifier");
  return `"${normalized}"`;
}

function queryError(error: unknown): QueryError {
  const value = error as PostgresError;
  return {
    message: value instanceof Error ? value.message : "database request failed",
    ...(typeof value?.code === "string" ? { code: value.code } : {}),
  };
}

function records(value: Record<string, unknown> | readonly Record<string, unknown>[]) {
  return Array.isArray(value) ? value : [value];
}

const poolGlobal = globalThis as typeof globalThis & {
  jyotishaLocalDataPools?: Map<string, Pool>;
};

function localDataPool(connectionString: string): Pool {
  poolGlobal.jyotishaLocalDataPools ??= new Map();
  let pool = poolGlobal.jyotishaLocalDataPools.get(connectionString);
  if (!pool) {
    pool = new Pool({
      connectionString,
      max: 10,
      idleTimeoutMillis: 30_000,
      connectionTimeoutMillis: 5_000,
      allowExitOnIdle: true,
      application_name: "jyotisha-business",
    });
    poolGlobal.jyotishaLocalDataPools.set(connectionString, pool);
  }
  return pool;
}

async function inBusinessTransaction<T>(
  pool: Pool,
  identity: LocalIdentity,
  role: LocalDatabaseRole,
  run: (client: PoolClient) => Promise<T>,
): Promise<T> {
  const client = await pool.connect();
  try {
    await client.query("begin");
    await client.query(`set local role ${role}`);
    await client.query(
      "select set_config('request.jwt.claim.sub', $1, true), set_config('request.jwt.claim.email', $2, true)",
      [identity?.id ?? "", identity?.email ?? ""],
    );
    const result = await run(client);
    await client.query("commit");
    return result;
  } catch (error) {
    await client.query("rollback").catch(() => undefined);
    throw error;
  } finally {
    client.release();
  }
}

async function columnTypes(
  client: PoolClient,
  table: string,
): Promise<Map<string, string>> {
  const result = await client.query<{ column_name: string; udt_name: string }>(
    `
      select column_name, udt_name
      from information_schema.columns
      where table_schema = 'public' and table_name = $1
    `,
    [table],
  );
  return new Map(result.rows.map((row) => [row.column_name, row.udt_name]));
}

function databaseValue(type: string | undefined, value: unknown): unknown {
  if ((type === "json" || type === "jsonb") && value !== null) {
    return JSON.stringify(value);
  }
  return value;
}

class LocalPostgresQueryBuilder implements PromiseLike<QueryResult> {
  private selectedColumns: string[] | null = null;
  private mutation: Mutation | null = null;
  private readonly filters: Filter[] = [];
  private ordering: Readonly<{ column: string; ascending: boolean }> | null = null;
  private rowLimit: number | null = null;
  private abort: AbortSignal | null = null;
  private cardinality: "many" | "single" | "maybeSingle" = "many";

  constructor(
    private readonly pool: Pool,
    private readonly identity: LocalIdentity,
    private readonly role: LocalDatabaseRole,
    private readonly table: string,
  ) {
    identifier(table);
  }

  select(columns = "*") {
    this.selectedColumns = columns === "*"
      ? ["*"]
      : columns.split(",").map((column) => column.trim()).filter(Boolean);
    for (const column of this.selectedColumns) {
      if (column !== "*") identifier(column);
    }
    return this;
  }

  insert(value: Record<string, unknown> | readonly Record<string, unknown>[]) {
    this.mutation = { kind: "insert", rows: records(value) };
    return this;
  }

  upsert(
    value: Record<string, unknown> | readonly Record<string, unknown>[],
    options: { onConflict: string },
  ) {
    const conflict = options.onConflict.split(",").map((column) => column.trim());
    conflict.forEach(identifier);
    this.mutation = { kind: "upsert", rows: records(value), conflict };
    return this;
  }

  update(values: Record<string, unknown>) {
    this.mutation = { kind: "update", values };
    return this;
  }

  delete(options?: { count?: string }) {
    this.mutation = { kind: "delete", exactCount: options?.count === "exact" };
    return this;
  }

  eq(column: string, value: unknown) {
    identifier(column);
    this.filters.push({ kind: "eq", column, value });
    return this;
  }

  in(column: string, value: readonly unknown[]) {
    identifier(column);
    this.filters.push({ kind: "in", column, value });
    return this;
  }

  is(column: string, value: unknown) {
    identifier(column);
    this.filters.push({ kind: "is", column, value });
    return this;
  }

  not(column: string, operator: string, value: unknown) {
    identifier(column);
    if (operator !== "cs") throw new Error("unsupported not filter");
    this.filters.push({ kind: "notContains", column, value });
    return this;
  }

  order(column: string, options: { ascending?: boolean } = {}) {
    identifier(column);
    this.ordering = { column, ascending: options.ascending !== false };
    return this;
  }

  limit(value: number) {
    if (!Number.isSafeInteger(value) || value < 0) throw new Error("invalid row limit");
    this.rowLimit = value;
    return this;
  }

  abortSignal(signal: AbortSignal) {
    this.abort = signal;
    return this;
  }

  single() {
    this.cardinality = "single";
    return this.execute();
  }

  maybeSingle() {
    this.cardinality = "maybeSingle";
    return this.execute();
  }

  then<TResult1 = QueryResult, TResult2 = never>(
    onfulfilled?: ((value: QueryResult) => TResult1 | PromiseLike<TResult1>) | null,
    onrejected?: ((reason: unknown) => TResult2 | PromiseLike<TResult2>) | null,
  ): PromiseLike<TResult1 | TResult2> {
    return this.execute().then(onfulfilled, onrejected);
  }

  private returningClause(): string {
    if (!this.selectedColumns) return "";
    return ` returning ${this.selectedColumns.map((column) => column === "*" ? "*" : identifier(column)).join(", ")}`;
  }

  private filterClause(parameters: unknown[], types: Map<string, string>): string {
    if (this.filters.length === 0) return "";
    const parts = this.filters.map((filter) => {
      const column = identifier(filter.column);
      if (filter.kind === "is") {
        if (filter.value === null) return `${column} is null`;
        if (filter.value === true) return `${column} is true`;
        if (filter.value === false) return `${column} is false`;
        throw new Error("unsupported is filter");
      }
      if (filter.kind === "in") {
        if (filter.value.length === 0) return "false";
        const placeholders = filter.value.map((value) => {
          parameters.push(databaseValue(types.get(filter.column), value));
          return `$${parameters.length}`;
        });
        return `${column} in (${placeholders.join(", ")})`;
      }
      if (filter.kind === "notContains") {
        parameters.push(databaseValue(types.get(filter.column), filter.value));
        return `not (${column} @> $${parameters.length})`;
      }
      parameters.push(databaseValue(types.get(filter.column), filter.value));
      return `${column} = $${parameters.length}`;
    });
    return ` where ${parts.join(" and ")}`;
  }

  private async execute(): Promise<QueryResult> {
    if (this.abort?.aborted) {
      return { data: null, error: { message: "AbortError" } };
    }
    try {
      return await inBusinessTransaction(this.pool, this.identity, this.role, async (client) => {
        const types = await columnTypes(client, this.table);
        const parameters: unknown[] = [];
        let sql: string;

        if (!this.mutation) {
          const selected = (this.selectedColumns ?? ["*"])
            .map((column) => column === "*" ? "*" : identifier(column))
            .join(", ");
          sql = `select ${selected} from public.${identifier(this.table)}`;
          sql += this.filterClause(parameters, types);
          if (this.ordering) {
            sql += ` order by ${identifier(this.ordering.column)} ${this.ordering.ascending ? "asc" : "desc"}`;
          }
          if (this.rowLimit !== null) sql += ` limit ${this.rowLimit}`;
        } else if (this.mutation.kind === "insert" || this.mutation.kind === "upsert") {
          const rows = this.mutation.rows;
          if (rows.length === 0) return { data: this.selectedColumns ? [] : null, error: null };
          const columns = Object.keys(rows[0] ?? {});
          if (columns.length === 0 || rows.some((row) => Object.keys(row).join("\0") !== columns.join("\0"))) {
            throw new Error("inconsistent insert rows");
          }
          columns.forEach(identifier);
          const valueGroups = rows.map((row) => `(${columns.map((column) => {
            parameters.push(databaseValue(types.get(column), row[column]));
            return `$${parameters.length}`;
          }).join(", ")})`);
          sql = `insert into public.${identifier(this.table)} (${columns.map(identifier).join(", ")}) values ${valueGroups.join(", ")}`;
          if (this.mutation.kind === "upsert") {
            const updates = columns.filter((column) => !this.mutation || this.mutation.kind !== "upsert" || !this.mutation.conflict.includes(column));
            sql += ` on conflict (${this.mutation.conflict.map(identifier).join(", ")}) do ${updates.length === 0
              ? "nothing"
              : `update set ${updates.map((column) => `${identifier(column)} = excluded.${identifier(column)}`).join(", ")}`}`;
          }
          sql += this.returningClause();
        } else if (this.mutation.kind === "update") {
          const columns = Object.keys(this.mutation.values);
          if (columns.length === 0) throw new Error("empty update");
          const assignments = columns.map((column) => {
            identifier(column);
            parameters.push(databaseValue(types.get(column), this.mutation && this.mutation.kind === "update" ? this.mutation.values[column] : null));
            return `${identifier(column)} = $${parameters.length}`;
          });
          sql = `update public.${identifier(this.table)} set ${assignments.join(", ")}`;
          sql += this.filterClause(parameters, types);
          sql += this.returningClause();
        } else {
          sql = `delete from public.${identifier(this.table)}`;
          sql += this.filterClause(parameters, types);
          sql += this.returningClause();
        }

        const result = await client.query(sql, parameters);
        const rows = result.rows;
        let data: unknown = this.selectedColumns ? rows : null;
        if (this.cardinality !== "many") {
          if (rows.length > 1 || (this.cardinality === "single" && rows.length !== 1)) {
            return { data: null, error: { code: "PGRST116", message: "unexpected row count" } };
          }
          data = rows[0] ?? null;
        }
        return {
          data,
          error: null,
          ...(this.mutation?.kind === "delete" && this.mutation.exactCount
            ? { count: result.rowCount ?? 0 }
            : {}),
        };
      });
    } catch (error) {
      return { data: null, error: queryError(error), count: null };
    }
  }
}

type FunctionMetadata = Readonly<{
  proretset: boolean;
  return_type: string;
  argument_names: string[] | null;
  argument_types: string[];
}>;

async function functionMetadata(
  client: PoolClient,
  functionName: string,
  argumentNames: readonly string[],
): Promise<FunctionMetadata> {
  const result = await client.query<FunctionMetadata>(
    `
      select
        p.proretset,
        format_type(p.prorettype, null) as return_type,
        p.proargnames as argument_names,
        array(
          select format_type(argument_type, null)
          from unnest(p.proargtypes) argument_type
        ) as argument_types
      from pg_proc p
      join pg_namespace n on n.oid = p.pronamespace
      where n.nspname = 'public'
        and p.proname = $1
        and $2::text[] <@ coalesce(p.proargnames, '{}'::text[])
      order by cardinality(p.proargtypes) asc
      limit 1
    `,
    [functionName, argumentNames],
  );
  const metadata = result.rows[0];
  if (!metadata) throw new Error("database function not found");
  return metadata;
}

function castType(value: string): string {
  if (!/^[a-z0-9_ .\[\]]+$/.test(value)) throw new Error("unsafe database type");
  return value;
}

export class LocalPostgresDataClient {
  readonly auth: Readonly<{
    getUser: () => Promise<Readonly<{
      data: { user: LocalIdentity };
      error: null;
    }>>;
  }>;

  private readonly pool: Pool;

  constructor(
    connectionString: string,
    private readonly identity: LocalIdentity,
    private readonly role: LocalDatabaseRole,
  ) {
    if (role !== "authenticated" && role !== "service_role") {
      throw new Error("unsupported database role");
    }
    this.pool = localDataPool(connectionString);
    this.auth = {
      getUser: async () => ({ data: { user: this.identity }, error: null }),
    };
  }

  from(table: string) {
    return new LocalPostgresQueryBuilder(this.pool, this.identity, this.role, table);
  }

  async rpc(functionName: string, args: Readonly<Record<string, unknown>> = {}) {
    try {
      identifier(functionName);
      return await inBusinessTransaction(this.pool, this.identity, this.role, async (client) => {
        const names = Object.keys(args);
        names.forEach(identifier);
        const metadata = await functionMetadata(client, functionName, names);
        const typeByName = new Map(
          (metadata.argument_names ?? []).map((name, index) => [name, metadata.argument_types[index]]),
        );
        const parameters = names.map((name) =>
          databaseValue(typeByName.get(name), args[name]));
        const call = names.map((name, index) =>
          `${identifier(name)} => $${index + 1}::${castType(typeByName.get(name) ?? "text")}`,
        ).join(", ");
        const sql = metadata.proretset
          ? `select * from public.${identifier(functionName)}(${call})`
          : `select public.${identifier(functionName)}(${call}) as value`;
        const result = await client.query(sql, parameters);
        return {
          data: metadata.proretset ? result.rows : result.rows[0]?.value ?? null,
          error: null,
        };
      });
    } catch (error) {
      return { data: null, error: queryError(error) };
    }
  }
}

export function createLocalPostgresDataClient(
  connectionString: string,
  identity: LocalIdentity = null,
  role: LocalDatabaseRole = "authenticated",
) {
  return new LocalPostgresDataClient(connectionString, identity, role);
}
