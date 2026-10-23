# Proposta de ligações entre as fontes

**SigPesq · Lattes · CNPq DGP · SRC**: o que une as quatro bases e por onde o ETL pode cruzá-las.

## 🧭 Mapa das ligações


**Roteiro:**

| # | Ligação | Cruza por | Resultado |
|:-:|---|---|---|
| ① | SigPesq ↔ CNPq | URL do espelho do grupo | **331 de 347** grupos, chave exata |
| ② | 4 fontes → Pessoa | id → CPF → e-mail → nome + contexto | **65 de 71** coordenadores do SRC achados na pesquisa |
| ③ | SigPesq ↔ Lattes | título + orientador | **30%** dos planos; orientador igual em 98% |
| ④ | SRC ↔ Lattes | título da ação | só **10%** das ações: ligar, não fundir |
| ⑤ | SigPesq ↔ SRC | hash de CPF e e-mail | chave forte, depende da credencial do SRC |

## 🧩 Classes que unem as bases

| Classe | SigPesq | Lattes | CNPq | SRC | Junta por | |
|---|:-:|:-:|:-:|:-:|---|:-:|
| Grupo de pesquisa | ✅ | ➖ | ✅ | ➖ | URL do espelho | 🟢 |
| Organização | ✅ | ✅ | ✅ | ✅ | tabela de campi (IFES → campus) | 🟢 |
| Área do conhecimento | ✅ | ✅ | ✅ | ⚠️ | tabela de áreas do CNPq | 🟢 |
| Pessoa | ✅ | ✅ | ✅ | ✅ | CPF/e-mail em hash ou nome | 🟡 |
| Orientação | ✅ | ✅ | ➖ | ➖ | título + orientador | 🟡 |
| Participação com papel | ✅ | ✅ | ✅ | ✅ | pessoa já casada | 🟡 |
| Vínculo institucional | ✅ | ✅ | ✅ | ✅ | reforça o casamento de pessoas | 🟡 |
| Fomento | ✅ | ✅ | ➖ | ✅ | de/para órgão × programa | 🟡 |
| Iniciativa | ✅ | ✅ | ➖ | ✅ | título + coordenador | 🔴 |
| Linha de pesquisa | ✅ | ✅ | ✅ | ➖ | texto | 🔴 |
| Curso | ✅ | ✅ | ➖ | ➖ | texto | 🔴 |

✅ tem · ➖ não tem · ⚠️ só no portal, falta no modelo · 🟢 funde com segurança · 🟡 funde com regra · 🔴 só liga ou enriquece
