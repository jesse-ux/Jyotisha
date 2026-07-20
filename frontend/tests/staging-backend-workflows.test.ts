import assert from "node:assert/strict";
import {
  chmodSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
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

const backendWorkflowUrl = new URL(
  "../../.github/workflows/backend-quality-gate.yml",
  import.meta.url,
);
const deploymentWorkflowUrl = new URL(
  "../../.github/workflows/deploy-staging.yml",
  import.meta.url,
);
const migrationWorkflowUrl = new URL(
  "../../.github/workflows/migrate-staging-database.yml",
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

function parseWorkflow(url = backendWorkflowUrl): WorkflowDocument {
  const lines = readFileSync(url, "utf8").split("\n");
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

function job(document: WorkflowDocument, name: string): YamlNode {
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

function stepRun(document: WorkflowDocument, step: WorkflowStep): string {
  const run = stepField(document, step, "run");
  return run.value === "|" ? blockScalar(document, run) : run.value;
}

function logicalShellLines(script: string): string[] {
  return script
    .replace(/\\\n\s*/g, " ")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
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
  const publishSteps = steps(document, publish);
  const publishStepNames = publishSteps.map(({ name }) => name);

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

  assert.ok(
    publishStepNames.indexOf("Validate staging web build variables") <
      publishStepNames.indexOf("Build and publish API image"),
  );
  assert.ok(
    publishStepNames.indexOf("Validate staging web build variables") <
      publishStepNames.indexOf("Build and publish web image"),
  );

  const stagingVariables = requiredStep(
    document,
    publish,
    "Validate staging web build variables",
  );
  const stagingVariableEnv = stepField(document, stagingVariables, "env");
  assert.equal(
    child(document, stagingVariableEnv, "STAGING_SUPABASE_URL").value,
    "${{ vars.STAGING_SUPABASE_URL }}",
  );
  assert.equal(
    child(document, stagingVariableEnv, "STAGING_SUPABASE_ANON_KEY").value,
    "${{ vars.STAGING_SUPABASE_ANON_KEY }}",
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
      "NEXT_PUBLIC_SUPABASE_URL=${{ vars.STAGING_SUPABASE_URL }}",
      "NEXT_PUBLIC_SUPABASE_ANON_KEY=${{ vars.STAGING_SUPABASE_ANON_KEY }}",
    ].join("\n"),
  );

  const validateFrontend = requiredStep(
    document,
    job(document, "validate"),
    "Validate frontend",
  );
  const outsideValidationBuild = [
    ...document.lines.slice(0, validateFrontend.node.start),
    ...document.lines.slice(validateFrontend.node.end),
  ].join("\n");
  assert.doesNotMatch(outsideValidationBuild, /placeholder/);
});

test("publishing fails closed for missing or invalid staging web variables without exposing values", () => {
  const document = parseWorkflow();
  const validation = requiredStep(
    document,
    job(document, "publish"),
    "Validate staging web build variables",
  );
  const script = stepRun(document, validation);
  const secretFixture = "anon-fixture-must-not-appear";
  const validUrl = "https://project-ref.supabase.co";
  const invalidUrl = "http://project-ref.supabase.co";
  const run = (url: string, anonKey: string) =>
    spawnSync("bash", ["-c", script], {
      encoding: "utf8",
      env: {
        ...process.env,
        STAGING_SUPABASE_URL: url,
        STAGING_SUPABASE_ANON_KEY: anonKey,
      },
    });

  assert.match(script, /test -n "\$STAGING_SUPABASE_URL"/);
  assert.match(script, /test -n "\$STAGING_SUPABASE_ANON_KEY"/);
  assert.doesNotMatch(script, /echo[^\n]*\$STAGING_SUPABASE_(?:URL|ANON_KEY)/);

  for (const failed of [
    run("", secretFixture),
    run(validUrl, ""),
    run(invalidUrl, secretFixture),
  ]) {
    assert.notEqual(failed.status, 0);
    assert.doesNotMatch(`${failed.stdout}\n${failed.stderr}`, new RegExp(secretFixture));
    assert.doesNotMatch(`${failed.stdout}\n${failed.stderr}`, new RegExp(invalidUrl));
  }
  assert.equal(run(validUrl, secretFixture).status, 0);
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

test("staging deploy structurally follows the backend gate and validates an exact manual SHA", () => {
  const document = parseWorkflow(deploymentWorkflowUrl);

  assert.equal(requiredNode(document.root, "name").value, "Deploy staging");
  const triggers = requiredNode(document.root, "on");
  const workflowRun = child(document, triggers, "workflow_run");
  assert.equal(
    child(document, workflowRun, "workflows").value,
    '["Staging Backend Quality Gate"]',
  );
  assert.equal(child(document, workflowRun, "types").value, "[completed]");
  const dispatch = child(document, triggers, "workflow_dispatch");
  const deploySha = child(document, child(document, dispatch, "inputs"), "deploy_sha");
  assert.equal(child(document, deploySha, "required").value, "true");
  assert.equal(child(document, deploySha, "type").value, "string");

  assert.deepEqual(
    children(document, requiredNode(document.root, "permissions")).map(
      ({ key, value }) => [key, value],
    ),
    [
      ["contents", "read"],
      ["actions", "read"],
      ["packages", "read"],
    ],
  );
  const deploy = job(document, "deploy");
  assert.match(child(document, deploy, "if").value, /conclusion == 'success'/);
  const revision = requiredStep(document, deploy, "Validate tested revision");
  assert.equal(
    child(document, stepField(document, revision, "env"), "REQUESTED_SHA").value,
    "${{ github.event.workflow_run.head_sha || inputs.deploy_sha }}",
  );
  const validation = stepRun(document, revision);
  assert.match(validation, /test "\$\{#REQUESTED_SHA\}" -eq 40/);
  assert.match(
    validation,
    /actions\/workflows\/backend-quality-gate\.yml\/runs\?head_sha=\$DEPLOY_GIT_SHA/,
  );
  assert.match(validation, /head_branch == "staging"/);
  assert.match(validation, /conclusion == "success"/);
});

test("staging deploy pins every Compose call and gates app changes on the read-only checker", () => {
  const document = parseWorkflow(deploymentWorkflowUrl);
  const deploy = job(document, "deploy");
  const deploySteps = steps(document, deploy);
  const names = deploySteps.map(({ name }) => name);
  const index = (name: string) => {
    const found = names.indexOf(name);
    assert.notEqual(found, -1, `missing deployment step: ${name}`);
    return found;
  };

  assert.ok(index("Pull exact staging images") < index("Start and wait for staging PostgreSQL"));
  assert.ok(index("Start and wait for staging PostgreSQL") < index("Check staging migrations"));
  assert.ok(index("Check staging migrations") < index("Deploy exact staging images"));
  assert.ok(index("Deploy exact staging images") < index("Verify staging"));
  assert.ok(index("Verify staging") < index("Roll back staging images"));
  assert.ok(index("Roll back staging images") < index("Log out of GHCR"));

  const scripts = deploySteps
    .map((step) => {
      const fields = mappingNodes(
        document.lines,
        step.node.indent + 2,
        step.node.start + 1,
        step.node.end,
      );
      const run = fields.find(({ key }) => key === "run");
      return run ? (run.value === "|" ? blockScalar(document, run) : run.value) : "";
    })
    .filter(Boolean);
  const composeCommands = scripts
    .flatMap(logicalShellLines)
    .filter((line) => line.includes("docker compose"));
  assert.equal(composeCommands.length, 7);
  const rollbackComposeCommands = composeCommands.filter((command) =>
    command.includes("API_IMAGE='$PREVIOUS_API_IMAGE'"),
  );
  assert.equal(rollbackComposeCommands.length, 1);
  const targetComposeCommands = composeCommands.filter(
    (command) => !command.includes("API_IMAGE='$PREVIOUS_API_IMAGE'"),
  );
  assert.equal(targetComposeCommands.length, 6);
  for (const command of targetComposeCommands) {
    assert.match(
      command,
      /API_IMAGE='ghcr\.io\/jesse-ux\/jyotisha-api:\$DEPLOY_GIT_SHA'/,
    );
    assert.match(
      command,
      /WEB_IMAGE='ghcr\.io\/jesse-ux\/jyotisha-web:\$DEPLOY_GIT_SHA'/,
    );
  }
  assert.match(rollbackComposeCommands[0], /WEB_IMAGE='\$PREVIOUS_WEB_IMAGE'/);
  assert.match(rollbackComposeCommands[0], /GITHUB_SHA='\$PREVIOUS_SHA'/);
  for (const command of composeCommands) {
    assert.match(command, /ssh /);
    assert.match(command, /APP_ENV_FILE='\.\.\/\.env\.staging'/);
    assert.match(command, /DATABASE_ENV_FILE='\.\.\/\.env\.staging\.database'/);
    assert.match(command, /CADDYFILE_PATH='\.\/Caddyfile\.staging'/);
    assert.match(command, /SITE_ADDRESS='https:\/\/staging\.jyotisha\.chat'/);
    assert.match(command, /--env-file \.env\.staging/);
    assert.match(command, /-f deploy\/docker-compose\.server\.yml/);
    assert.match(command, /-f deploy\/docker-compose\.postgres\.yml/);
  }

  const login = stepRun(document, requiredStep(document, deploy, "Log in to GHCR"));
  assert.match(login, /printf '%s' "\$GHCR_TOKEN" \| ssh /);
  assert.match(login, /docker login ghcr\.io .*--password-stdin/);
  assert.doesNotMatch(login, /--password(?:\s|=)/);

  assert.match(
    stepRun(document, requiredStep(document, deploy, "Pull exact staging images")),
    /pull api web postgres/,
  );
  assert.match(
    stepRun(
      document,
      requiredStep(document, deploy, "Start and wait for staging PostgreSQL"),
    ),
    /up -d --no-build --wait postgres/,
  );

  const check = requiredStep(document, deploy, "Check staging migrations");
  assert.equal(stepField(document, check, "id").value, "migration_check");
  const checkScript = stepRun(document, check);
  assert.match(checkScript, /--profile migration-check run --rm migration-checker/);
  assert.match(checkScript, /"\$CHECK_STATUS" -eq 3/);
  assert.match(checkScript, /Migrate Staging Database/);
  assert.match(checkScript, /\$DEPLOY_GIT_SHA/);
  assert.match(checkScript, /exit 3/);
  assert.match(
    readFileSync(
      new URL("../../deploy/docker-compose.postgres.yml", import.meta.url),
      "utf8",
    ),
    /command: \["npm", "run", "db:migrate:check"\]/,
  );

  const workflow = readFileSync(deploymentWorkflowUrl, "utf8");
  assert.doesNotMatch(workflow, /npm\s+run\s+db:migrate(?!:check)/);
  assert.doesNotMatch(workflow, /run\s+--rm\s+migrator/);
  assert.doesNotMatch(workflow, /--profile\s+migration(?:\s|["'])/);
  assert.doesNotMatch(workflow, /(?:up -d[^\n]*--build|docker compose build)/);

  const applicationDeploy = stepRun(
    document,
    requiredStep(document, deploy, "Deploy exact staging images"),
  );
  assert.match(applicationDeploy, /up -d --no-build --remove-orphans/);
  const previous = requiredStep(document, deploy, "Record previous staging images");
  assert.equal(stepField(document, previous, "id").value, "previous");
  const previousScript = stepRun(document, previous);
  assert.match(previousScript, /docker inspect --format '\{\{\.Config\.Image\}\}'/);
  assert.match(previousScript, /api_image=\$PREVIOUS_API_IMAGE/);
  assert.match(previousScript, /web_image=\$PREVIOUS_WEB_IMAGE/);
  assert.match(previousScript, /previous_sha=\$PREVIOUS_SHA/);
  assert.doesNotMatch(
    previousScript,
    /(?:api_image|web_image|previous_sha)=not-deployed/,
  );
  assert.match(previousScript, /\$\{PREVIOUS_SHA:-not-deployed\}/);

  const rollback = requiredStep(document, deploy, "Roll back staging images");
  assert.equal(
    stepField(document, rollback, "if").value,
    "failure() && steps.migration_check.outcome == 'success' && steps.previous.outputs.api_image != '' && steps.previous.outputs.web_image != '' && steps.previous.outputs.previous_sha != ''",
  );
  const rollbackEnv = stepField(document, rollback, "env");
  assert.equal(
    child(document, rollbackEnv, "PREVIOUS_API_IMAGE").value,
    "${{ steps.previous.outputs.api_image }}",
  );
  assert.equal(
    child(document, rollbackEnv, "PREVIOUS_WEB_IMAGE").value,
    "${{ steps.previous.outputs.web_image }}",
  );
  assert.equal(
    child(document, rollbackEnv, "PREVIOUS_SHA").value,
    "${{ steps.previous.outputs.previous_sha }}",
  );
  assert.match(stepRun(document, rollback), /API_IMAGE='\$PREVIOUS_API_IMAGE'/);
  assert.match(stepRun(document, rollback), /WEB_IMAGE='\$PREVIOUS_WEB_IMAGE'/);
  assert.match(stepRun(document, rollback), /GITHUB_SHA='\$PREVIOUS_SHA'/);
  assert.match(stepRun(document, rollback), /up -d --no-build/);
  assert.doesNotMatch(stepRun(document, rollback), /not-deployed/);

  const logout = requiredStep(document, deploy, "Log out of GHCR");
  assert.equal(stepField(document, logout, "if").value, "always()");
  assert.equal(stepField(document, logout, "continue-on-error").value, "true");
  assert.match(stepRun(document, logout), /docker logout ghcr\.io/);
});

test("pending migration status exits 3 with the manual workflow and exact SHA", () => {
  const document = parseWorkflow(deploymentWorkflowUrl);
  const check = requiredStep(
    document,
    job(document, "deploy"),
    "Check staging migrations",
  );
  const script = stepRun(document, check);
  const root = mkdtempSync(join(tmpdir(), "jyotisha-migration-check-"));
  const fakeBin = join(root, "bin");
  const fakeSsh = join(fakeBin, "ssh");
  const exactSha = "0123456789abcdef0123456789abcdef01234567";
  mkdirSync(fakeBin);
  writeFileSync(fakeSsh, '#!/usr/bin/env bash\nexit "${FAKE_SSH_STATUS:?}"\n');
  chmodSync(fakeSsh, 0o700);

  const run = (status: number) =>
    spawnSync("bash", ["-c", script], {
      encoding: "utf8",
      env: {
        ...process.env,
        DEPLOY_GIT_SHA: exactSha,
        DEPLOY_HOST: "staging.example.invalid",
        DEPLOY_PORT: "22",
        DEPLOY_USER: "deploy",
        DEPLOY_PATH: "/opt/jyotisha-staging",
        FAKE_SSH_STATUS: String(status),
        HOME: root,
        PATH: `${fakeBin}:${process.env.PATH}`,
      },
    });

  try {
    const pending = run(3);
    assert.equal(pending.status, 3, pending.stderr);
    assert.match(`${pending.stdout}\n${pending.stderr}`, /Migrate Staging Database/);
    assert.match(`${pending.stdout}\n${pending.stderr}`, new RegExp(exactSha));
    assert.equal(run(0).status, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("staging migration is manual-only, serialized, and least-privileged", () => {
  const document = parseWorkflow(migrationWorkflowUrl);

  assert.equal(requiredNode(document.root, "name").value, "Migrate Staging Database");
  const triggers = requiredNode(document.root, "on");
  assert.deepEqual(children(document, triggers).map(({ key }) => key), [
    "workflow_dispatch",
  ]);
  const dispatch = child(document, triggers, "workflow_dispatch");
  const inputs = child(document, dispatch, "inputs");
  assert.deepEqual(children(document, inputs).map(({ key }) => key), [
    "deploy_sha",
  ]);
  const deploySha = child(document, inputs, "deploy_sha");
  assert.equal(child(document, deploySha, "required").value, "true");
  assert.equal(child(document, deploySha, "type").value, "string");

  const concurrency = requiredNode(document.root, "concurrency");
  assert.equal(
    child(document, concurrency, "group").value,
    "staging-database-migration",
  );
  assert.equal(child(document, concurrency, "cancel-in-progress").value, "false");
  assert.deepEqual(
    children(document, requiredNode(document.root, "permissions")).map(
      ({ key, value }) => [key, value],
    ),
    [
      ["contents", "read"],
      ["actions", "write"],
      ["packages", "read"],
    ],
  );
  assert.deepEqual(
    children(document, requiredNode(document.root, "jobs")).map(({ key }) => key),
    ["migrate"],
  );

  const migrate = job(document, "migrate");
  assert.equal(child(document, migrate, "environment").value, "staging");
  assert.equal(child(document, migrate, "runs-on").value, "ubuntu-latest");
  assert.equal(child(document, migrate, "timeout-minutes").value, "20");
});

test("staging migration accepts only an exact lowercase SHA with a successful staging gate", () => {
  const document = parseWorkflow(migrationWorkflowUrl);
  const migrate = job(document, "migrate");
  const revision = requiredStep(document, migrate, "Validate tested revision");
  const revisionEnv = stepField(document, revision, "env");
  assert.equal(
    child(document, revisionEnv, "REQUESTED_SHA").value,
    "${{ inputs.deploy_sha }}",
  );
  assert.equal(
    child(document, revisionEnv, "GH_TOKEN").value,
    "${{ github.token }}",
  );
  const validation = stepRun(document, revision);
  assert.match(validation, /\^\[0-9a-f\]\{40\}\$/);
  assert.match(
    validation,
    /actions\/workflows\/backend-quality-gate\.yml\/runs\?head_sha=\$REQUESTED_SHA&branch=staging&event=push&status=success/,
  );
  assert.match(validation, /\.head_sha == \$sha/);
  assert.match(validation, /\.head_branch == "staging"/);
  assert.match(validation, /\.event == "push"/);
  assert.match(validation, /\.conclusion == "success"/);
  assert.equal(
    validation.match(/>> "\$GITHUB_OUTPUT"/g)?.length,
    1,
    "only the validated single-line SHA may reach GITHUB_OUTPUT",
  );

  const checkout = requiredStep(document, migrate, "Checkout tested revision");
  assert.equal(stepField(document, checkout, "uses").value, "actions/checkout@v4");
  assert.equal(
    child(document, stepField(document, checkout, "with"), "ref").value,
    "${{ steps.revision.outputs.deploy_sha }}",
  );
  const verify = requiredStep(document, migrate, "Verify checked-out revision");
  assert.match(stepRun(document, verify), /git rev-parse HEAD/);
  assert.match(stepRun(document, verify), /"\$DEPLOY_SHA"/);
});

test("tested-revision validation fails closed before checkout or migration", () => {
  const document = parseWorkflow(migrationWorkflowUrl);
  const script = stepRun(
    document,
    requiredStep(document, job(document, "migrate"), "Validate tested revision"),
  );
  const root = mkdtempSync(join(tmpdir(), "jyotisha-migration-gate-"));
  const fakeBin = join(root, "bin");
  const fakeCurl = join(fakeBin, "curl");
  const curlLog = join(root, "curl.log");
  const githubOutput = join(root, "github-output");
  const exactSha = "0123456789abcdef0123456789abcdef01234567";
  mkdirSync(fakeBin);
  writeFileSync(
    fakeCurl,
    [
      "#!/usr/bin/env bash",
      'printf \'%s\\n\' "$@" >> "$FAKE_CURL_LOG"',
      'printf \'%s\' "$FAKE_GATE_JSON"',
    ].join("\n"),
  );
  chmodSync(fakeCurl, 0o700);

  const run = (sha: string, gateJson: object) => {
    writeFileSync(curlLog, "");
    writeFileSync(githubOutput, "");
    const result = spawnSync("bash", ["-c", script], {
      encoding: "utf8",
      env: {
        ...process.env,
        FAKE_CURL_LOG: curlLog,
        FAKE_GATE_JSON: JSON.stringify(gateJson),
        GH_TOKEN: "gate-token-fixture",
        GITHUB_API_URL: "https://api.github.test",
        GITHUB_OUTPUT: githubOutput,
        GITHUB_REPOSITORY: "jesse-ux/Jyotisha",
        PATH: `${fakeBin}:${process.env.PATH}`,
        REQUESTED_SHA: sha,
      },
    });
    return {
      calls: readFileSync(curlLog, "utf8"),
      output: readFileSync(githubOutput, "utf8"),
      result,
    };
  };

  try {
    for (const invalidSha of [exactSha.toUpperCase(), exactSha.slice(1), `${exactSha}\n`]) {
      const invalid = run(invalidSha, { workflow_runs: [] });
      assert.notEqual(invalid.result.status, 0);
      assert.equal(invalid.calls, "");
      assert.equal(invalid.output, "");
    }

    const wrongBranch = run(exactSha, {
      workflow_runs: [
        {
          conclusion: "success",
          event: "push",
          head_branch: "main",
          head_sha: exactSha,
        },
      ],
    });
    assert.notEqual(wrongBranch.result.status, 0);
    assert.equal(wrongBranch.output, "");

    const accepted = run(exactSha, {
      workflow_runs: [
        {
          conclusion: "success",
          event: "push",
          head_branch: "staging",
          head_sha: exactSha,
        },
      ],
    });
    assert.equal(accepted.result.status, 0, accepted.result.stderr);
    assert.equal(accepted.output, `deploy_sha=${exactSha}\n`);
    assert.match(accepted.calls, new RegExp(`head_sha=${exactSha}`));
    assert.doesNotMatch(
      `${accepted.result.stdout}\n${accepted.result.stderr}`,
      /gate-token-fixture/,
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("staging migration preserves env files and runs only PostgreSQL plus migrator", () => {
  const document = parseWorkflow(migrationWorkflowUrl);
  const migrate = job(document, "migrate");
  const names = steps(document, migrate).map(({ name }) => name);
  const stepIndex = (name: string) => {
    const index = names.indexOf(name);
    assert.notEqual(index, -1, `missing migration step: ${name}`);
    return index;
  };
  assert.ok(
    stepIndex("Validate staging environment files") <
      stepIndex("Start and wait for staging PostgreSQL"),
  );
  assert.ok(
    stepIndex("Start and wait for staging PostgreSQL") <
      stepIndex("Apply reviewed staging migrations"),
  );
  assert.ok(
    stepIndex("Apply reviewed staging migrations") <
      stepIndex("Print ordered migration ledger"),
  );
  assert.ok(
    stepIndex("Print ordered migration ledger") <
      stepIndex("Dispatch exact-SHA staging deployment"),
  );

  const target = stepRun(
    document,
    requiredStep(document, migrate, "Validate staging target configuration"),
  );
  assert.match(target, /DEPLOY_HOST" = "118\.26\.111\.127/);
  assert.match(target, /DEPLOY_USER" = "deploy/);
  assert.match(target, /DEPLOY_PATH" = "\/opt\/jyotisha-staging/);
  assert.match(target, /test -n "\$STAGING_KNOWN_HOSTS"/);
  const ssh = stepRun(
    document,
    requiredStep(document, migrate, "Configure pinned staging SSH"),
  );
  assert.match(ssh, /STAGING_KNOWN_HOSTS/);
  assert.doesNotMatch(ssh, /ssh-keyscan/);

  const sync = stepRun(
    document,
    requiredStep(document, migrate, "Sync tested staging sources"),
  );
  assert.match(sync, /rsync -az --delete/);
  assert.match(sync, /--exclude='\.env\*'/);
  const validators = stepRun(
    document,
    requiredStep(document, migrate, "Validate staging environment files"),
  );
  assert.match(validators, /validate-staging-env\.sh \.env\.staging/);
  assert.match(
    validators,
    /validate-staging-database-env\.sh \.env\.staging\.database/,
  );

  const migrationSteps = steps(document, migrate);
  const scripts = migrationSteps.map((step) => {
    const run = mappingNodes(
      document.lines,
      step.node.indent + 2,
      step.node.start + 1,
      step.node.end,
    ).find(({ key }) => key === "run");
    return run ? (run.value === "|" ? blockScalar(document, run) : run.value) : "";
  });
  const composeCommands = scripts
    .flatMap(logicalShellLines)
    .filter((line) => line.includes("docker compose"));
  assert.equal(composeCommands.length, 3);
  for (const command of composeCommands) {
    assert.match(command, /-f deploy\/docker-compose\.postgres\.yml/);
    assert.doesNotMatch(command, /docker-compose\.server\.yml/);
    assert.doesNotMatch(command, /\brestart\b/);
  }
  const startCommands = composeCommands.filter((command) => /\sup\s/.test(command));
  assert.equal(startCommands.length, 1);
  assert.match(startCommands[0], /up -d --wait postgres/);
  assert.doesNotMatch(startCommands[0], /\b(?:api|web|caddy)\b/);

  const apply = stepRun(
    document,
    requiredStep(document, migrate, "Apply reviewed staging migrations"),
  );
  assert.match(
    apply,
    /WEB_IMAGE='ghcr\.io\/jesse-ux\/jyotisha-web:\$DEPLOY_SHA'/,
  );
  assert.match(apply, /--profile migration run --rm migrator/);
  const ledger = stepRun(
    document,
    requiredStep(document, migrate, "Print ordered migration ledger"),
  );
  assert.match(ledger, /psql -U postgres -d jyotisha -Atc/);
  assert.match(
    ledger,
    /select filename from migration\.schema_migrations order by filename/,
  );
  assert.doesNotMatch(
    readFileSync(migrationWorkflowUrl, "utf8"),
    /docker-compose\.server\.yml/,
  );
});

test("successful migration dispatches exact-SHA staging deploy and always logs out", () => {
  const document = parseWorkflow(migrationWorkflowUrl);
  const migrate = job(document, "migrate");
  const dispatch = requiredStep(
    document,
    migrate,
    "Dispatch exact-SHA staging deployment",
  );
  const dispatchFields = mappingNodes(
    document.lines,
    dispatch.node.indent + 2,
    dispatch.node.start + 1,
    dispatch.node.end,
  );
  assert.equal(dispatchFields.some(({ key }) => key === "if"), false);
  assert.equal(dispatchFields.some(({ key }) => key === "continue-on-error"), false);
  const script = stepRun(document, dispatch);
  assert.match(
    script,
    /actions\/workflows\/deploy-staging\.yml\/dispatches/,
  );
  assert.match(script, /--data-binary "@\$PAYLOAD_FILE"/);

  const logout = requiredStep(document, migrate, "Log out of GHCR");
  assert.equal(stepField(document, logout, "if").value, "always()");
  assert.equal(stepField(document, logout, "continue-on-error").value, "true");
  assert.match(stepRun(document, logout), /docker logout ghcr\.io/);

  const root = mkdtempSync(join(tmpdir(), "jyotisha-migration-dispatch-"));
  const fakeBin = join(root, "bin");
  const fakeCurl = join(fakeBin, "curl");
  const body = join(root, "body.json");
  const curlLog = join(root, "curl.log");
  const exactSha = "0123456789abcdef0123456789abcdef01234567";
  mkdirSync(fakeBin);
  writeFileSync(
    fakeCurl,
    [
      "#!/usr/bin/env bash",
      'printf \'%s\\n\' "$@" > "$FAKE_CURL_LOG"',
      'for argument in "$@"; do',
      '  case "$argument" in',
      '    @*) cp -- "${argument#@}" "$FAKE_REQUEST_BODY" ;;',
      "  esac",
      "done",
      'exit "${FAKE_CURL_STATUS:-0}"',
    ].join("\n"),
  );
  chmodSync(fakeCurl, 0o700);

  const run = (status: number) =>
    spawnSync("bash", ["-c", script], {
      encoding: "utf8",
      env: {
        ...process.env,
        DEPLOY_SHA: exactSha,
        FAKE_CURL_LOG: curlLog,
        FAKE_CURL_STATUS: String(status),
        FAKE_REQUEST_BODY: body,
        GH_TOKEN: "dispatch-token-fixture",
        GITHUB_API_URL: "https://api.github.test",
        GITHUB_REPOSITORY: "jesse-ux/Jyotisha",
        PATH: `${fakeBin}:${process.env.PATH}`,
      },
    });

  try {
    const accepted = run(0);
    assert.equal(accepted.status, 0, accepted.stderr);
    assert.deepEqual(JSON.parse(readFileSync(body, "utf8")), {
      inputs: { deploy_sha: exactSha },
      ref: "staging",
    });
    assert.match(
      readFileSync(curlLog, "utf8"),
      /actions\/workflows\/deploy-staging\.yml\/dispatches/,
    );
    assert.doesNotMatch(
      `${accepted.stdout}\n${accepted.stderr}`,
      /dispatch-token-fixture/,
    );
    assert.notEqual(run(22).status, 0, "workflow dispatch API failure must fail");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
