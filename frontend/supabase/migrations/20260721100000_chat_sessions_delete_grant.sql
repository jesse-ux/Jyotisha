begin;

drop policy if exists chat_sessions_delete_own on public.chat_sessions;
create policy chat_sessions_delete_own
  on public.chat_sessions
  for delete
  to authenticated
  using ((select auth.uid()) = user_id);

grant delete on table public.chat_sessions to authenticated;

commit;
