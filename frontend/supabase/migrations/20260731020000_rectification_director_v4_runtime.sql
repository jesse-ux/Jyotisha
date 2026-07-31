-- New and unfinished Agent cases use the adaptive Director loop contract.
alter table public.birth_time_rectification_v4_cases
  alter column skill_version set default 'birth-time-rectification-v8',
  alter column prompt_version set default 'rectification-director-v4';

-- The scoring and evidence contracts are unchanged, so unfinished cases can continue safely.
update public.birth_time_rectification_v4_cases
set skill_version = 'birth-time-rectification-v8',
    prompt_version = 'rectification-director-v4',
    updated_at = greatest(updated_at, pg_catalog.now())
where status in ('awaiting_answer', 'processing', 'paused')
  and deployment_mode in ('v5_shadow', 'v5_agent')
  and (skill_version is distinct from 'birth-time-rectification-v8'
    or prompt_version is distinct from 'rectification-director-v4');
