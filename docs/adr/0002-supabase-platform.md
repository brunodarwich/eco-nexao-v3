# ADR 0002 — Supabase gerenciado como plataforma de dados

Status: aceito  
Data: 11/08/2026

## Contexto

A aplicação precisa de PostgreSQL/PostGIS, autenticação, storage e ambientes reproduzíveis. O proprietário prefere não depender de Docker.

## Decisão

Usar Supabase gerenciado para PostgreSQL 17 + PostGIS, Auth e Storage. Manter FastAPI como API de domínio e fronteira dos conectores externos.

## Limites

- Expo acessa diretamente Supabase Auth e fluxos de Storage aprovados.
- Dados territoriais e regras de negócio passam pelo FastAPI.
- Migrations SQL Supabase são a fonte única do schema.
- Projetos development, test, staging e production são separados.
- IA não recebe credenciais de produção.

## Consequências

- Docker deixa de ser pré-requisito.
- Desenvolvimento depende de rede e de um projeto Supabase remoto.
- RLS, grants, Storage policies e JWT tornam-se parte obrigatória dos testes.
- FastAPI usa conexão PostgreSQL gerenciada e valida tokens Supabase.
