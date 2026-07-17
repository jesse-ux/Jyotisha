begin;

alter table public.chat_sessions
  add column if not exists model_id text;

grant insert (model_id)
  on table public.chat_sessions to authenticated;
grant update (model_id)
  on table public.chat_sessions to authenticated;

commit;
