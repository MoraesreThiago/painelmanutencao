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
      return jsonResponse({ error: "Apenas administradores podem excluir usuários" }, 403, cors);
    }

    // --- Payload validation ---
    let body: unknown;
    try {
      body = await req.json();
    } catch {
      return jsonResponse({ error: "Payload JSON inválido" }, 400, cors);
    }

    const { user_id } = body as Record<string, unknown>;

    if (typeof user_id !== "string" || !user_id.trim()) {
      return jsonResponse({ error: "ID do usuário é obrigatório" }, 400, cors);
    }

    // UUID format validation
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(user_id)) {
      return jsonResponse({ error: "ID do usuário inválido" }, 400, cors);
    }

    // Prevent self-deletion
    if (user_id === caller.id) {
      return jsonResponse({ error: "Você não pode excluir sua própria conta" }, 400, cors);
    }

    const adminClient = createClient(supabaseUrl, serviceRoleKey, {
      auth: { autoRefreshToken: false, persistSession: false },
    });

    // Delete profile and roles
    await adminClient.from("profiles").delete().eq("id", user_id);
    await adminClient.from("user_roles").delete().eq("user_id", user_id);

    // Delete from auth.users
    const { error: deleteError } = await adminClient.auth.admin.deleteUser(user_id);

    if (deleteError) {
      console.error("[delete-user] Auth delete error:", deleteError.message);
      return jsonResponse({ error: "Erro ao excluir usuário. Tente novamente." }, 400, cors);
    }

    return jsonResponse({ success: true }, 200, cors);
  } catch (err) {
    console.error("[delete-user] Unhandled error:", (err as Error).message);
    return jsonResponse({ error: "Erro interno do servidor" }, 500, cors);
  }
});
