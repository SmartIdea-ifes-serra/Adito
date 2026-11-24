<script setup lang="ts">
import { computed, nextTick, ref, useId, watch } from 'vue'
import { ArrowRight, Database, Download, Loader2, X } from 'lucide-vue-next'
import { useAtualizacoes } from '@/common/composables/useAtualizacoes'

const props = defineProps<{ collapsed?: boolean }>()
const {
  app, dadosNovos, temAtualizacao, precisaPrimeiraCarga, avisoAberto,
  instalandoApp, instalandoDados, progressoApp, erro,
  instalarApp, instalarDados, abrirAviso, adiarAviso,
} = useAtualizacoes()

const chave = ref('')
const gatilho = ref<HTMLButtonElement | null>(null)
const painel = ref<HTMLElement | null>(null)
const botaoDepois = ref<HTMLButtonElement | null>(null)
const descricaoId = useId()
const ocupado = computed(() => instalandoApp.value || instalandoDados.value)
const mostrar = computed(() => avisoAberto.value && temAtualizacao.value && !precisaPrimeiraCarga.value)
let focoAnterior: HTMLElement | null = null

function tamanhoMb(bytes: number) {
  return `${(bytes / 1024 / 1024).toFixed(1).replace('.', ',')} MB`
}

async function baixarAgora() {
  if (ocupado.value || (dadosNovos.value?.precisa_chave && !chave.value.trim())) return
  // Os dados são atualizados antes do app, pois a instalação do app reinicia o Adito.
  if (dadosNovos.value) {
    const ok = await instalarDados(dadosNovos.value.precisa_chave ? chave.value : undefined)
    if (!ok) return
    chave.value = ''
  }
  if (app.value) await instalarApp()
}

function focoVisivel(elemento: HTMLElement | null): elemento is HTMLElement {
  return !!elemento?.isConnected && elemento !== document.body && elemento !== document.documentElement && !elemento.closest('[inert]') &&
    !elemento.matches(':disabled') && elemento.getClientRects().length > 0
}

watch(mostrar, async (aberto, estavaAberto) => {
  if (aberto) {
    focoAnterior = document.activeElement instanceof HTMLElement ? document.activeElement : null
    await nextTick()
    botaoDepois.value?.focus()
  } else if (estavaAberto) {
    if (!focoAnterior) return
    await nextTick()
    const candidatos = [document.querySelector<HTMLElement>('[data-testid="primeiro-uso-dados"] input'), focoAnterior, gatilho.value,
      document.querySelector<HTMLElement>('button[aria-controls="adito-sidebar"]'),
      document.querySelector<HTMLElement>('main textarea, main input, main button, main a[href]')]
    candidatos.find(focoVisivel)?.focus()
  }
}, { immediate: true })

watch(ocupado, async (carregando) => {
  if (!mostrar.value) return
  await nextTick()
  if (carregando) painel.value?.focus()
  else if (document.activeElement === painel.value) botaoDepois.value?.focus()
})

function onKeydown(event: KeyboardEvent) {
  // Mantém os atalhos da navegação fora da confirmação central.
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    event.stopPropagation()
    return
  }
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    adiarAviso()
    return
  }
  if (event.key !== 'Tab') return
  const elementos = [...(painel.value?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), a[href]') || [])]
    .filter(focoVisivel)
  const primeiro = elementos[0]
  const ultimo = elementos.at(-1)
  if (!primeiro) {
    event.preventDefault()
    painel.value?.focus()
  } else if (event.shiftKey && (document.activeElement === primeiro || document.activeElement === painel.value)) {
    event.preventDefault()
    ultimo?.focus()
  } else if (!event.shiftKey && (document.activeElement === ultimo || document.activeElement === painel.value)) {
    event.preventDefault()
    primeiro.focus()
  }
}
</script>

