import {
  getCorsHeaders,
  isOriginBlocked,
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


Deno.serve(async (req) => {
  const cors = getCorsHeaders(req);
  if (req.method === "OPTIONS") return new Response(null, { headers: cors });
  if (isOriginBlocked(req)) return jsonError("Origem não permitida", 403, cors);

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

    // 3. Delete via Auth admin API.
    //    The auth.users table has ON DELETE CASCADE for profiles (via trigger/FK
    //    on profiles.id → auth.users.id) and user_roles (user_id → auth.users.id).
    //    Therefore deleting the auth user automatically removes profile and role rows.
    //    The explicit cleanup below is a safety net for edge cases where cascades
    //    may not be configured or have been altered.
    const adminClient = getAdminClient();

    const { error: authDeleteError } = await adminClient.auth.admin.deleteUser(userId);
    if (authDeleteError) {
      console.error(`${tag} Auth delete failed for ${userId}:`, authDeleteError.message);
      return jsonError("Erro ao excluir usuário. Tente novamente.", 400, cors);
    }
    console.info(`${tag} Auth user deleted: ${userId}`);

    // 4. Best-effort cleanup (safety net — cascades should already handle this)
    const { error: profileErr } = await adminClient.from("profiles").delete().eq("id", userId);
    if (profileErr) console.warn(`${tag} Profile cleanup (may already be cascaded): ${profileErr.message}`);

    const { error: roleErr } = await adminClient.from("user_roles").delete().eq("user_id", userId);
    if (roleErr) console.warn(`${tag} Role cleanup (may already be cascaded): ${roleErr.message}`);

    console.info(`${tag} User ${userId} fully deleted`);
    return jsonOk({ success: true }, cors);
  } catch (err) {
    if (isKnownError(err)) return jsonError(err.message, err.status, cors);
    console.error(`${tag} Unhandled:`, (err as Error).message);
    return jsonError("Erro interno do servidor", 500, cors);
  }
});
