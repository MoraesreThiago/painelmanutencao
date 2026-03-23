import {
  getCorsHeaders,
  jsonOk,
  jsonError,
  parseAuthHeader,
  parseBody,
  getCallerUser,
  assertAdmin,
  getAdminClient,
  assertUuid,
  isKnownError,
  PayloadError,
} from "../_shared/helpers.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

Deno.serve(async (req) => {
  const cors = getCorsHeaders(req);
  if (req.method === "OPTIONS") return new Response(null, { headers: cors });

  const tag = "[delete-user]";

  try {
    // 1. Auth
    const authHeader = parseAuthHeader(req);
    if (!authHeader) return jsonError("Não autorizado", 401, cors);

    const { caller, callerClient } = await getCallerUser(authHeader);
    await assertAdmin(callerClient, caller.id);
    console.info(`${tag} Admin ${caller.id} iniciou exclusão de usuário`);

    // 2. Parse & validate payload
    const body = await parseBody(req);
    const userId = assertUuid(body.user_id, "ID do usuário");

    if (userId === caller.id) {
      throw new PayloadError("Você não pode excluir sua própria conta");
    }

    // 3. Delete — order: auth first, then profile/roles
    //    Rationale: if auth delete succeeds the user can no longer log in,
    //    so leftover profile/role rows are harmless orphans.
    //    If auth delete fails we abort without touching other tables.
    const adminClient = getAdminClient();

    const { error: authDeleteError } = await adminClient.auth.admin.deleteUser(userId);
    if (authDeleteError) {
      console.error(`${tag} Auth delete failed for ${userId}:`, authDeleteError.message);
      return jsonError("Erro ao excluir usuário. Tente novamente.", 400, cors);
    }
    console.info(`${tag} Auth user deleted: ${userId}`);

    // 4. Clean up profile and roles (best-effort; FK cascades may also handle this)
    const { error: profileErr } = await adminClient.from("profiles").delete().eq("id", userId);
    if (profileErr) console.warn(`${tag} Profile cleanup failed for ${userId}:`, profileErr.message);

    const { error: roleErr } = await adminClient.from("user_roles").delete().eq("user_id", userId);
    if (roleErr) console.warn(`${tag} Role cleanup failed for ${userId}:`, roleErr.message);

    console.info(`${tag} User ${userId} fully deleted`);
    return jsonOk({ success: true }, cors);
  } catch (err) {
    if (isKnownError(err)) return jsonError(err.message, err.status, cors);
    console.error(`${tag} Unhandled:`, (err as Error).message);
    return jsonError("Erro interno do servidor", 500, cors);
  }
});
