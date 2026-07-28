#!/usr/bin/env bash
set -euo pipefail
set +x

required=(DEPLOY_PATH EXPECTED_DEPLOY_SHA RESET_EMAIL RESET_CONFIRMATION)
for key in "${required[@]}"; do
  if [ -z "${!key:-}" ]; then
    echo "required staging account-reset input is missing: $key" >&2
    exit 1
  fi
done

[[ "$EXPECTED_DEPLOY_SHA" =~ ^[0-9a-f]{40}$ ]] || {
  echo "invalid expected deployment SHA" >&2
  exit 1
}
[[ "$RESET_EMAIL" =~ ^[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,63}$ ]] || {
  echo "invalid reset email" >&2
  exit 1
}
[ "$RESET_CONFIRMATION" = "RESET $RESET_EMAIL" ] || {
  echo "account reset confirmation does not match" >&2
  exit 1
}
[ "$DEPLOY_PATH" = "/opt/jyotisha-staging" ] || {
  echo "refusing non-staging deployment path" >&2
  exit 1
}

state_directory="$DEPLOY_PATH/.state"
[ -f "$state_directory/deployed-revision" ] || {
  echo "staging deployed revision is unavailable" >&2
  exit 1
}
[ "$(<"$state_directory/deployed-revision")" = "$EXPECTED_DEPLOY_SHA" ] || {
  echo "deployed staging revision does not match the approved reset SHA" >&2
  exit 1
}

install -d -m 700 "$state_directory"
exec 9>"$state_directory/mutation.lock"
flock -n 9 || {
  echo "another staging mutation holds the host lock" >&2
  exit 75
}

cd "$DEPLOY_PATH"
compose=(docker compose -p jyotisha-staging -f deploy/docker-compose.postgres.yml)
"${compose[@]}" ps --status running postgres --quiet | grep -q . || {
  echo "staging postgres container is not running" >&2
  exit 1
}

run_psql() {
  "${compose[@]}" exec -T -e RESET_EMAIL="$RESET_EMAIL" postgres sh -ceu '
    exec psql -X -v ON_ERROR_STOP=1 -v target_email="$RESET_EMAIL" \
      -U "$POSTGRES_USER" -d "$POSTGRES_DB"
  '
}

run_psql <<'SQL'
begin;

create temporary table reset_snapshot on commit drop as
select
  identity_user.id,
  identity_user.email,
  profile.email as profile_email,
  profile.credits,
  (select count(*) from identity.accounts value where value.user_id = identity_user.id) as identity_accounts,
  (select count(*) from identity.sessions value where value.user_id = identity_user.id) as identity_sessions,
  (select count(*) from public.credit_transactions value where value.user_id = identity_user.id) as credit_transactions,
  (select count(*) from public.credit_request_cancellations value where value.user_id = identity_user.id) as credit_cancellations,
  (select count(*) from public.consultation_requests value where value.user_id = identity_user.id) as consultation_requests,
  (select count(*) from public.birth_time_rectification_billing value where value.user_id = identity_user.id) as rectification_billing,
  (select count(*) from public.birth_time_rectification_action_receipts value where value.user_id = identity_user.id) as action_receipts,
  (select count(*) from public.redemption_codes value where value.redeemed_by = identity_user.id) as redeemed_codes,
  (select count(*) from audit.admin_audit_logs value where value.actor_user_id = identity_user.id) as admin_audit_logs
from identity.users identity_user
join auth.users auth_user on auth_user.id = identity_user.id
join public.profiles profile on profile.id = identity_user.id
where lower(btrim(identity_user.email)) = lower(btrim(:'target_email'))
  and lower(btrim(auth_user.email)) = lower(btrim(:'target_email'))
for update of identity_user, auth_user, profile;

do $$
begin
  if (select count(*) from reset_snapshot) <> 1 then
    raise exception 'account_not_found_or_identity_bridge_mismatch';
  end if;
end $$;

