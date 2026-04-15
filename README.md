# PainelManutenção

Monólito modular em Django para gestão de manutenção industrial, com:

- Django Templates como frontend principal
- HTMX para interações dinâmicas sem SPA
- Django REST Framework em `/api/v1/`
- PostgreSQL como banco principal
- base de PWA com suporte offline parcial

## Estrutura principal

```text
repo/
├── backend/
│   ├── manage.py
│   ├── config/
│   │   ├── asgi.py
│   │   ├── wsgi.py
│   │   ├── urls.py
│   │   └── settings/
│   │       ├── base.py
│   │       ├── dev.py
│   │       └── prod.py
│   ├── apps/
│   │   ├── accounts/
│   │   ├── access/
│   │   ├── unidades/
│   │   ├── colaboradores/
│   │   ├── equipamentos/
│   │   ├── ocorrencias/
│   │   ├── ordens_servico/
│   │   ├── relatorios/
│   │   ├── notificacoes/
│   │   ├── integracoes/
│   │   └── auditoria/
│   ├── api/
│   │   └── v1/
│   ├── common/
│   ├── templates/
│   ├── static/
│   ├── requirements/
│   └── tests/
├── infra/
├── docs/
└── README.md
```

## Como rodar localmente

### 1. Instalar dependências

```powershell
cd "C:\Users\user\OneDrive\Documentos\New project\repo"
py -3.12 -m pip install -r .\backend\requirements\dev.txt
```

### 2. Aplicar migrações

```powershell
cd "C:\Users\user\OneDrive\Documentos\New project\repo"
py -3.12 .\backend\manage.py migrate
```

### 3. Criar dados iniciais

```powershell
cd "C:\Users\user\OneDrive\Documentos\New project\repo"
py -3.12 .\backend\manage.py bootstrap_system
```

### 4. Subir a aplicação Django

```powershell
cd "C:\Users\user\OneDrive\Documentos\New project\repo"
py -3.12 .\backend\manage.py runserver 0.0.0.0:8000
```

### URLs principais

- App web: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Admin Django: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- API DRF: [http://127.0.0.1:8000/api/v1/](http://127.0.0.1:8000/api/v1/)

Credenciais iniciais:

- e-mail: `admin@maintenance.example.com`
- senha: `Admin@123`

## Docker Compose

```powershell
cd "C:\Users\user\OneDrive\Documentos\New project\repo"
docker compose up --build
```

Serviços:

- `db`: PostgreSQL 16
- `backend`: Django + Gunicorn

## Variáveis de ambiente

Veja `.env.example`.

As principais são:

- `BACKEND_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DEFAULT_ADMIN_EMAIL`
- `DEFAULT_ADMIN_PASSWORD`

## Organização de código

- Views ficam enxutas.
- Regras de negócio ficam em `services.py`.
- Templates ficam em `backend/templates`.
- Assets, manifest e service worker ficam em `backend/static`.
- A API interna fica em `backend/api/v1`.
- Componentes transversais ficam em `backend/common`.

## Situação da migração

A nova espinha dorsal Django já está criada e validada com:

- `manage.py check`
- migrations iniciais
- bootstrap inicial
- smoke tests básicos

A stack anterior em FastAPI/Reflex foi removida do repositório. O desenvolvimento e a portabilidade seguem somente em `backend/`.
