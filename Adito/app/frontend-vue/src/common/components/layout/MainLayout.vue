<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import SidebarNav from '@/common/components/navigation/SidebarNav.vue'
import { Menu } from 'lucide-vue-next'

import BrandIcon from '@/common/components/BrandIcon.vue'
import PrimeiroUsoDados from '@/common/components/feedback/PrimeiroUsoDados.vue'
import { useAtualizacoes } from '@/common/composables/useAtualizacoes'
import { provideChatWorkspace } from '@/modules/chat/composables/useChatWorkspace'

const isSidebarOpen = ref(false)
provideChatWorkspace()

const { precisaPrimeiraCarga, verificar, instalandoApp, instalandoDados } = useAtualizacoes()
const intervaloVerificacao = 15 * 60 * 1000
let ultimaVerificacao = Date.now()

function verificarAoRetornar() {
  if (Date.now() - ultimaVerificacao < intervaloVerificacao) return
  verificarAoReconectar()
}

function verificarAoReconectar() {
  if (instalandoApp.value || instalandoDados.value) return
  ultimaVerificacao = Date.now()
  verificar({ forcar: true })
}

onMounted(() => {
  verificar()
  window.addEventListener('focus', verificarAoRetornar)
  window.addEventListener('online', verificarAoReconectar)
})
onBeforeUnmount(() => {
  window.removeEventListener('focus', verificarAoRetornar)
  window.removeEventListener('online', verificarAoReconectar)
})

function toggleSidebar() {
  isSidebarOpen.value = !isSidebarOpen.value
}
</script>

<template>
  <div class="flex h-dvh overflow-hidden bg-primary text-primary">
    <header class="md:hidden fixed top-0 left-0 right-0 z-50 flex h-16 items-center justify-between border-b border-border-subtle bg-surface/95 px-5 backdrop-blur-md">
      <div class="flex items-center gap-2">
        <BrandIcon class="h-8 w-8" />
        <h1 class="text-xl font-semibold tracking-[-0.04em] text-primary">Adito</h1>
      </div>

      <button
        aria-label="Abrir menu de navegação"
        aria-controls="adito-sidebar"
        :aria-expanded="isSidebarOpen"
        @click="toggleSidebar"
        class="rounded-lg border border-border-subtle bg-surface-elevated/90 p-2.5 text-text-secondary transition-colors hover:bg-surface-elevated hover:text-primary"
      >
        <Menu class="h-6 w-6" />
      </button>
    </header>

    <SidebarNav v-model:isOpen="isSidebarOpen" />

    <main class="min-w-0 flex-1 overflow-y-auto pt-16 md:pt-0">
      <RouterView />
    </main>

    <div
      v-if="isSidebarOpen"
      class="md:hidden fixed inset-0 z-[55] bg-black/45 backdrop-blur-sm transition-opacity duration-300"
      @click="isSidebarOpen = false"
    />

    <PrimeiroUsoDados v-if="precisaPrimeiraCarga" />
  </div>
</template>