select jsonb_build_object(
  'stage', 'preflight',
  'email', snapshot.email,
  'credits', snapshot.credits,
  'identityAccounts', snapshot.identity_accounts,
  'identitySessions', snapshot.identity_sessions,
  'creditTransactions', snapshot.credit_transactions,
  'creditCancellations', snapshot.credit_cancellations,
  'consultationRequests', snapshot.consultation_requests,
  'rectificationBilling', snapshot.rectification_billing,
  'actionReceipts', snapshot.action_receipts,
  'redeemedCodes', snapshot.redeemed_codes,
  'adminAuditLogs', snapshot.admin_audit_logs,
  'chatSessions', (select count(*) from public.chat_sessions value where value.user_id = snapshot.id),
  'chartProfiles', (select count(*) from public.chart_profiles value where value.user_id = snapshot.id),
  'synastryReports', (select count(*) from public.synastry_reports value where value.user_id = snapshot.id),
  'legacyRectificationCases', (select count(*) from public.birth_time_rectification_cases value where value.user_id = snapshot.id),
  'v5RectificationCases', (select count(*) from public.birth_time_rectification_v4_cases value where value.user_id = snapshot.id),
  'v5AgentRuns', (select count(*) from public.birth_time_rectification_agent_runs value where value.user_id = snapshot.id),
  'v5Diagnostics', (select count(*) from public.birth_time_rectification_diagnostics value where value.user_id = snapshot.id),
  'v5Jobs', (select count(*) from public.birth_time_rectification_v4_jobs value where value.user_id = snapshot.id)
)
from reset_snapshot snapshot;

update public.profiles profile
set name = null,
    birth_date = null,
    birth_time = null,
    country_code = null,
    province_code = null,
    city_code = null,
    district_code = null,
    onboarding_payload = null,
    onboarding_version = null,
    onboarding_generated_at = null,
    latitude = null,
    longitude = null,
    timezone_offset = null,
    reported_birth_time = null,
    active_birth_time = null,
    birth_time_source = null,
    birth_time_period = null,
    birth_time_clue = null,
    uncertainty_before_minutes = null,
    uncertainty_after_minutes = null,
    birth_time_status = null,
    rectification_confidence = null,
    rectification_case_id = null,
    birth_place_label = null,
    birth_place_type = null,
    birth_place_provider = null,
    birth_place_provider_id = null,
    timezone_id = null,
    timezone_source = null,
    updated_at = pg_catalog.now()
from reset_snapshot snapshot
where profile.id = snapshot.id;

delete from public.chat_sessions value using reset_snapshot snapshot where value.user_id = snapshot.id;
delete from public.chart_profiles value using reset_snapshot snapshot where value.user_id = snapshot.id;
delete from public.synastry_reports value using reset_snapshot snapshot where value.user_id = snapshot.id;
delete from public.birth_time_rectification_v4_cases value using reset_snapshot snapshot where value.user_id = snapshot.id;
delete from public.birth_time_rectification_cases value using reset_snapshot snapshot where value.user_id = snapshot.id;

