-- New cases use the semantic-question V6 prompt contract by default.
alter table public.birth_time_rectification_v4_cases
  alter column skill_version set default 'birth-time-rectification-v6',
  alter column prompt_version set default 'rectification-agent-v6-1';

-- Advance only unfinished rectification cases to the semantic-question V6 prompt contract.
-- Historical completed, abandoned, range-ready, and audit artifacts remain immutable.
update public.birth_time_rectification_v4_cases
set skill_version = 'birth-time-rectification-v6',
    prompt_version = 'rectification-agent-v6-1',
    updated_at = greatest(updated_at, now())
where status in ('awaiting_answer', 'processing', 'paused')
  and (skill_version is distinct from 'birth-time-rectification-v6'
    or prompt_version is distinct from 'rectification-agent-v6-1');
