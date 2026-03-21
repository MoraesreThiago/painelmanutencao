# ManutençãoPro

Sistema de gestão de manutenção industrial com controle de acesso por perfil e área, desenvolvido com React + Supabase.

**URL de produção:** https://painelmanutencao.lovable.app

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| UI Components | shadcn/ui (Radix primitives) |
| Estado/Cache | TanStack React Query |
| Roteamento | React Router v6 |
| Backend/Auth | Supabase (PostgreSQL, Auth, Edge Functions) |
| PWA | vite-plugin-pwa (Workbox) |
| Mobile | Capacitor (Android) |

---

## Estrutura de Pastas

```
src/
├── components/        # Componentes reutilizáveis
│   ├── ui/            # shadcn/ui (button, card, dialog, etc.)
│   ├── AppSidebar.tsx # Navegação lateral com permissões
│   ├── Layout.tsx     # Layout principal (sidebar + content)
│   ├── NavLink.tsx    # Link de navegação ativo
│   └── ProtectedRoute.tsx # Guard de autenticação
├── contexts/
│   └── AuthContext.tsx # Provider de autenticação (user + profile)
├── hooks/             # Custom hooks (use-mobile, use-toast)
├── integrations/
│   └── supabase/
│       ├── client.ts  # Cliente Supabase tipado
│       └── types.ts   # Tipos gerados automaticamente (read-only)
├── lib/
│   ├── roles.ts       # Helpers de autorização (isAdmin, isLeader, etc.)
│   ├── utils.ts       # Utilidades (cn, etc.)
│   └── fetchAllEquipamentos.ts
├── pages/             # Páginas/rotas do app
│   ├── Login.tsx
│   ├── Dashboard.tsx
│   ├── Ocorrencias.tsx / OcorrenciaForm.tsx
│   ├── Colaboradores.tsx
│   ├── Equipamentos.tsx
│   ├── MotoresEletricos.tsx / MotorEletricoForm.tsx
│   ├── Historico.tsx
│   ├── ResumoMensal.tsx
│   ├── Automacoes.tsx
│   ├── GerenciarUsuarios.tsx  # Admin-only
│   └── NotFound.tsx
├── types/
│   └── database.ts    # Tipos de domínio (Profile, etc.)
└── test/              # Setup de testes (Vitest)

supabase/
├── config.toml        # Configuração do projeto Supabase
├── migrations/        # Migrações SQL (read-only após aplicadas)
└── functions/
    ├── create-user/   # Edge Function: criação de usuários (admin-only)
    └── improve-description/ # Edge Function: IA para descrições técnicas
```

---

## Fluxo de Autenticação

```
Usuário → /login → supabase.auth.signInWithPassword()
                         ↓
              AuthContext carrega session + profile
                         ↓
              ProtectedRoute verifica user !== null
                         ↓
              Layout renderiza sidebar + <Outlet />
```

### Regras Importantes

1. **Sem cadastro público** — a opção "Allow new users to sign up" está desativada no Supabase.
2. **Criação de usuários** — apenas administradores, via página `/usuarios`, que invoca a Edge Function `create-user` com `service_role_key`.
3. **Perfis** — após criar o auth user, a função cria registros em `profiles` e `user_roles`.
4. **JWT** — Edge Functions validam tokens via `getClaims()` em código (`verify_jwt = false` no config).

---

## Perfis e Hierarquia de Acesso

| Perfil | Área | Nível |
|---|---|---|
| `administrador` | Todas | Total |
| `supervisor_eletrica` | Elétrica | Elevado |
| `supervisor_mecanica` | Mecânica | Elevado |
| `lider_eletrica` | Elétrica | Elevado |
| `lider_mecanica` | Mecânica | Elevado |
| `manutencao_eletrica` | Elétrica | Básico |
| `manutencao_mecanica` | Mecânica | Básico |

**Funções de banco auxiliares:** `has_role()`, `is_leader_or_above()`, `get_user_area()` — todas `SECURITY DEFINER`.