do $$
begin
  if exists (
    select 1
    from reset_snapshot snapshot
    join identity.users identity_user on identity_user.id = snapshot.id
    join auth.users auth_user on auth_user.id = snapshot.id
    join public.profiles profile on profile.id = snapshot.id
    where identity_user.email is distinct from snapshot.email
       or auth_user.email is distinct from snapshot.email
       or profile.email is distinct from snapshot.profile_email
       or profile.credits is distinct from snapshot.credits
       or (select count(*) from identity.accounts value where value.user_id = snapshot.id) <> snapshot.identity_accounts
       or (select count(*) from identity.sessions value where value.user_id = snapshot.id) <> snapshot.identity_sessions
       or (select count(*) from public.credit_transactions value where value.user_id = snapshot.id) <> snapshot.credit_transactions
       or (select count(*) from public.credit_request_cancellations value where value.user_id = snapshot.id) <> snapshot.credit_cancellations
       or (select count(*) from public.consultation_requests value where value.user_id = snapshot.id) <> snapshot.consultation_requests
       or (select count(*) from public.birth_time_rectification_billing value where value.user_id = snapshot.id) <> snapshot.rectification_billing
       or (select count(*) from public.birth_time_rectification_action_receipts value where value.user_id = snapshot.id) <> snapshot.action_receipts
       or (select count(*) from public.redemption_codes value where value.redeemed_by = snapshot.id) <> snapshot.redeemed_codes
       or (select count(*) from audit.admin_audit_logs value where value.actor_user_id = snapshot.id) <> snapshot.admin_audit_logs
  ) then
    raise exception 'preserved_state_changed';
  end if;

  if exists (select 1 from public.chat_sessions value join reset_snapshot snapshot on value.user_id = snapshot.id)
     or exists (select 1 from public.chart_profiles value join reset_snapshot snapshot on value.user_id = snapshot.id)
     or exists (select 1 from public.synastry_reports value join reset_snapshot snapshot on value.user_id = snapshot.id)
     or exists (select 1 from public.birth_time_rectification_cases value join reset_snapshot snapshot on value.user_id = snapshot.id)
     or exists (select 1 from public.birth_time_rectification_v4_cases value join reset_snapshot snapshot on value.user_id = snapshot.id)
     or exists (select 1 from public.birth_time_rectification_v4_jobs value join reset_snapshot snapshot on value.user_id = snapshot.id)
     or exists (select 1 from public.birth_time_rectification_agent_runs value join reset_snapshot snapshot on value.user_id = snapshot.id)
     or exists (select 1 from public.birth_time_rectification_diagnostics value join reset_snapshot snapshot on value.user_id = snapshot.id)
     or exists (select 1 from public.birth_time_rectification_candidate_feature_snapshots value join reset_snapshot snapshot on value.user_id = snapshot.id)
     or exists (select 1 from public.birth_time_rectification_public_messages value join reset_snapshot snapshot on value.user_id = snapshot.id)
     or exists (select 1 from public.birth_time_rectification_pending_evidence value join reset_snapshot snapshot on value.user_id = snapshot.id)
     or exists (
       select 1 from public.profiles profile join reset_snapshot snapshot on profile.id = snapshot.id
       where profile.name is not null or profile.birth_date is not null or profile.birth_time is not null
          or profile.country_code is not null or profile.province_code is not null or profile.city_code is not null or profile.district_code is not null
          or profile.onboarding_payload is not null or profile.onboarding_version is not null or profile.onboarding_generated_at is not null
          or profile.latitude is not null or profile.longitude is not null or profile.timezone_offset is not null
          or profile.reported_birth_time is not null or profile.active_birth_time is not null or profile.birth_time_source is not null
          or profile.birth_time_period is not null or profile.birth_time_clue is not null
          or profile.uncertainty_before_minutes is not null or profile.uncertainty_after_minutes is not null
          or profile.birth_time_status is not null or profile.rectification_confidence is not null or profile.rectification_case_id is not null
          or profile.birth_place_label is not null or profile.birth_place_type is not null or profile.birth_place_provider is not null
          or profile.birth_place_provider_id is not null or profile.timezone_id is not null or profile.timezone_source is not null
     ) then
    raise exception 'reset_state_not_empty';
  end if;
end $$;

commit;
SQL

run_psql <<'SQL'
begin;

create temporary table postflight_target on commit drop as
select identity_user.id, identity_user.email, profile.credits,
  not (
    profile.name is null and profile.birth_date is null and profile.birth_time is null
    and profile.country_code is null and profile.province_code is null and profile.city_code is null and profile.district_code is null
    and profile.onboarding_payload is null and profile.onboarding_version is null and profile.onboarding_generated_at is null
    and profile.latitude is null and profile.longitude is null and profile.timezone_offset is null
    and profile.reported_birth_time is null and profile.active_birth_time is null and profile.birth_time_source is null
    and profile.birth_time_period is null and profile.birth_time_clue is null
    and profile.uncertainty_before_minutes is null and profile.uncertainty_after_minutes is null
    and profile.birth_time_status is null and profile.rectification_confidence is null and profile.rectification_case_id is null
    and profile.birth_place_label is null and profile.birth_place_type is null and profile.birth_place_provider is null
    and profile.birth_place_provider_id is null and profile.timezone_id is null and profile.timezone_source is null
  ) as profile_not_reset,
  lower(btrim(profile.email)) = lower(btrim(identity_user.email)) as profile_email_matches
from identity.users identity_user
join auth.users auth_user on auth_user.id = identity_user.id
  and lower(btrim(auth_user.email)) = lower(btrim(identity_user.email))
