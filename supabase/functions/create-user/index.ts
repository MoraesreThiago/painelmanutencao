import { createClient } from "@supabase/supabase-js";

const ALLOWED_ORIGINS = Deno.env.get("ALLOWED_ORIGINS")
  ?.split(",")
  .map((o) => o.trim())
  .filter(Boolean) ?? [];

function getCorsHeaders(req: Request) {
  const origin = req.headers.get("Origin") ?? "";
  const allowed =
    ALLOWED_ORIGINS.length === 0 ||
    ALLOWED_ORIGINS.includes(origin);
  return {
    "Access-Control-Allow-Origin": allowed ? origin : ALLOWED_ORIGINS[0] ?? "",
    "Access-Control-Allow-Headers":
      "authorization, x-client-info, apikey, content-type, x-supabase-client-platform, x-supabase-client-platform-version, x-supabase-client-runtime, x-supabase-client-runtime-version",
    "Vary": "Origin",
  };
}

function jsonResponse(body: Record<string, unknown>, status: number, cors: Record<string, string>) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

Deno.serve(async (req) => {
  const cors = getCorsHeaders(req);

  if (req.method === "OPTIONS") {
    return new Response(null, { headers: cors });
  }

  try {
    const authHeader = req.headers.get("Authorization");
    if (!authHeader?.startsWith("Bearer ")) {
      return jsonResponse({ error: "Não autorizado" }, 401, cors);
    }

    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY")!;
    const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

    const callerClient = createClient(supabaseUrl, supabaseAnonKey, {
      global: { headers: { Authorization: authHeader } },
    });

    const {
      data: { user: caller },
    } = await callerClient.auth.getUser();
    if (!caller) {
      return jsonResponse({ error: "Não autorizado" }, 401, cors);
    }

    // Verify caller is admin
    const { data: roleData } = await callerClient
      .from("user_roles")
      .select("role")
      .eq("user_id", caller.id)
      .eq("role", "administrador")
      .maybeSingle();

    if (!roleData) {
      return jsonResponse({ error: "Apenas administradores podem criar usuários" }, 403, cors);
    }

    // --- Payload validation ---
    let body: unknown;
    try {
      body = await req.json();
    } catch {
      return jsonResponse({ error: "Payload JSON inválido" }, 400, cors);
    }

    const { email, password, nome, perfil, area } = body as Record<string, unknown>;

    if (
      typeof email !== "string" || !email.trim() ||
      typeof password !== "string" || !password.trim() ||
      typeof nome !== "string" || !nome.trim() ||
      typeof perfil !== "string" || !perfil.trim() ||
      typeof area !== "string" || !area.trim()
    ) {
      return jsonResponse({ error: "Todos os campos são obrigatórios" }, 400, cors);
    }

    if (password.length < 6) {
      return jsonResponse({ error: "A senha deve ter pelo menos 6 caracteres" }, 400, cors);
    }

    // Validate perfil — admin cannot be created via this function
    const validPerfis = [
      "manutencao_eletrica",
      "manutencao_mecanica",
      "manutencao_instrumentacao",
      "lider_eletrica",
      "lider_mecanica",
      "lider_instrumentacao",
      "supervisor_eletrica",
      "supervisor_mecanica",
      "supervisor_instrumentacao",
    ];
    if (!validPerfis.includes(perfil)) {
      return jsonResponse({ error: "Perfil inválido" }, 400, cors);
    }

    const validAreas = ["Elétrica", "Mecânica", "Instrumentação"];
    if (!validAreas.includes(area)) {
      return jsonResponse({ error: "Área inválida" }, 400, cors);
    }

    // Create user with service role
    const adminClient = createClient(supabaseUrl, serviceRoleKey, {
      auth: { autoRefreshToken: false, persistSession: false },
    });

    const { data: newUser, error: createError } = await adminClient.auth.admin.createUser({
      email: email.trim(),
      password,
      email_confirm: true,
    });

    if (createError) {
      console.error("[create-user] Auth create error:", createError.message);
      return jsonResponse({ error: "Erro ao criar usuário. Verifique os dados e tente novamente." }, 400, cors);
    }

    // Create profile
    await adminClient.from("profiles").upsert({
      id: newUser.user.id,
      email: email.trim(),
      nome: nome.trim(),
      perfil,
      area,
    });

    // Create role
    await adminClient.from("user_roles").upsert({
      user_id: newUser.user.id,
      role: perfil,
    });

    return jsonResponse({ success: true, user_id: newUser.user.id }, 200, cors);
  } catch (err) {
    console.error("[create-user] Unhandled error:", (err as Error).message);
    return jsonResponse({ error: "Erro interno do servidor" }, 500, cors);
  }
});
