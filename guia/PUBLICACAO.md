# Guia Adito — publicação e revisão

Site estático em HTML, CSS e JavaScript, sem build. O vídeo foi removido. A identidade usa a paleta, a logo e as famílias tipográficas oficiais; os arquivos de marca e fontes são referenciados no repositório público por commit fixo.

## Atualizar a branch existente

Na raiz do clone Adito, na branch `feature/guia-adito`, substitua somente os arquivos do guia em `guia/` pelo conteúdo deste pacote, incluindo `.nojekyll`. Não altere os diretórios não monitorados `Docs/LevantamentoEscopo/` e `outputs/`.

```bash
git status
python3 -m http.server 8080 --directory guia
```

Acesse http://localhost:8080 e confira o site. Encerre o servidor com Ctrl+C. Após revisar:

```bash
git add guia/
git status
git commit -m "docs: atualiza guia de instalação e primeiro acesso do Adito"
git push -u origin feature/guia-adito
```

A pasta `guia/` não é uma origem de publicação direta por branch no Pages. Para manter essa organização, configure um workflow de GitHub Actions que publique somente `guia/`, após acordo com a equipe. Em Settings → Pages → Build and deployment, um administrador poderá selecionar GitHub Actions como origem. Abra um pull request para a branch de destino adotada pela equipe. Não publique banco de dados, chaves ou arquivos de levantamento internos.

## Checklist da equipe

- [ ] Conferir os formatos de instaladores efetivamente disponíveis no Release.
- [ ] Testar a instalação e a primeira abertura em Linux e Windows, verificando dados e contextos padrão.
- [ ] Confirmar os provedores de IA disponíveis e o caráter opcional do contexto.
- [ ] Validar perguntas no desktop e comparar com a fonte oficial.
- [ ] Conferir logo, fontes, responsividade e acessibilidade.
- [ ] Aprovar a remoção do vídeo no escopo da task.
- [ ] Revisar o pull request, configurar Pages e verificar o endereço público.

As instruções sobre o instalador, banco, contextos e IA foram atualizadas a partir das informações fornecidas pela equipe; não houve teste de instalação real nesta revisão.
