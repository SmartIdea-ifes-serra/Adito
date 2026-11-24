# Assets visuais do Adito

O pacote `Adito/app/assets/adito-assets.zip` reúne os arquivos usados pela interface web e pela casca Tauri, com um `manifest.json` de formatos, dimensões e tamanhos. Os mesmos arquivos estão nos diretórios de origem para uso direto pelo aplicativo.

A marca mantém os PNGs originais da identidade vigente, com as mesmas cores, texturas e transparência nos temas claro e escuro. Os ícones existentes do Tauri também são preservados. As exportações em SVG incorporam a arte PNG original sem perdas: são arquivos autônomos, mas o símbolo continua raster, limitado à resolução de origem de 1254 × 1254. Uma vetorização integral exige o arquivo vetorial original aprovado da marca, que não acompanha o projeto. As assinaturas horizontais usam IBM Plex Sans, com o nome convertido em caminhos e sem dependências externas.

| Arquivo | Formato / dimensão | Aplicação |
| --- | --- | --- |
| `frontend-vue/public/brand/adito-light.svg` e `adito-dark.svg` | SVG, viewBox 1254 × 1254 | Contêiner autônomo da arte original incorporada, em temas claro e escuro |
| `frontend-vue/public/brand/adito-light.png` e `adito-dark.png` | PNG RGBA, 1254 × 1254 | Arquivos originais preservados integralmente; fontes para as exportações |
| `frontend-vue/public/brand/adito-light-1024.png` e `adito-dark-1024.png` | PNG RGBA, 1024 × 1024 | Exportação em alta resolução |
| `frontend-vue/public/brand/logo-adito-light.svg` e `logo-adito-dark.svg` | SVG, viewBox 880 × 320 | Assinatura horizontal com o nome Adito |
| `frontend-vue/public/brand/logo-adito-light.png` e `logo-adito-dark.png` | PNG RGBA, 880 × 320 | Assinatura horizontal em resolução padrão |
| `frontend-vue/public/brand/logo-adito-light@2x.png` e `logo-adito-dark@2x.png` | PNG RGBA, 1760 × 640 | Assinatura horizontal para telas de alta densidade |
| `frontend-vue/public/favicon.svg` | SVG adaptável ao tema do sistema | Ícone da aba do navegador |
| `frontend-vue/public/favicon.png` e `favicon-32x32.png` | PNG RGBA, 32 × 32 | Alternativa de favicon raster |
| `frontend-vue/public/favicon-16x16.png` | PNG RGBA, 16 × 16 | Ícone de aba compacto |
| `frontend-vue/public/favicon.ico` | ICO, 16, 32 e 48 px | Compatibilidade com navegadores e atalhos |
| `frontend-vue/public/apple-touch-icon.png` | PNG RGBA, 180 × 180 | Atalho em dispositivos Apple |
| `src-tauri/icons/32x32.png` | PNG RGBA, 32 × 32 | Tauri |
| `src-tauri/icons/128x128.png` | PNG RGBA, 128 × 128 | Tauri |
| `src-tauri/icons/128x128@2x.png` | PNG RGBA, 256 × 256 | Tauri em alta densidade |
| `src-tauri/icons/icon.png` | PNG RGBA, 512 × 512 | Ícone principal desktop |
| `src-tauri/icons/icon.ico` | ICO, tamanhos originais registrados no manifesto | Windows |
| `src-tauri/icons/icon.icns` | ICNS, 32 a 1024 px, incluindo variantes @2x | macOS |

## Reexportação

A partir da raiz do repositório, execute:

```bash
python3 Adito/app/scripts/exportar_assets.py
```

O script é uma ferramenta de desenvolvimento para Linux e usa Pillow, PyGObject, Pycairo e librsvg, além do Fontconfig e da fonte local já incluída no projeto. Em Debian/Ubuntu, os pacotes correspondentes são `python3-pil`, `python3-gi`, `python3-cairo`, `python3-gi-cairo` e `gir1.2-rsvg-2.0`. Eles não são dependências do núcleo Python nem precisam acompanhar o instalador. A exportação não usa rede ou fontes externas.

As fontes da arte são os dois PNGs originais `adito-light.png` e `adito-dark.png`. As variantes SVG, assinaturas horizontais, PNGs adicionais, favicons e ZIP são gerados a partir deles, sem substituir suas cores. Os arquivos originais de `src-tauri/icons` são verificados e incluídos no pacote sem modificação. A tipografia vem de `public/fonts/ibm-plex-5.ttf`, distribuída com sua licença SIL Open Font License em `public/fonts/ibmplexsans-OFL.txt`.

## Validação

Cada exportação reabre todos os arquivos raster para verificar a decodificação, registra as dimensões no manifesto e inspeciona os tamanhos internos dos contêineres ICO/ICNS. Os PNGs do Tauri são RGBA, com área externa transparente. Os SVGs contêm a imagem original incorporada; o nome nas assinaturas horizontais usa caminhos, sem dependência de fontes no destino. Os PNGs da marca e os seis arquivos Tauri foram comparados byte a byte com os arquivos originais do repositório. A revisão visual confere os símbolos claro/escuro, a assinatura horizontal e o ícone de 32 px.
