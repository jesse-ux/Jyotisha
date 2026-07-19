from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "frontend" / "src" / "app" / "page.tsx"
AGENT = ROOT / "frontend" / "src" / "mastra" / "index.ts"
ONBOARDING_ROUTE = ROOT / "frontend" / "src" / "app" / "api" / "onboarding" / "route.ts"
CONSULT_ROUTE = ROOT / "frontend" / "src" / "app" / "api" / "consult" / "route.ts"
MODELS_ROUTE = ROOT / "frontend" / "src" / "app" / "api" / "models" / "route.ts"
MODEL_SELECTION = ROOT / "frontend" / "src" / "lib" / "consultation-model-selection.ts"
SESSION_MODEL_PERSISTENCE = (
    ROOT / "frontend" / "src" / "lib" / "session-model-persistence.ts"
)
ONBOARDING_MIGRATION = (
    ROOT
    / "frontend"
    / "supabase"
    / "migrations"
    / "20260715040000_agent_onboarding_cache.sql"
)


def test_onboarding_and_agent_suggestion_contract() -> None:
    page = PAGE.read_text(encoding="utf-8")
    agent = AGENT.read_text(encoding="utf-8")
    route = ONBOARDING_ROUTE.read_text(encoding="utf-8")
    consult_route = CONSULT_ROUTE.read_text(encoding="utf-8")
    migration = ONBOARDING_MIGRATION.read_text(encoding="utf-8")

    assert "onboarding-card" in page
    assert 'type OnboardingStep = "name" | "birth" | "place"' in page
    assert "text.slice(0, length)" in page
    assert "window.setInterval" in page
    assert "prefers-reduced-motion: reduce" in page
    assert "用于计算星盘，并安全保存到你的账号" not in page
    assert "saveOnboardingName" in page
    assert "saveOnboardingBirth" in page
    assert "saveOnboardingPlace" in page
    assert "<BirthTimeIntakeFields value={value}" in page
    assert "<BirthLocationFields value={profileDraft}" in page
    assert "Enter 确认称呼" in page
    assert 'fetch("/api/onboarding"' in page
    assert "onboarding?.suggestions" in page
    assert "parseAgentReply(answer, theme)" in page
    assert "suggestions: reply.suggestions" in page
    assert "activeSuggestions.map" in page

    assert "export function getOnboardingAgent" in agent
    assert "skills: [jyotishSkillPath]" in agent
    assert "This is onboarding, not a chart reading" in agent
    assert "<!--AYANAM_SUGGESTIONS:" in agent
    assert "grounded in the answer just given" in agent
    assert "Treat the server-provided current time as authoritative" in agent

    assert "supabase.auth.getUser()" in route
    assert "function currentTimeContext(now = new Date())" in consult_route
    assert "currentTimeContext()," in consult_route
    assert "中国标准时间（UTC+8）" in consult_route
    assert 'profile.onboarding_version === ONBOARDING_VERSION' in route
    assert "getOnboardingAgent(onboardingModel).generate" in route
    assert 'source: "cache"' in route
    assert "onboarding_payload" in migration
    assert "to service_role" in migration
    assert "to authenticated" not in migration


def test_multi_model_route_and_persistence_contract() -> None:
    consult_route = CONSULT_ROUTE.read_text(encoding="utf-8")
    models_route = MODELS_ROUTE.read_text(encoding="utf-8")
    selection = MODEL_SELECTION.read_text(encoding="utf-8")
    persistence = SESSION_MODEL_PERSISTENCE.read_text(encoding="utf-8")

    assert "supabase.auth.getUser()" in models_route
    assert "publicLanguageModelCatalog()" in models_route
    assert "reserveConsultationModel(" in consult_route
    assert "resolveLanguageModel," in consult_route
    assert 'runCreditRpc(accounting, "begin_consultation_credit"' in consult_route
    assert "getJyotishAgent(selectedModel).stream" in consult_route
    assert "modelSelection.usageModelId" in consult_route
    assert 'if (!model) return { status: "unavailable" }' in selection
    assert 'reservation: await reserveCredit()' in selection
    assert 'values: { model_id: modelId }' in persistence
    assert "SessionModelPersistenceQueue" in persistence
