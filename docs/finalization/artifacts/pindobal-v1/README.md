# Pacote de promoção Pindobal v1

Status: **bloqueado para promoção até aceite editorial explícito**.

Este diretório fixa metadados, hashes, migrations, versões e contagens do incremento
Pindobal verificado no Supabase test. Ele não contém o dataset original, credenciais,
JWTs, payloads raw ou dados de staging/production.

## Verificação offline

Na raiz de `backend`:

```powershell
.\.venv\Scripts\python.exe -m scripts.verify_pindobal_promotion_package
```

O verificador confere o checksum do manifesto, todos os arquivos de implementação e
migrations referenciados, as nove fontes do snapshot e os invariantes do double-run.

## Pré-condições para uma futura promoção

1. Revisar editorialmente os 53 candidatos fuzzy; nenhum merge é automático.
2. Confirmar licença, crédito e alt text da capa e de toda mídia editorial.
3. Manter os 737 registros Google legados sem Place ID fora de merge automático.
4. Executar Publish Guard, migrations, advisors, dry-run e smoke no ambiente alvo.
5. Obter autorização separada e explícita para cada ambiente. Este pacote não autoriza
   staging nem production.

## Rollback lógico

Interromper a promoção e manter rota, atores e mídias em estado `draft`/não publicado.
Preservar audit trail, proveniência e registros de ingestão. Não apagar dados como
rollback automático. Qualquer correção produz uma nova versão imutável do pacote,
mantendo esta versão para auditoria.
