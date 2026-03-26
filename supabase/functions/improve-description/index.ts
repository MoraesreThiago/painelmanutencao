import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { getCorsHeaders, isOriginBlocked } from "../_shared/helpers.ts";

function jsonResponse(body: Record<string, unknown>, status: number, cors: Record<string, string>) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

const MAX_DESC_LENGTH = 2000;

Deno.serve(async (req) => {
  const cors = getCorsHeaders(req);

  if (req.method === "OPTIONS") {
    return new Response(null, { headers: cors });
  }
  if (isOriginBlocked(req)) {
    return jsonResponse({ error: "Origem não permitida" }, 403, cors);
  }

  try {
    // Auth is now enforced by Supabase gateway (verify_jwt = true),
    // but we still validate the user for logging/auditing purposes.
    const authHeader = req.headers.get("Authorization");
    if (!authHeader?.startsWith("Bearer ")) {
      return jsonResponse({ error: "Não autorizado" }, 401, cors);
    }

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_ANON_KEY")!,
      { global: { headers: { Authorization: authHeader } } }
    );

    const {
      data: { user },
      error: userError,
    } = await supabase.auth.getUser();
    if (userError || !user) {
      return jsonResponse({ error: "Não autorizado" }, 401, cors);
    }

    // --- Payload validation ---
    let body: unknown;
    try {
      body = await req.json();
    } catch {
      return jsonResponse({ error: "Payload JSON inválido" }, 400, cors);
    }

    const { descricao } = body as Record<string, unknown>;

    if (typeof descricao !== "string" || !descricao.trim()) {
      return jsonResponse({ error: "Descrição vazia" }, 400, cors);
    }
    if (descricao.length > MAX_DESC_LENGTH) {
      return jsonResponse(
        { error: `Descrição muito longa (máx. ${MAX_DESC_LENGTH} caracteres)` },
        400,
        cors
      );
    }

    const LOVABLE_API_KEY = Deno.env.get("LOVABLE_API_KEY");
    if (!LOVABLE_API_KEY) {
      console.error("[improve-description] AI API key is not configured");
      return jsonResponse({ error: "Serviço de IA indisponível" }, 500, cors);
    }

    const response = await fetch("https://ai.gateway.lovable.dev/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${LOVABLE_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "google/gemini-3-flash-preview",
        messages: [
          {
            role: "system",
            content: `Você é um assistente técnico de manutenção industrial (elétrica, mecânica e instrumentação).
Sua tarefa é aprimorar descrições de ocorrências de manutenção para ficarem mais claras, profissionais e bem escritas.

Regras:
- Corrija erros de gramática, ortografia e pontuação
- Melhore a estrutura e clareza do texto — pode reorganizar frases para melhor leitura
- Use terminologia técnica adequada quando o contexto permitir (ex: "rolamento" em vez de "peça que gira", "disjuntor" em vez de "chave que desliga")
- Mas NÃO invente informações que não estão no texto original
- Mantenha TODOS os fatos, dados e detalhes mencionados pelo autor
- Preserve termos populares/informais quando forem a melhor forma de identificar o problema (ex: "tá com folga", "fazendo barulho estranho")
- Pode adicionar conectivos e melhorar a fluidez do texto
- Seja objetivo e conciso — não torne o texto mais longo desnecessariamente
- Retorne APENAS o texto aprimorado, sem explicações ou comentários adicionais
- Mantenha o texto em português brasileiro`,
          },
          { role: "user", content: descricao },
        ],
      }),
    });

    if (!response.ok) {
      if (response.status === 429) {
        return jsonResponse({ error: "Limite de requisições excedido, tente novamente em alguns segundos." }, 429, cors);
      }
      if (response.status === 402) {
        return jsonResponse({ error: "Créditos insuficientes para IA." }, 402, cors);
      }
      const t = await response.text();
      console.error("[improve-description] AI gateway error:", response.status, t);
      return jsonResponse({ error: "Erro no serviço de IA" }, 502, cors);
    }

    const data = await response.json();
    const improved = data.choices?.[0]?.message?.content?.trim();

    if (!improved) {
      console.error("[improve-description] Empty AI response");
      return jsonResponse({ error: "Resposta vazia do serviço de IA" }, 502, cors);
    }

    return jsonResponse({ improved }, 200, cors);
  } catch (e) {
    console.error("[improve-description] Unhandled error:", (e as Error).message);
    return jsonResponse({ error: "Erro interno do servidor" }, 500, cors);
  }
});
