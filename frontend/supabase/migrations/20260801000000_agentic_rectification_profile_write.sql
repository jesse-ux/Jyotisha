-- Agentic birth-time rectification profile write-back.
--
-- The agentic rectification flow lets an LLM drive the full local Jyotish
-- methodology on the web. Unlike v4 (which deliberately never touches the
-- profile), this flow may persist a confirmed birth minute. The write is
-- deliberately narrow and service-role-only:
--   * The server layer re-validates against the engine's high-rigor
--     confirmation gate before calling this RPC, so the LLM can never
--     persist an arbitrary or invented minute.
--   * `p_baseline_time` guards against clobbering a concurrent rectification
--     or manual edit (the write only succeeds if the current active time
--     still equals the baseline the server observed at session start).
--   * Only a whole minute (second = 0) is accepted.

begin;

create or replace function public.apply_agentic_rectification_birth_time(
  p_user_id uuid,
  p_time time without time zone,
  p_baseline_time time without time zone default null,
  p_source text default 'agentic-rectification'
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_response jsonb;
begin
  if p_user_id is null or p_time is null
    or extract(second from p_time) is distinct from 0
    or nullif(p_source, '') is null
    or p_source not in ('agentic-rectification', 'agentic-rectification-admin') then
    raise exception 'agentic_rectification_invalid_input' using errcode = 'P0001';
  end if;

  update public.profiles
  set active_birth_time = p_time,
      birth_time = p_time,
      birth_time_status = 'confirmed',
      updated_at = pg_catalog.now()
  where id = p_user_id
    and (p_baseline_time is null
      or active_birth_time is not distinct from p_baseline_time);

  if not found then
    raise exception 'agentic_rectification_baseline_changed' using errcode = 'P0001';
  end if;

  v_response := jsonb_build_object(
    'success', true,
    'saved_time', pg_catalog.to_char(p_time, 'HH24:MI'),
    'source', p_source,
    'updated_at', pg_catalog.now()
  );
  return v_response;
end;
$$;

revoke all on function public.apply_agentic_rectification_birth_time(uuid, time without time zone, time without time zone, text)
  from public, anon, authenticated;
grant execute on function public.apply_agentic_rectification_birth_time(uuid, time without time zone, time without time zone, text)
  to service_role;

commit;
