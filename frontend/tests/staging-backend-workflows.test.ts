import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const workflowUrl = new URL(
  "../../.github/workflows/backend-quality-gate.yml",
  import.meta.url,
);

function workflowSource(): string {
  return readFileSync(workflowUrl, "utf8");
}

function jobSource(workflow: string, job: "validate" | "publish"): string {
  const nextJob = job === "validate" ? "publish" : undefined;
  const pattern = nextJob
    ? new RegExp(`^  ${job}:\\n([\\s\\S]*?)(?=^  ${nextJob}:\\n)`, "m")
    : new RegExp(`^  ${job}:\\n([\\s\\S]*)$`, "m");
  const match = workflow.match(pattern);
  assert.ok(match, `${job} job is missing`);
  return match[0];
}

test("backend quality gate covers pull requests, staging pushes, and manual runs", () => {
  const workflow = workflowSource();

  assert.match(workflow, /^name: Staging Backend Quality Gate$/m);
  assert.match(workflow, /^on:\n  pull_request:\n  push:\n    branches: \[staging\]\n  workflow_dispatch:$/m);
  assert.match(
    workflow,
    /^concurrency:\n  group: backend-quality-\$\{\{ github\.workflow \}\}-\$\{\{ github\.ref \}\}\n  cancel-in-progress: true$/m,
  );
  assert.match(workflow, /^permissions:\n  contents: read$/m);
});

test("validation runs the database, frontend, and existing Python quick gates", () => {
  const validate = jobSource(workflowSource(), "validate");

  assert.match(validate, /runs-on: ubuntu-latest/);
  assert.match(validate, /timeout-minutes: 30/);
  assert.match(validate, /actions\/setup-python@v5[\s\S]*python-version: ['"]3\.12['"]/);
  assert.match(validate, /actions\/setup-node@v4[\s\S]*node-version: ['"]22['"]/);
  assert.match(
    validate,
    /python -m pip install -r requirements\.txt -r requirements-dev\.txt/,
  );
  assert.match(validate, /npm ci --prefix frontend/);
  assert.match(
    validate,
    /ruff check scripts\/run_quality_gate\.py tests\/test_varga_bphs\.py \\\n\s+tests\/test_ashtakavarga_invariants\.py tests\/test_cli_smoke\.py \\\n\s+tests\/test_yoga_rules_integrity\.py/,
  );
  assert.match(
    validate,
    /python -m py_compile scripts\/\*\.py jyotish_vedic\/\*\.py mcp_server\.py/,
  );
  assert.match(
    validate,
    /python scripts\/run_quality_gate\.py \\\n\s+--profile quick --skip-yoga-logic --skip-frontend-runtime \\\n\s+2>&1 \| tee artifacts\/quick-quality-gate\.log/,
  );
  assert.match(validate, /python -m build --no-isolation/);
  assert.match(validate, /npm run test:db --prefix frontend/);
  assert.match(validate, /npm test --prefix frontend/);
  assert.match(validate, /npm run lint --prefix frontend/);
  assert.match(validate, /npm run build --prefix frontend/);
  assert.match(
    validate,
    /NEXT_PUBLIC_SUPABASE_URL: https:\/\/placeholder\.supabase\.co/,
  );
  assert.match(validate, /NEXT_PUBLIC_SUPABASE_ANON_KEY: placeholder/);
  assert.match(
    validate,
    /name: Upload quick quality gate diagnostics[\s\S]*if: always\(\)[\s\S]*actions\/upload-artifact@v4[\s\S]*path: artifacts\/quick-quality-gate\.log/,
  );
  assert.doesNotMatch(validate, /packages: write/);
});

test("publishing waits for validation and publishes immutable staging SHA images", () => {
  const workflow = workflowSource();
  const publish = jobSource(workflow, "publish");

  assert.match(
    publish,
    /if: github\.event_name == 'push' && github\.ref == 'refs\/heads\/staging'/,
  );
  assert.match(publish, /needs: validate/);
  assert.match(
    publish,
    /permissions:\n      contents: read\n      packages: write/,
  );
  assert.match(publish, /docker\/login-action@v3/);
  assert.match(publish, /password: \$\{\{ secrets\.GITHUB_TOKEN \}\}/);
  assert.equal(publish.match(/docker\/build-push-action@v6/g)?.length, 2);
  assert.match(
    publish,
    /context: \.\n\s+file: deploy\/railway-api\.Dockerfile[\s\S]*push: true[\s\S]*tags: ghcr\.io\/jesse-ux\/jyotisha-api:\$\{\{ github\.sha \}\}/,
  );
  assert.match(
    publish,
    /context: \.\n\s+file: deploy\/railway-web\.Dockerfile[\s\S]*push: true[\s\S]*tags: ghcr\.io\/jesse-ux\/jyotisha-web:\$\{\{ github\.sha \}\}[\s\S]*build-args: \|\n\s+NEXT_PUBLIC_SUPABASE_URL=https:\/\/placeholder\.supabase\.co\n\s+NEXT_PUBLIC_SUPABASE_ANON_KEY=placeholder/,
  );
  assert.doesNotMatch(publish, /(?:^|:)latest(?:$|\s)/m);
});
