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
  assertNonEmptyString,
  isKnownError,
  PayloadError,
  VALID_PERFIS,
  VALID_AREAS,
} from "../_shared/helpers.ts";


Deno.serve(async (req) => {
  const cors = getCorsHeaders(req);
  if (req.method === "OPTIONS") return new Response(null, { headers: cors });
  if (isOriginBlocked(req)) return jsonError("Origem não permitida", 403, cors);

  const tag = "[create-user]";

  try {
    // 1. Auth
    const authHeader = parseAuthHeader(req);
    if (!authHeader) return jsonError("Não autorizado", 401, cors);

    const { caller, callerClient } = await getCallerUser(authHeader);
    await assertAdmin(callerClient, caller.id);
    console.info(`${tag} Admin ${caller.id} iniciou criação de usuário`);

    // 2. Parse & validate payload
    const body = await parseBody(req);
    const email = assertNonEmptyString(body.email, "Email");
    const password = assertNonEmptyString(body.password, "Senha");
    const nome = assertNonEmptyString(body.nome, "Nome");
    const perfil = assertNonEmptyString(body.perfil, "Perfil");
    const area = assertNonEmptyString(body.area, "Área");

    if (password.length < 6) throw new PayloadError("A senha deve ter pelo menos 6 caracteres");
    if (!(VALID_PERFIS as readonly string[]).includes(perfil)) throw new PayloadError("Perfil inválido");
    if (!(VALID_AREAS as readonly string[]).includes(area)) throw new PayloadError("Área inválida");

    // 3. Create auth user
    const adminClient = getAdminClient();

    const { data: newUser, error: createError } = await adminClient.auth.admin.createUser({
      email,
      password,
      email_confirm: true,
    });

    if (createError || !newUser?.user) {
      console.error(`${tag} Auth create failed:`, createError?.message);
      return jsonError("Erro ao criar usuário. Verifique os dados e tente novamente.", 400, cors);
    }

    const userId = newUser.user.id;
    console.info(`${tag} Auth user created: ${userId}`);

    // 4. Create profile (with rollback on failure)
    const { error: profileError } = await adminClient.from("profiles").upsert({
      id: userId,
      email,
      nome,
      perfil,
      area,
    });

    if (profileError) {
      console.error(`${tag} Profile upsert failed, rolling back auth user ${userId}:`, profileError.message);
      await adminClient.auth.admin.deleteUser(userId);
      return jsonError("Erro ao criar perfil do usuário. Operação revertida.", 500, cors);
    }

    // 5. Create role (with rollback on failure)
    const { error: roleError } = await adminClient.from("user_roles").upsert({
      user_id: userId,
      role: perfil,
    });

    if (roleError) {
      console.error(`${tag} Role upsert failed, rolling back auth+profile for ${userId}:`, roleError.message);
      await adminClient.from("profiles").delete().eq("id", userId);
      await adminClient.auth.admin.deleteUser(userId);
      return jsonError("Erro ao atribuir perfil do usuário. Operação revertida.", 500, cors);
    }

    console.info(`${tag} User ${userId} created successfully with profile=${perfil}, area=${area}`);
    return jsonOk({ success: true, user_id: userId }, cors);
  } catch (err) {
    if (isKnownError(err)) return jsonError(err.message, err.status, cors);
    console.error(`${tag} Unhandled:`, (err as Error).message);
    return jsonError("Erro interno do servidor", 500, cors);
  }
});