---

## Tabelas Principais

### `profiles`
Dados do usuário (nome, email, perfil, área). Chave primária = `auth.users.id`.

### `user_roles`
Vínculo usuário ↔ role (`app_role` enum). Usado pelas RLS policies via `has_role()`.

### `ocorrencias`
Registros de manutenção com área, turno, equipamento, descrição, status de OS, parada, etc.

### `colaboradores`
Equipe de manutenção (nome, turno, área, cargo, status).

### `equipamentos`
Cadastro de equipamentos com tag, área, local e status.

### `motores_eletricos`
Controle de saída/retorno de motores para serviço externo.

### `ocorrencias_importacao`
Staging de importações em lote (admin-only).

### Views (`vw_equipamentos_*`)
Views consolidadas de equipamentos com `SECURITY DEFINER`.

---

## Regras de Acesso (RLS)

Todas as tabelas possuem Row Level Security habilitado. Resumo:

| Tabela | SELECT | INSERT | UPDATE | DELETE |
|---|---|---|---|---|
| `profiles` | Admin: todos · Líder/Sup: área · Usuário: próprio | Próprio perfil | Próprio (sem mudar perfil/área) | ✗ |
| `user_roles` | Próprio + Admin (ALL) | Admin | Admin | Admin |
| `colaboradores` | Admin + área | Líder/Sup da área | Líder/Sup da área | Líder/Sup da área |
| `ocorrencias` | Admin + área | Área do usuário | Admin/Líder: área · Usuário: área + <24h | Líder/Sup da área |
| `equipamentos` | Admin + área (ou NULL) | Admin | Admin | Admin |
| `motores_eletricos` | Admin + área | Área do usuário | Área do usuário | Líder/Sup da área |
| `ocorrencias_importacao` | Admin | Admin | Admin | Admin |

---

## Edge Functions

### `create-user`
- **Propósito:** Criar usuários (auth + profile + role)
- **Autenticação:** Verifica se o chamador é `administrador` via consulta a `user_roles`
- **Segurança:** Usa `SUPABASE_SERVICE_ROLE_KEY` para `admin.createUser()`

### `improve-description`
- **Propósito:** Reescrever descrições de ocorrências com IA (terminologia técnica)
- **Autenticação:** `getClaims()` valida JWT
- **CORS:** Restrito aos domínios do app
- **API:** Lovable AI Gateway (`google/gemini-3-flash-preview`)

---

## Como Rodar Localmente

### Pré-requisitos
- Node.js ≥ 18
- npm ou bun

### Setup

```bash
git clone <repo-url>
cd <repo-dir>
npm install
npm run dev
# Acesse http://localhost:8080
```

As variáveis `VITE_SUPABASE_URL` e `VITE_SUPABASE_PUBLISHABLE_KEY` já estão no `.env`.

### Testes

```bash
npm test             # Vitest (unit tests)
npx playwright test  # E2E tests
```

### Build de Produção

```bash
npm run build
npm run preview
```

### Android (Capacitor)

```bash
npx cap sync android
npx cap open android
```

---

## Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `VITE_SUPABASE_URL` | URL do projeto Supabase |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Chave anon (pública) |
| `VITE_SUPABASE_PROJECT_ID` | ID do projeto |

Secrets das Edge Functions (configurados no painel Supabase):
`SUPABASE_SERVICE_ROLE_KEY`, `LOVABLE_API_KEY`

---

## Decisões de Arquitetura

1. **RBAC via banco** — roles em tabela separada (`user_roles`) com funções `SECURITY DEFINER` para evitar recursão em RLS.
2. **Segregação por área** — dados filtrados automaticamente pela área do usuário no nível do banco.
3. **Sem registro público** — signup desabilitado no Supabase Auth; criação centralizada via Edge Function.
4. **PWA** — app instalável com service worker para cache offline.
5. **IA integrada** — descrições de ocorrências podem ser aprimoradas via LLM com terminologia industrial.
