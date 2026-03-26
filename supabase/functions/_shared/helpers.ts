import { createClient, SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2";

// ─── CORS ────────────────────────────────────────────────────────────────────

const ALLOWED_ORIGINS = Deno.env.get("ALLOWED_ORIGINS")
  ?.split(",")
  .map((o) => o.trim())
  .filter(Boolean) ?? [];

/**
 * Returns CORS headers for the given request.
 *
 * - If ALLOWED_ORIGINS is configured, only listed origins get
 *   `Access-Control-Allow-Origin`. Unknown origins receive a 403-safe
 *   empty string, which the browser will reject.
 * - If ALLOWED_ORIGINS is empty (local dev), all origins are allowed
 *   so `supabase functions serve` works out of the box.
 */
export function getCorsHeaders(req: Request): Record<string, string> {
  const origin = req.headers.get("Origin") ?? "";

  let allowedOrigin: string;
  if (ALLOWED_ORIGINS.length === 0) {
    // Local development: no restriction
    allowedOrigin = origin || "*";
  } else {
    // Production: strict allow-list
    allowedOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : "";
  }

  return {
    "Access-Control-Allow-Origin": allowedOrigin,
    "Access-Control-Allow-Headers":
      "authorization, x-client-info, apikey, content-type, x-supabase-client-platform, x-supabase-client-platform-version, x-supabase-client-runtime, x-supabase-client-runtime-version",
    Vary: "Origin",
  };
}

/**
 * Returns true when the origin is NOT in the allow-list (production only).
 * Use after getCorsHeaders to short-circuit with 403.
 */
export function isOriginBlocked(req: Request): boolean {
  if (ALLOWED_ORIGINS.length === 0) return false; // dev mode
  const origin = req.headers.get("Origin") ?? "";
  return !ALLOWED_ORIGINS.includes(origin);
}

// ─── Responses ───────────────────────────────────────────────────────────────

export function jsonOk(data: Record<string, unknown>, cors: Record<string, string>) {
  return json(data, 200, cors);
}

export function jsonError(message: string, status: number, cors: Record<string, string>) {
  return json({ error: message }, status, cors);
}

function json(body: Record<string, unknown>, status: number, cors: Record<string, string>) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

// ─── Request helpers ─────────────────────────────────────────────────────────

export function parseAuthHeader(req: Request): string | null {
  const h = req.headers.get("Authorization");
  return h?.startsWith("Bearer ") ? h : null;
}

export async function parseBody<T = Record<string, unknown>>(req: Request): Promise<T> {
  try {
    return (await req.json()) as T;
  } catch {
    throw new PayloadError("Payload JSON inválido");
  }
}

// ─── Auth helpers ────────────────────────────────────────────────────────────

export interface CallerInfo {
  id: string;
  email: string | undefined;
}

/**
 * Validates the JWT, fetches the user object and returns basic caller info.
 * Throws `AuthError` on failure.
 */
export async function getCallerUser(authHeader: string): Promise<{ caller: CallerInfo; callerClient: SupabaseClient }> {
  const callerClient = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_ANON_KEY")!,
    { global: { headers: { Authorization: authHeader } } },
  );

  const { data: { user }, error } = await callerClient.auth.getUser();
  if (error || !user) throw new AuthError();

  return {
    caller: { id: user.id, email: user.email },
    callerClient,
  };
}

/**
 * Asserts the caller holds the `administrador` role.
 * Throws `ForbiddenError` if not.
 */
export async function assertAdmin(callerClient: SupabaseClient, callerId: string): Promise<void> {
  const { data } = await callerClient
    .from("user_roles")
    .select("role")
    .eq("user_id", callerId)
    .eq("role", "administrador")
    .maybeSingle();

  if (!data) throw new ForbiddenError();
}

/**
 * Returns a service-role Supabase client for privileged operations.
 */
export function getAdminClient(): SupabaseClient {
  return createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
}

// ─── Validation helpers ─────────────────────────────────────────────────────

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function assertUuid(value: unknown, label: string): string {
  if (typeof value !== "string" || !UUID_RE.test(value)) {
    throw new PayloadError(`${label} inválido`);
  }
  return value;
}

export function assertNonEmptyString(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) {
    throw new PayloadError(`${label} é obrigatório`);
  }
  return value.trim();
}

export const VALID_PERFIS = [
  "manutencao_eletrica",
  "manutencao_mecanica",
  "manutencao_instrumentacao",
  "lider_eletrica",
  "lider_mecanica",
  "lider_instrumentacao",
  "supervisor_eletrica",
  "supervisor_mecanica",
  "supervisor_instrumentacao",
] as const;

export const VALID_AREAS = ["Elétrica", "Mecânica", "Instrumentação"] as const;

// ─── Custom errors ───────────────────────────────────────────────────────────

export class AuthError extends Error {
  status = 401;
  constructor(msg = "Não autorizado") {
    super(msg);
  }
}

export class ForbiddenError extends Error {
  status = 403;
  constructor(msg = "Apenas administradores podem executar esta ação") {
    super(msg);
  }
}

export class PayloadError extends Error {
  status = 400;
  constructor(msg: string) {
    super(msg);
  }
}

export function isKnownError(e: unknown): e is AuthError | ForbiddenError | PayloadError {
  return e instanceof AuthError || e instanceof ForbiddenError || e instanceof PayloadError;
}
