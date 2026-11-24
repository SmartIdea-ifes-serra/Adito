import { computed, ref, shallowRef } from 'vue'
import {
  appInstalar,
  appVerificar,
  dadosInstalar,
  dadosStatus,
  dadosVerificar,
  type AppUpdate,
  type DadosRemoto,
  type DadosStatus,
} from '@/common/api/atualizacoes'

/**
 * Estado único (compartilhado entre a barra lateral e a tela de primeiro uso) das atualizações.
 * Ao abrir, confere uma vez se há versão nova do app ou dos dados; nunca instala sem o usuário pedir.
 * Sem internet, ou sem release publicado, não mostra nada.
 */

const status = ref<DadosStatus | null>(null)
const dadosRemoto = ref<DadosRemoto | null>(null)
const app = shallowRef<AppUpdate | null>(null)

const instalandoDados = ref(false)
const instalandoApp = ref(false)
const progressoApp = ref(0)
const erro = ref<string | null>(null)
const avisoAberto = ref(false)
const avisosExibidos = new Set<string>()

let verificacao: Promise<void> | null = null
let verificando = false

function mensagem(err: unknown): string {
  if (typeof err === 'string') return err
  if (err && typeof err === 'object' && 'message' in err) return String((err as Error).message)
  return String(err)
}

async function carregarStatus() {
  try {
    status.value = await dadosStatus()
  } catch {
    status.value = null
  }
}

async function verificarAgora() {
  await carregarStatus()
  const [remoto, update] = await Promise.allSettled([dadosVerificar(), appVerificar()])
  dadosRemoto.value = remoto.status === 'fulfilled' ? remoto.value : null
  app.value = update.status === 'fulfilled' ? update.value : null
  avaliarAviso()
}

/** O padrão reutiliza a conferência; forcar permite detectar novas versões na mesma sessão. */
function verificar({ forcar = false }: { forcar?: boolean } = {}): Promise<void> {
  if (verificacao && (!forcar || verificando || instalandoApp.value || instalandoDados.value)) return verificacao
  verificando = true
  verificacao = verificarAgora().catch(() => {}).finally(() => { verificando = false })
  return verificacao
}

/** Primeiro uso: o app está rodando como app (status conhecido) e ainda não tem dados. */
const precisaPrimeiraCarga = computed(() => status.value !== null && !status.value.instalado)

const dadosNovos = computed(() => {
  const s = status.value
  const r = dadosRemoto.value
  // Em desenvolvimento o núcleo usa o dados.db do repositório: não oferece troca.
  if (!s || !r || !s.instalado || s.desenvolvimento) return null
  return r.atualizacao ? r : null
})

const temAtualizacao = computed(() => !!app.value || !!dadosNovos.value)

function versoesDisponiveis() {
  return [app.value ? `app:${app.value.version}` : null, dadosNovos.value ? `dados:${dadosNovos.value.versao}` : null]
    .filter((versao): versao is string => versao !== null)
}

function avaliarAviso() {
  // A chave da primeira carga deve ser resolvida antes de qualquer outro aviso.
  if (precisaPrimeiraCarga.value || !temAtualizacao.value) {
    avisoAberto.value = false
    return
  }
  const versoes = versoesDisponiveis()
  if (versoes.some((versao) => !avisosExibidos.has(versao))) {
    versoes.forEach((versao) => avisosExibidos.add(versao))
    avisoAberto.value = true
  }
}

function abrirAviso() {
  if (precisaPrimeiraCarga.value || !temAtualizacao.value) return
  versoesDisponiveis().forEach((versao) => avisosExibidos.add(versao))
  avisoAberto.value = true
}

function adiarAviso() {
  if (instalandoApp.value || instalandoDados.value) return
  avisoAberto.value = false
  erro.value = null
}

async function instalarDados(chave?: string): Promise<boolean> {
  if (instalandoApp.value || instalandoDados.value) return false
  instalandoDados.value = true
  erro.value = null
  try {
    await dadosInstalar(chave)
    await carregarStatus()
    if (dadosRemoto.value) dadosRemoto.value = { ...dadosRemoto.value, atualizacao: false, precisa_chave: false }
    avaliarAviso()
    return true
  } catch (err) {
    erro.value = mensagem(err)
    // Pode ter sido a chave que mudou: volta a perguntar ao Rust o que falta.
    try {
      dadosRemoto.value = await dadosVerificar()
    } catch {
      /* sem rede: mantém o que já sabia */
    }
    return false
  } finally {
    instalandoDados.value = false
  }
}

async function instalarApp(): Promise<void> {
  if (!app.value || instalandoApp.value || instalandoDados.value) return
  instalandoApp.value = true
  progressoApp.value = 0
  erro.value = null
  try {
    await appInstalar(app.value, (f) => (progressoApp.value = f))
    app.value = null
    avaliarAviso()
  } catch (err) {
    erro.value = `Não foi possível atualizar o app: ${mensagem(err)}`
  } finally {
    instalandoApp.value = false
  }
}

export function useAtualizacoes() {
  return {
    status,
    dadosRemoto,
    app,
    dadosNovos,
    temAtualizacao,
    precisaPrimeiraCarga,
    instalandoDados,
    instalandoApp,
    progressoApp,
    erro,
    avisoAberto,
    abrirAviso,
    adiarAviso,
    verificar,
    instalarDados,
    instalarApp,
    limparErro: () => (erro.value = null),
  }
}

/** Só para testes: volta ao estado de app recém-aberto. */
export function _resetAtualizacoes() {
  status.value = null
  dadosRemoto.value = null
  app.value = null
  instalandoDados.value = false
  instalandoApp.value = false
  progressoApp.value = 0
  erro.value = null
  avisoAberto.value = false
  avisosExibidos.clear()
  verificacao = null
  verificando = false
}
