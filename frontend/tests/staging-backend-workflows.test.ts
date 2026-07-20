import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

type YamlNode = {
  key: string;
  value: string;
  indent: number;
  start: number;
  end: number;
};

type WorkflowDocument = {
  lines: string[];
  root: YamlNode[];
};

type WorkflowStep = {
  node: YamlNode;
  name: string;
};

const workflowUrl = new URL(
  "../../.github/workflows/backend-quality-gate.yml",
  import.meta.url,
);

function indentation(line: string): number {
  return line.match(/^ */)?.[0].length ?? 0;
}

function mappingNodes(
  lines: string[],
  indent: number,
  start = 0,
  end = lines.length,
): YamlNode[] {
  const nodes: YamlNode[] = [];
  for (let index = start; index < end; index += 1) {
    const line = lines[index];
    if (!line.trim() || indentation(line) !== indent) continue;
    const match = line.slice(indent).match(/^([^:#][^:]*):(?:\s+(.*))?$/);
    if (!match) continue;
    let nodeEnd = end;
    for (let cursor = index + 1; cursor < end; cursor += 1) {
      if (!lines[cursor].trim()) continue;
      if (indentation(lines[cursor]) <= indent) {
        nodeEnd = cursor;
        break;
      }
    }
    nodes.push({
      key: match[1],
      value: match[2] ?? "",
      indent,
      start: index,
      end: nodeEnd,
    });
  }
  return nodes;
}

function parseWorkflow(): WorkflowDocument {
  const lines = readFileSync(workflowUrl, "utf8").split("\n");
  return { lines, root: mappingNodes(lines, 0) };
}

function requiredNode(nodes: YamlNode[], key: string): YamlNode {
  const matches = nodes.filter((node) => node.key === key);
  assert.equal(matches.length, 1, `expected exactly one YAML key: ${key}`);
  return matches[0];
}

function children(document: WorkflowDocument, parent: YamlNode): YamlNode[] {
  return mappingNodes(
    document.lines,
    parent.indent + 2,
    parent.start + 1,
    parent.end,
  );
}

function child(
  document: WorkflowDocument,
  parent: YamlNode,
  key: string,
): YamlNode {
  return requiredNode(children(document, parent), key);
}

function blockScalar(document: WorkflowDocument, node: YamlNode): string {
  assert.equal(node.value, "|", `${node.key} must be a literal block scalar`);
  const contentIndent = node.indent + 2;
  return document.lines
    .slice(node.start + 1, node.end)
    .filter((line) => line.trim())
    .map((line) => {
      assert.ok(
        indentation(line) >= contentIndent,
        `${node.key} contains an outdented block-scalar line`,
      );
      return line.slice(contentIndent);
    })
    .join("\n");
}

function job(
  document: WorkflowDocument,
  name: "validate" | "publish",
): YamlNode {
  return child(document, requiredNode(document.root, "jobs"), name);
}

function steps(document: WorkflowDocument, jobNode: YamlNode): WorkflowStep[] {
  const stepsNode = child(document, jobNode, "steps");
  const stepIndent = stepsNode.indent + 2;
  const result: WorkflowStep[] = [];
  for (
    let index = stepsNode.start + 1;
    index < stepsNode.end;
    index += 1
  ) {
    const line = document.lines[index];
    if (indentation(line) !== stepIndent) continue;
    const match = line.slice(stepIndent).match(/^- name:\s+(.+)$/);
    if (!match) continue;
    let stepEnd = stepsNode.end;
    for (let cursor = index + 1; cursor < stepsNode.end; cursor += 1) {
      if (
        indentation(document.lines[cursor]) === stepIndent &&
        document.lines[cursor].slice(stepIndent).startsWith("- ")
      ) {
        stepEnd = cursor;
        break;
      }
    }
    result.push({
      name: match[1],
      node: {
        key: match[1],
        value: "",
        indent: stepIndent,
        start: index,
        end: stepEnd,
      },
    });
  }
  return result;
}

function requiredStep(
  document: WorkflowDocument,
  jobNode: YamlNode,
  name: string,
): WorkflowStep {
  const matches = steps(document, jobNode).filter((step) => step.name === name);
  assert.equal(matches.length, 1, `expected exactly one workflow step: ${name}`);
  return matches[0];
}

function stepField(
  document: WorkflowDocument,
  step: WorkflowStep,
  key: string,
): YamlNode {
  return requiredNode(
    mappingNodes(
      document.lines,
      step.node.indent + 2,
      step.node.start + 1,
      step.node.end,
    ),
    key,
  );
}

test("backend quality gate has structured staging triggers and concurrency", () => {
  const document = parseWorkflow();

  assert.equal(requiredNode(document.root, "name").value, "Staging Backend Quality Gate");
  const triggers = requiredNode(document.root, "on");
  assert.equal(child(document, triggers, "pull_request").value, "");
  const push = child(document, triggers, "push");
  assert.equal(child(document, push, "branches").value, "[staging]");
  assert.equal(child(document, triggers, "workflow_dispatch").value, "");

  const concurrency = requiredNode(document.root, "concurrency");
  assert.equal(
    child(document, concurrency, "group").value,
    "backend-quality-${{ github.workflow }}-${{ github.ref }}",
  );
  assert.equal(child(document, concurrency, "cancel-in-progress").value, "true");
  const permissions = requiredNode(document.root, "permissions");
  assert.deepEqual(
    children(document, permissions).map(({ key, value }) => [key, value]),
    [["contents", "read"]],
  );
  assert.deepEqual(
    children(document, requiredNode(document.root, "jobs")).map(
      ({ key }) => key,
    ),
    ["validate", "publish"],
  );
});

test("validation locates every command in its intended job and step", () => {
  const document = parseWorkflow();
  const validate = job(document, "validate");

  assert.equal(child(document, validate, "runs-on").value, "ubuntu-latest");
  assert.equal(child(document, validate, "timeout-minutes").value, "30");
  assert.equal(
    stepField(
      document,
      requiredStep(document, validate, "Set up Python"),
      "uses",
    ).value,
    "actions/setup-python@v5",
  );
  assert.equal(
    stepField(
      document,
      requiredStep(document, validate, "Set up Node"),
      "uses",
    ).value,
    "actions/setup-node@v4",
  );
  assert.equal(
    child(
      document,
      stepField(
        document,
        requiredStep(document, validate, "Set up Python"),
        "with",
      ),
      "python-version",
    ).value,
    "'3.12'",
  );
  assert.equal(
    child(
      document,
      stepField(
        document,
        requiredStep(document, validate, "Set up Node"),
        "with",
      ),
      "node-version",
    ).value,
    "'22'",
  );

  const install = blockScalar(
    document,
    stepField(
      document,
      requiredStep(document, validate, "Install dependencies"),
      "run",
    ),
  );
  assert.match(
    install,
    /python -m pip install -r requirements\.txt -r requirements-dev\.txt/,
  );
  assert.match(install, /npm ci --prefix frontend/);

  const pythonStep = requiredStep(
    document,
    validate,
    "Run Python quick quality gate",
  );
  assert.equal(stepField(document, pythonStep, "shell").value, "bash");
  const pythonGate = blockScalar(
    document,
    stepField(document, pythonStep, "run"),
  );
  assert.match(pythonGate, /^set -o pipefail\n/);
  assert.match(
    pythonGate,
    /ruff check scripts\/run_quality_gate\.py tests\/test_varga_bphs\.py \\\n\s+tests\/test_ashtakavarga_invariants\.py tests\/test_cli_smoke\.py \\\n\s+tests\/test_yoga_rules_integrity\.py/,
  );
  assert.match(
    pythonGate,
    /python -m py_compile scripts\/\*\.py jyotish_vedic\/\*\.py mcp_server\.py/,
  );
  assert.match(
    pythonGate,
    /python scripts\/run_quality_gate\.py \\\n\s+--profile quick --skip-yoga-logic --skip-frontend-runtime \\\n\s+2>&1 \| tee artifacts\/quick-quality-gate\.log/,
  );
  assert.match(pythonGate, /python -m build --no-isolation/);

  assert.equal(
    stepField(
      document,
      requiredStep(document, validate, "Run database tests"),
      "run",
    ).value,
    "npm run test:db --prefix frontend",
  );
  const frontend = requiredStep(document, validate, "Validate frontend");
  const frontendEnv = stepField(document, frontend, "env");
  assert.equal(
    child(document, frontendEnv, "NEXT_PUBLIC_SUPABASE_URL").value,
    "https://placeholder.supabase.co",
  );
  assert.equal(
    child(document, frontendEnv, "NEXT_PUBLIC_SUPABASE_ANON_KEY").value,
    "placeholder",
  );
  assert.equal(
    blockScalar(document, stepField(document, frontend, "run")),
    [
      "npm test --prefix frontend",
      "npm run lint --prefix frontend",
      "npm run build --prefix frontend",
    ].join("\n"),
  );
  assert.equal(
    children(document, validate).some((node) => node.key === "permissions"),
    false,
  );
});

test("diagnostic artifact upload is always executed in validation", () => {
  const document = parseWorkflow();
  const upload = requiredStep(
    document,
    job(document, "validate"),
    "Upload quick quality gate diagnostics",
  );

  assert.equal(stepField(document, upload, "if").value, "always()");
  assert.equal(
    stepField(document, upload, "uses").value,
    "actions/upload-artifact@v4",
  );
  assert.equal(
    child(document, stepField(document, upload, "with"), "path").value,
    "artifacts/quick-quality-gate.log",
  );
});

test("publishing has job-local permissions and immutable staging SHA images", () => {
  const document = parseWorkflow();
  const publish = job(document, "publish");

  assert.equal(
    child(document, publish, "if").value,
    "github.event_name == 'push' && github.ref == 'refs/heads/staging'",
  );
  assert.equal(child(document, publish, "needs").value, "validate");
  assert.deepEqual(
    children(document, child(document, publish, "permissions")).map(
      ({ key, value }) => [key, value],
    ),
    [
      ["contents", "read"],
      ["packages", "write"],
    ],
  );

  const login = requiredStep(document, publish, "Log in to GHCR");
  assert.equal(stepField(document, login, "uses").value, "docker/login-action@v3");
  assert.equal(
    child(document, stepField(document, login, "with"), "password").value,
    "${{ secrets.GITHUB_TOKEN }}",
  );

  for (const [name, dockerfile, tag] of [
    [
      "Build and publish API image",
      "deploy/railway-api.Dockerfile",
      "ghcr.io/jesse-ux/jyotisha-api:${{ github.sha }}",
    ],
    [
      "Build and publish web image",
      "deploy/railway-web.Dockerfile",
      "ghcr.io/jesse-ux/jyotisha-web:${{ github.sha }}",
    ],
  ]) {
    const build = requiredStep(document, publish, name);
    assert.equal(
      stepField(document, build, "uses").value,
      "docker/build-push-action@v6",
    );
    const options = stepField(document, build, "with");
    assert.equal(child(document, options, "context").value, ".");
    assert.equal(child(document, options, "file").value, dockerfile);
    assert.equal(child(document, options, "push").value, "true");
    assert.equal(child(document, options, "tags").value, tag);
    assert.doesNotMatch(tag, /(?:^|:)latest$/);
  }

  const webOptions = stepField(
    document,
    requiredStep(document, publish, "Build and publish web image"),
    "with",
  );
  assert.equal(
    blockScalar(document, child(document, webOptions, "build-args")),
    [
      "NEXT_PUBLIC_SUPABASE_URL=https://placeholder.supabase.co",
      "NEXT_PUBLIC_SUPABASE_ANON_KEY=placeholder",
    ].join("\n"),
  );
});

test("deployment test script covers health and backend workflow contracts", () => {
  const packageJson = JSON.parse(
    readFileSync(new URL("../package.json", import.meta.url), "utf8"),
  ) as { scripts: Record<string, string> };
  assert.equal(
    packageJson.scripts["test:deployment"],
    "tsx --test tests/health-deployment.test.ts tests/staging-backend-workflows.test.ts",
  );
});
