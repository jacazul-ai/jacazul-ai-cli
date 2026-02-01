# Taskwarrior Cleanup Reminder

## 📅 Data: 2026-02-15 (2 semanas após migração)

## 🎯 Tarefa: Arquivar Base Central

### ✅ Antes de Arquivar - Checklist:

- [ ] Base do projeto (`~/.task/piraz_ai_cli_sandboxed/`) está funcionando bem?
- [ ] Todas as tasks estão acessíveis via `taskp`?
- [ ] `tw-flow` e `ponder` funcionam corretamente?
- [ ] Nenhum problema encontrado nas últimas 2 semanas?

### 📦 Procedimento de Arquivamento:

```bash
# 1. Fazer backup final
tar -czf ~/.task-backup-$(date +%Y%m%d).tar.gz ~/.task/

# 2. Verificar backup
tar -tzf ~/.task-backup-$(date +%Y%m%d).tar.gz | head

# 3. Mover (não deletar) para arquivo
mv ~/.task ~/.task-archived-$(date +%Y%m%d)

# 4. (Opcional) Após mais 1 mês, deletar se tudo ok
# rm -rf ~/.task-archived-*
```

### ⚠️ Importante:

- Base central está em `~/.task/` (~400KB)
- Contém 90 tasks (duplicadas na base do projeto)
- Manter backup compactado é suficiente
- Espaço liberado: ~400KB

### 🔄 Rollback (se necessário):

```bash
# Se algo der errado, restaurar:
mv ~/.task-archived-* ~/.task
# ou
tar -xzf ~/.task-backup-*.tar.gz -C ~/
```

---

**Criado em:** 2026-02-01  
**Revisar em:** 2026-02-15