join public.profiles profile on profile.id = identity_user.id
where lower(btrim(identity_user.email)) = lower(btrim(:'target_email'));

do $$
declare
  target_id uuid;
begin
  if (select count(*) from postflight_target) <> 1 then
    raise exception 'postflight_account_not_found_or_identity_bridge_mismatch';
  end if;
  select id into target_id from postflight_target;

  if exists (select 1 from public.chat_sessions value where value.user_id = target_id)
     or exists (select 1 from public.chart_profiles value where value.user_id = target_id)
     or exists (select 1 from public.synastry_reports value where value.user_id = target_id)
     or exists (select 1 from public.birth_time_rectification_cases value where value.user_id = target_id)
     or exists (select 1 from public.birth_time_rectification_v4_cases value where value.user_id = target_id)
     or exists (select 1 from public.birth_time_rectification_v4_jobs value where value.user_id = target_id)
     or exists (select 1 from public.birth_time_rectification_agent_runs value where value.user_id = target_id)
     or exists (select 1 from public.birth_time_rectification_diagnostics value where value.user_id = target_id)
     or exists (select 1 from public.birth_time_rectification_candidate_feature_snapshots value where value.user_id = target_id)
     or exists (select 1 from public.birth_time_rectification_public_messages value where value.user_id = target_id)
     or exists (select 1 from public.birth_time_rectification_pending_evidence value where value.user_id = target_id)
     or exists (select 1 from postflight_target where profile_not_reset) then
    raise exception 'postflight_reset_state_not_empty';
  end if;
end $$;

select jsonb_build_object(
  'stage', 'postflight',
  'matchedAccounts', (select count(*) from postflight_target),
  'email', (select email from postflight_target),
  'credits', (select credits from postflight_target),
  'profileEmailMatches', (select profile_email_matches from postflight_target),
  'profileNotReset', (select profile_not_reset from postflight_target),
  'chatSessions', (select count(*) from public.chat_sessions value where value.user_id = (select id from postflight_target)),
  'chartProfiles', (select count(*) from public.chart_profiles value where value.user_id = (select id from postflight_target)),
  'synastryReports', (select count(*) from public.synastry_reports value where value.user_id = (select id from postflight_target)),
  'legacyRectificationCases', (select count(*) from public.birth_time_rectification_cases value where value.user_id = (select id from postflight_target)),
  'v5RectificationCases', (select count(*) from public.birth_time_rectification_v4_cases value where value.user_id = (select id from postflight_target)),
  'v5Jobs', (select count(*) from public.birth_time_rectification_v4_jobs value where value.user_id = (select id from postflight_target)),
  'v5AgentRuns', (select count(*) from public.birth_time_rectification_agent_runs value where value.user_id = (select id from postflight_target)),
  'v5Diagnostics', (select count(*) from public.birth_time_rectification_diagnostics value where value.user_id = (select id from postflight_target)),
  'v5FeatureSnapshots', (select count(*) from public.birth_time_rectification_candidate_feature_snapshots value where value.user_id = (select id from postflight_target)),
  'v5PublicMessages', (select count(*) from public.birth_time_rectification_public_messages value where value.user_id = (select id from postflight_target)),
  'v5PendingEvidence', (select count(*) from public.birth_time_rectification_pending_evidence value where value.user_id = (select id from postflight_target)),
  'identityAccounts', (select count(*) from identity.accounts value where value.user_id = (select id from postflight_target)),
  'identitySessions', (select count(*) from identity.sessions value where value.user_id = (select id from postflight_target)),
  'creditTransactions', (select count(*) from public.credit_transactions value where value.user_id = (select id from postflight_target)),
  'creditCancellations', (select count(*) from public.credit_request_cancellations value where value.user_id = (select id from postflight_target)),
  'consultationRequests', (select count(*) from public.consultation_requests value where value.user_id = (select id from postflight_target)),
  'rectificationBilling', (select count(*) from public.birth_time_rectification_billing value where value.user_id = (select id from postflight_target)),
  'actionReceipts', (select count(*) from public.birth_time_rectification_action_receipts value where value.user_id = (select id from postflight_target))
);

commit;
SQL
