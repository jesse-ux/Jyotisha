import "server-only";

import { createAdminSupabaseClient } from "@/lib/supabase/admin";
import type { IdentityUser } from "@/modules/identity/contracts";
import type { AdminRole } from "./auth";

export type RedemptionCodeRecord = {
  id: string;
  mask: string;
  credits: number;
  expiresAt: string | null;
  note: string | null;
  createdAt: string;
  redeemedBy: string | null;
  redeemedEmail: string | null;
  redeemedAt: string | null;
  revokedBy: string | null;
  revokedAt: string | null;
  status: "available" | "expired" | "redeemed" | "revoked";
};

type RpcCodeRow = {
  id: string;
  code_mask: string;
  credits: number;
  expires_at: string | null;
  note: string | null;
  created_at: string;
  redeemed_by: string | null;
  redeemed_email: string | null;
  redeemed_at: string | null;
  revoked_by: string | null;
  revoked_at: string | null;
};

export function codeStatus(row: RpcCodeRow): RedemptionCodeRecord["status"] {
  if (row.redeemed_at) return "redeemed";
  if (row.revoked_at) return "revoked";
  if (row.expires_at && Date.parse(row.expires_at) <= Date.now()) return "expired";
  return "available";
}

export function mapCode(row: RpcCodeRow): RedemptionCodeRecord {
  return {
    id: row.id,
    mask: row.code_mask,
    credits: row.credits,
    expiresAt: row.expires_at,
    note: row.note,
    createdAt: row.created_at,
    redeemedBy: row.redeemed_by,
    redeemedEmail: row.redeemed_email,
    redeemedAt: row.redeemed_at,
    revokedBy: row.revoked_by,
    revokedAt: row.revoked_at,
    status: codeStatus(row),
  };
}

export async function runCodeRpc(
  functionName:
    | "admin_create_redemption_codes"
    | "admin_update_redemption_code"
    | "admin_revoke_redemption_code",
  session: { user: IdentityUser; role: AdminRole },
  id: string,
  args: Record<string, unknown>,
): Promise<RedemptionCodeRecord[]> {
  const admin = createAdminSupabaseClient();
  const { data, error } = await admin.rpc(functionName, {
    p_actor_user_id: session.user.id,
    p_actor_email: session.user.email,
    p_actor_role: session.role,
    p_request_id: id,
    ...args,
  });
  if (error) throw new Error(error.message);
  return ((data ?? []) as RpcCodeRow[]).map(mapCode);
}