<template>
  <div v-if="temAtualizacao && !precisaPrimeiraCarga" data-testid="atualizacao-disponivel">
    <button
      ref="gatilho"
      type="button"
      aria-label="Atualização disponível"
      aria-haspopup="dialog"
      :aria-expanded="mostrar"
      :title="props.collapsed ? 'Atualização disponível' : undefined"
      :class="['flex w-full items-center gap-2 rounded-md border border-white/[0.14] bg-white/[0.08] text-[13px] font-medium text-white transition-colors hover:bg-white/[0.14]', props.collapsed ? 'justify-center p-3' : 'px-3.5 py-2.5']"
      @click="abrirAviso"
    >
      <span class="h-2 w-2 shrink-0 rounded-full bg-[#68d388]" aria-hidden="true" />
      <template v-if="!props.collapsed"><span class="flex-1 text-left">Atualização disponível</span><ArrowRight class="h-4 w-4 text-white/70" /></template>
    </button>
  </div>

  <Teleport to="body">
    <div v-if="mostrar" class="fixed inset-0 z-[90] flex items-center justify-center bg-black/50 p-4" @keydown="onKeydown" @click.self="adiarAviso">
      <section
        ref="painel"
        role="dialog"
        aria-modal="true"
        aria-label="Atualizações do Adito"
        :aria-describedby="descricaoId"
        :aria-busy="ocupado"
        tabindex="-1"
        class="relative max-h-[calc(100dvh-2rem)] w-full max-w-md overflow-y-auto rounded-2xl border border-border-subtle bg-surface p-6 text-sm text-text-primary shadow-premium outline-none"
      >
        <button type="button" aria-label="Fechar atualização" :disabled="ocupado" class="absolute right-4 top-4 rounded-lg p-1.5 text-text-muted transition-colors hover:bg-surface-elevated disabled:opacity-40" @click="adiarAviso"><X class="h-4 w-4" /></button>
        <div class="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-accent"><Download class="h-5 w-5" /></div>
        <h2 class="pr-6 text-lg font-semibold text-text-primary">Nova atualização disponível</h2>
        <p :id="descricaoId" class="mt-2 leading-relaxed text-text-secondary">Há novidades para o Adito. Você pode baixar agora ou continuar e atualizar mais tarde.</p>

        <div class="my-5 space-y-3">
          <div v-if="app" class="rounded-xl border border-border-subtle p-4">
            <div class="flex items-center gap-2 font-medium"><Download class="h-4 w-4 text-accent" />Nova versão do Adito</div>
            <p class="mt-1.5 text-xs leading-relaxed text-text-secondary">Versão {{ app.version }}. O download instala a atualização e reinicia o aplicativo. Suas conversas e painéis são preservados.</p>
          </div>
          <div v-if="dadosNovos" class="rounded-xl border border-border-subtle p-4">
            <div class="flex items-center gap-2 font-medium"><Database class="h-4 w-4 text-accent" />Dados novos</div>
            <p class="mt-1.5 text-xs leading-relaxed text-text-secondary">Versão {{ dadosNovos.versao }} · {{ tamanhoMb(dadosNovos.tamanho) }}. Atualiza a base de pesquisa e extensão.</p>
            <template v-if="dadosNovos.precisa_chave">
              <p class="mt-3 text-xs leading-relaxed text-text-secondary">A chave dos dados mudou. Informe a nova chave para baixar esta versão.</p>
              <input v-model="chave" type="password" aria-label="Nova chave dos dados" autocomplete="off" spellcheck="false" :disabled="ocupado" placeholder="Nova chave dos dados" class="mt-2 w-full rounded-lg border border-border-standard bg-surface-elevated px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-2 focus:outline-accent disabled:opacity-50" @keydown.enter.prevent="baixarAgora" />
            </template>
          </div>
        </div>

        <div v-if="ocupado" class="mb-4" role="status" aria-live="polite">
          <p class="flex items-center gap-2 text-xs text-text-secondary"><Loader2 class="h-4 w-4 animate-spin text-accent" />{{ instalandoDados ? 'Baixando e conferindo os dados…' : progressoApp < 1 ? `Baixando o aplicativo… ${Math.round(progressoApp * 100)}%` : 'Instalando atualização e reiniciando…' }}</p>
          <div v-if="instalandoApp" role="progressbar" aria-label="Download da atualização" :aria-valuenow="Math.round(progressoApp * 100)" aria-valuemin="0" aria-valuemax="100" class="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-elevated"><div class="h-full bg-accent transition-[width]" :style="{ width: `${Math.round(progressoApp * 100)}%` }" /></div>
        </div>
        <p v-if="erro" role="alert" class="mb-4 text-xs leading-relaxed text-red-700 dark:text-red-300">{{ erro }}</p>
        <div class="flex flex-col-reverse gap-2 sm:flex-row">
          <button ref="botaoDepois" type="button" class="btn-secondary flex-1 disabled:opacity-50" :disabled="ocupado" @click="adiarAviso">Deixar para depois</button>
          <button type="button" class="btn-primary flex-1 disabled:opacity-50" :disabled="ocupado || (dadosNovos?.precisa_chave && !chave.trim())" @click="baixarAgora">Baixar agora</button>
        </div>
      </section>
    </div>
  </Teleport>
</template>
