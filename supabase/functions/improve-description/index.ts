import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-supabase-client-platform, x-supabase-client-platform-version, x-supabase-client-runtime, x-supabase-client-runtime-version",
};

Deno.serve(async (req) => {

  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const authHeader = req.headers.get("Authorization");
    if (!authHeader?.startsWith("Bearer ")) {
      return new Response(JSON.stringify({ error: "Não autorizado" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_ANON_KEY")!,
      { global: { headers: { Authorization: authHeader } } }
    );

    const token = authHeader.replace("Bearer ", "");
    const { data: claimsData, error: claimsError } = await supabase.auth.getClaims(token);
    if (claimsError || !claimsData?.claims) {
      return new Response(JSON.stringify({ error: "Não autorizado" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const { descricao } = await req.json();
    if (!descricao?.trim()) {
      return new Response(JSON.stringify({ error: "Descrição vazia" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }
    if (descricao.length > 2000) {
      return new Response(JSON.stringify({ error: "Descrição muito longa (máx. 2000 caracteres)" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const LOVABLE_API_KEY = Deno.env.get("LOVABLE_API_KEY");
    if (!LOVABLE_API_KEY) {
      console.error("[improve-description] AI API key is not configured");
      return new Response(JSON.stringify({ error: "Serviço de IA indisponível" }), {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
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
        return new Response(JSON.stringify({ error: "Limite de requisições excedido, tente novamente em alguns segundos." }), {
          status: 429, headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }
      if (response.status === 402) {
        return new Response(JSON.stringify({ error: "Créditos insuficientes para IA." }), {
          status: 402, headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }
      const t = await response.text();
      console.error("AI gateway error:", response.status, t);
      throw new Error("Erro no gateway de IA");
    }

    const data = await response.json();
    const improved = data.choices?.[0]?.message?.content?.trim();

    return new Response(JSON.stringify({ improved }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (e) {
    
    console.error("improve-description error:", e);
    return new Response(JSON.stringify({ error: e instanceof Error ? e.message : "Erro desconhecido" }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
