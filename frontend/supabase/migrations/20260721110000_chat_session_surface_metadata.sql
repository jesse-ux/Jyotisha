begin;

alter table public.chat_sessions
  add column if not exists session_type text not null default 'consultation'
    check (session_type in ('consultation', 'birth_time_rectification')),
  add column if not exists rectification_case_id uuid
    references public.birth_time_rectification_cases(id) on delete set null;

grant insert (session_type, rectification_case_id)
  on table public.chat_sessions to authenticated;
grant update (session_type, rectification_case_id)
  on table public.chat_sessions to authenticated;

create index if not exists chat_sessions_rectification_case_idx
  on public.chat_sessions (user_id, rectification_case_id)
  where rectification_case_id is not null;

commit;
