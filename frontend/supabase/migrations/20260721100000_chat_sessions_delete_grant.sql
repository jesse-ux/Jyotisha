begin;

grant delete on table public.chat_sessions to authenticated;

commit;
