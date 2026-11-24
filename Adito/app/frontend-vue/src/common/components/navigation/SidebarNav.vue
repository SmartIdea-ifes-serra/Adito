<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/modules/auth/composables/useAuth'
import { useChatWorkspace } from '@/modules/chat/composables/useChatWorkspace'
import type { Conversation } from '@/modules/chat/types'
import BrandIcon from '@/common/components/BrandIcon.vue'
import ConfirmModal from '@/common/components/feedback/ConfirmModal.vue'
import AtualizacaoDisponivel from '@/common/components/navigation/AtualizacaoDisponivel.vue'
import {
  AreaChart, Loader2, MessageSquare, Moon, PanelLeftClose,
  PanelLeftOpen, Search, Settings, ShieldCheck, SquarePen, Sun, Trash2, X,
} from 'lucide-vue-next'

const props = defineProps<{ isOpen?: boolean }>()
const emit = defineEmits<{ (e: 'update:isOpen', value: boolean): void }>()
const { user } = useAuth()
const { history, isStreaming } = useChatWorkspace()
const { conversations, currentConvId, isHistoryLoading, historyError } = history
const route = useRoute()
const router = useRouter()
const sidebar = ref<HTMLElement | null>(null)
const searchInput = ref<HTMLInputElement | null>(null)
const searchButton = ref<HTMLButtonElement | null>(null)
const isCollapsed = ref(localStorage.getItem('adito_sidebar_collapsed') === 'true')
const isMobile = ref(window.matchMedia('(max-width: 767px)').matches)
const isEffectivelyCollapsed = computed(() => isCollapsed.value && !isMobile.value)
const isSearching = ref(false)
const searchQuery = ref('')
const isDark = ref(document.documentElement.classList.contains('dark'))
const conversationToDelete = ref<Conversation | null>(null)
const deleting = ref(false)
const deleteError = ref('')
let mediaQuery: MediaQueryList | undefined
let themeObserver: MutationObserver | undefined
let previousFocus: HTMLElement | null = null

function normalize(text: string) {
  return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR')
}
const normalizedQuery = computed(() => normalize(searchQuery.value.trim()))
const historyConversations = computed(() => conversations.value.filter(c => c.messages.some(m => m.id !== 'welcome')))
const filteredConversations = computed(() => {
  const query = normalizedQuery.value
  return [...historyConversations.value]
    .filter(c => !query || normalize(c.title).includes(query) || c.messages.some(m => m.id !== 'welcome' && normalize(m.text).includes(query)))
    .sort((a, b) => (Date.parse(b.updatedAt) || 0) - (Date.parse(a.updatedAt) || 0))
})
const menuItems = computed(() => [
  { icon: MessageSquare, label: 'Chat', path: '/chat' },
  { icon: AreaChart, label: 'Meu painel', path: '/meu-dashboard' },
  ...(user.value?.role === 'admin' ? [{ icon: ShieldCheck, label: 'Administração', path: '/admin' }] : []),
  { icon: Settings, label: 'Configurações', path: '/configuracoes' },
])

function closeSidebar() { emit('update:isOpen', false) }
function toggleCollapsed() {
  isCollapsed.value = !isCollapsed.value
  localStorage.setItem('adito_sidebar_collapsed', String(isCollapsed.value))
}
async function openSearch() {
  if (isEffectivelyCollapsed.value) {
    isCollapsed.value = false
    localStorage.setItem('adito_sidebar_collapsed', 'false')
  }
  if (isMobile.value) emit('update:isOpen', true)
  isSearching.value = true
  await nextTick()
  searchInput.value?.focus()
}
async function clearSearch() {
  searchQuery.value = ''
  await nextTick()
  searchInput.value?.focus()
}
async function selectConversation(id: string) {
  if (isStreaming.value) return
  history.setCurrentConvId(id)
  await router.push('/chat')
  closeSidebar()
}
async function newConversation() {
  if (isStreaming.value) return
  history.handleNewConversation()
  searchQuery.value = ''
  isSearching.value = false
  await router.push('/chat')
  closeSidebar()
}
function snippet(conversation: Conversation) {
  return conversation.messages.find(m => m.id !== 'welcome' && normalize(m.text).includes(normalizedQuery.value))?.text || ''
}
async function deleteConversation() {
  if (!conversationToDelete.value || deleting.value || isStreaming.value) return
  deleting.value = true
  try {
    await history.handleDeleteConversation(conversationToDelete.value.id)
    conversationToDelete.value = null
    await nextTick()
    const focusTarget = sidebar.value?.querySelector<HTMLButtonElement>('[aria-current="true"]')
      || sidebar.value?.querySelector<HTMLButtonElement>('[aria-label="Nova conversa"]')
    focusTarget?.focus()
  } catch {
    deleteError.value = 'Não foi possível excluir a conversa. Tente novamente.'
    conversationToDelete.value = null
  } finally {
    deleting.value = false
  }
}
function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}
function onMediaChange(event: MediaQueryListEvent) {
  isMobile.value = event.matches
  if (!event.matches) closeSidebar()
}
function onKeydown(event: KeyboardEvent) {
  if (conversationToDelete.value) return
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    openSearch()
  }
  if (event.key === 'Escape' && !event.defaultPrevented && !conversationToDelete.value) {
    if (isMobile.value && props.isOpen) closeSidebar()
    else if (isSearching.value) {
      searchQuery.value = ''
      isSearching.value = false
      searchButton.value?.focus()
    }
  }
}
function trapMobileFocus(event: KeyboardEvent) {
  if (!isMobile.value || !props.isOpen || event.key !== 'Tab') return
  const elements = sidebar.value?.querySelectorAll<HTMLElement>('button:not(:disabled), a[href], input')
  const focusable = [...(elements || [])].filter(el => el.getClientRects().length)
  const first = focusable[0]
  const last = focusable.at(-1)
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
}
watch(() => props.isOpen, async (open) => {
  if (!isMobile.value) return
  if (open) {
    previousFocus = document.activeElement as HTMLElement
    await nextTick()
    sidebar.value?.querySelector<HTMLButtonElement>('button')?.focus()
  } else previousFocus?.focus()
})
watch(() => route.path, closeSidebar)
onMounted(() => {
  mediaQuery = window.matchMedia('(max-width: 767px)')
  mediaQuery.addEventListener('change', onMediaChange)
  document.addEventListener('keydown', onKeydown)
  themeObserver = new MutationObserver(() => { isDark.value = document.documentElement.classList.contains('dark') })
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
})
onBeforeUnmount(() => {
  mediaQuery?.removeEventListener('change', onMediaChange)
  document.removeEventListener('keydown', onKeydown)
  themeObserver?.disconnect()
})
</script>

<template>
  <aside
    id="adito-sidebar"
    ref="sidebar"
    aria-label="Barra lateral"
    :inert="isMobile && !isOpen"
    :class="['adito-sidebar', { 'is-collapsed': isEffectivelyCollapsed, 'is-open': isOpen }]"
    @keydown="trapMobileFocus"
  >
    <div class="sidebar-header">
      <button v-if="isEffectivelyCollapsed" type="button" class="brand-expand icon-button" aria-label="Expandir menu" title="Expandir menu" @click="toggleCollapsed">
        <BrandIcon class="brand-symbol h-8 w-8" />
        <PanelLeftOpen class="expand-symbol h-5 w-5" />
      </button>
      <template v-else>
        <div class="flex min-w-0 items-center gap-2.5">
          <BrandIcon class="h-8 w-8" />
          <h1 class="adito-wordmark text-[27px] leading-none">Adito</h1>
        </div>
        <div class="flex items-center gap-0.5">
          <button ref="searchButton" type="button" class="icon-button" aria-label="Pesquisar conversas" title="Pesquisar conversas (Ctrl+K)" :aria-expanded="isSearching" @click="openSearch">
            <Search class="h-[19px] w-[19px]" />
          </button>
          <button v-if="!isMobile" type="button" class="icon-button" aria-label="Recolher menu" title="Recolher menu" @click="toggleCollapsed"><PanelLeftClose class="h-[18px] w-[18px]" /></button>
          <button v-else type="button" class="icon-button" aria-label="Fechar menu de navegação" @click="closeSidebar"><X class="h-5 w-5" /></button>
        </div>
      </template>
    </div>

    <div class="sidebar-actions">
      <button type="button" class="nav-item new-conversation" aria-label="Nova conversa" :title="isEffectivelyCollapsed ? 'Nova conversa' : undefined" :disabled="isStreaming" @click="newConversation">
        <SquarePen class="h-5 w-5 shrink-0" />
        <span v-if="!isEffectivelyCollapsed">Nova conversa</span>
      </button>
      <button v-if="isEffectivelyCollapsed" ref="searchButton" type="button" class="nav-item" aria-label="Pesquisar conversas" title="Pesquisar conversas (Ctrl+K)" @click="openSearch"><Search class="h-5 w-5" /></button>
      <nav aria-label="Navegação principal" class="mt-2 space-y-0.5">
        <RouterLink v-for="item in menuItems" :key="item.path" :to="item.path" :aria-label="item.label" :title="isEffectivelyCollapsed ? item.label : undefined" :class="['nav-item', { 'nav-active': route.path === item.path }]" @click="closeSidebar">
          <component :is="item.icon" class="h-5 w-5 shrink-0" />
          <span v-if="!isEffectivelyCollapsed">{{ item.label }}</span>
        </RouterLink>
      </nav>
    </div>

    <section v-if="!isEffectivelyCollapsed" class="history-section" aria-label="Histórico de conversas">
      <div class="history-heading"><h2>Conversas</h2><span v-if="!isHistoryLoading">{{ historyConversations.length }}</span></div>
      <div v-if="isSearching" class="search-field">
        <Search class="pointer-events-none h-4 w-4 shrink-0" />
        <input ref="searchInput" v-model="searchQuery" type="search" aria-label="Pesquisar conversas" placeholder="Pesquisar conversas" autocomplete="off" />
        <button v-if="searchQuery" type="button" class="icon-button h-7! w-7! shrink-0" aria-label="Limpar pesquisa" @click="clearSearch"><X class="h-3.5 w-3.5" /></button>
      </div>
      <p v-if="normalizedQuery" class="search-count" role="status">{{ filteredConversations.length }} {{ filteredConversations.length === 1 ? 'conversa encontrada' : 'conversas encontradas' }}</p>
      <div class="conversation-scroll" :aria-busy="isHistoryLoading">
        <p v-if="isHistoryLoading" class="history-empty" role="status"><Loader2 class="h-4 w-4 animate-spin" />Carregando conversas…</p>
        <div v-if="historyError" class="history-empty flex-col! items-start!" role="status">
          <span>{{ historyError }}</span>
          <button type="button" class="underline underline-offset-4" @click="history.syncFromBackend()">Tentar novamente</button>
        </div>
        <template v-if="!isHistoryLoading">
          <p v-if="!filteredConversations.length" class="history-empty">{{ normalizedQuery ? 'Nenhuma conversa encontrada' : 'Suas conversas ficam aqui.' }}</p>
          <ul v-else class="space-y-0.5">
            <li v-for="conversation in filteredConversations" :key="conversation.id" :class="['conversation-item group', { 'conversation-active': route.path === '/chat' && conversation.id === currentConvId }]">
              <button type="button" class="conversation-select" :aria-current="route.path === '/chat' && conversation.id === currentConvId ? 'true' : undefined" :disabled="isStreaming" :title="conversation.title" @click="selectConversation(conversation.id)">
                <span class="block truncate">{{ conversation.title }}</span>
                <span v-if="normalizedQuery && snippet(conversation)" class="conversation-snippet">{{ snippet(conversation) }}</span>
              </button>
              <button type="button" class="conversation-delete" :aria-label="`Excluir conversa ${conversation.title}`" title="Excluir conversa" :disabled="isStreaming || deleting" @click="deleteError = ''; conversationToDelete = conversation"><Trash2 class="h-3.5 w-3.5" /></button>
            </li>
          </ul>
        </template>
      </div>
      <p v-if="deleteError" role="alert" class="px-3 py-2 text-xs text-red-700 dark:text-red-300">{{ deleteError }}</p>
    </section>
    <div v-else class="flex-1" />

    <footer class="sidebar-footer">
      <AtualizacaoDisponivel :collapsed="isEffectivelyCollapsed" />
      <button
        type="button"
        :class="['theme-toggle flex w-full items-center gap-2.5 rounded-md border border-white/[0.12] bg-white/[0.06] text-[10px] font-medium uppercase tracking-[0.1em] text-white/80 transition-colors hover:bg-white/[0.12] hover:text-white', isEffectivelyCollapsed ? 'justify-center p-3' : 'px-4 py-2.5']"
        :aria-label="isDark ? 'Modo Claro' : 'Modo Escuro'"
        :title="isDark ? 'Modo Claro' : 'Modo Escuro'"
        @click="toggleTheme"
      >
        <Sun v-if="isDark" class="h-4 w-4 text-white/85" />
        <Moon v-else class="h-4 w-4 text-white/85" />
        <span v-if="!isEffectivelyCollapsed">{{ isDark ? 'Modo Claro' : 'Modo Escuro' }}</span>
      </button>
      <p class="sidebar-signature">Powered by <span>LEDS &amp; SmartIdea</span></p>
    </footer>
  </aside>
  <ConfirmModal :is-open="!!conversationToDelete" :loading="deleting" title="Excluir conversa" :message="`Excluir a conversa “${conversationToDelete?.title || ''}”? Esta ação não pode ser desfeita.`" confirm-text="Excluir conversa" cancel-text="Cancelar" @confirm="deleteConversation" @close="conversationToDelete = null" />
</template>

<style scoped>
.adito-sidebar { --sidebar-expanded-width: 352px; --sidebar-background: var(--brand-dark); --sidebar-new: rgba(255,255,255,.06); --sidebar-hover: rgba(255,255,255,.06); --sidebar-active: rgba(255,255,255,.12); --sidebar-active-text: #ffffff; --sidebar-active-icon: #ffffff; --sidebar-muted: rgba(255,255,255,.60); --sidebar-border: rgba(255,255,255,.12); position: fixed; inset: 0 auto 0 0; z-index: 60; display: flex; height: 100dvh; width: min(var(--sidebar-expanded-width), calc(100vw - 28px)); flex-shrink: 0; flex-direction: column; background: var(--sidebar-background); color: #ffffff; border-right: 1px solid rgba(255,255,255,.08); box-shadow: rgba(0,0,0,.3) 0 0 0 1px; transform: translateX(-100%); transition: width 200ms ease, transform 200ms ease; }
:global(.dark .adito-sidebar) { --sidebar-active: rgba(43,122,66,.25); --sidebar-active-icon: #68d388; }
.adito-sidebar.is-open { transform: translateX(0); }
.sidebar-header { display: flex; align-items: center; justify-content: space-between; min-height: 80px; padding: 18px 18px 14px 22px; }
.sidebar-header h1 { color: #ffffff; }
.nav-active > svg { color: var(--sidebar-active-icon); }
.icon-button { display: inline-flex; height: 34px; width: 34px; align-items: center; justify-content: center; border-radius: 9px; color: rgba(255,255,255,.75); transition: background 150ms, color 150ms; }
.icon-button:hover { background: var(--sidebar-hover); color: #ffffff; }
.sidebar-actions { padding: 0 12px; }
.nav-item { display: flex; min-height: 42px; width: 100%; align-items: center; gap: 12px; border-radius: 10px; padding: 10px 13px; color: rgba(255,255,255,.75); font-size: 14px; line-height: 20px; transition: background 150ms, color 150ms; }
.nav-item:hover { background: var(--sidebar-hover); color: #ffffff; }
.nav-item.nav-active { background: var(--sidebar-active); color: var(--sidebar-active-text); font-weight: 500; }
.new-conversation { background: var(--sidebar-new); color: #ffffff; font-weight: 500; border-radius: 24px; }
.new-conversation:hover { background: var(--sidebar-hover); }
.history-section { display: flex; min-height: 0; flex: 1; flex-direction: column; padding: 23px 10px 8px; }
.history-heading { display: flex; align-items: center; justify-content: space-between; padding: 0 15px 11px; color: var(--sidebar-muted); }
.history-heading h2 { color: inherit; font-size: 12px; font-weight: 500; letter-spacing: .01em; }
.history-heading > span { font-size: 10px; font-variant-numeric: tabular-nums; }
.search-field { display: flex; align-items: center; gap: 8px; min-height: 40px; margin: 0 3px 9px; padding: 0 10px; border: 1px solid var(--sidebar-border); border-radius: 10px; background: rgba(255,255,255,.06); color: var(--sidebar-muted); }
.search-field:focus-within { outline: 2px solid rgba(255,255,255,.65); outline-offset: 1px; }
.search-field input { min-width: 0; width: 100%; padding: 9px 0; outline: none; color: #ffffff; font-size: 12px; }
.search-field input::placeholder { color: var(--sidebar-muted); }
.search-field input::-webkit-search-cancel-button { display: none; }
.search-count { padding: 0 8px 9px; color: var(--sidebar-muted); font-size: 11px; }
.conversation-scroll { min-height: 0; flex: 1; overflow-y: auto; scrollbar-width: thin; scrollbar-color: rgba(255,255,255,.25) transparent; }
.conversation-item { position: relative; display: flex; align-items: center; border-radius: 9px; }
.conversation-item:hover, .conversation-item:focus-within { background: var(--sidebar-hover); }
.conversation-active { background: var(--sidebar-active); color: var(--sidebar-active-text); }
.conversation-select { min-width: 0; width: 100%; padding: 10px 34px 10px 15px; text-align: left; font-size: 13px; line-height: 18px; border-radius: 9px; }
.conversation-active .conversation-select { font-weight: 500; }
.conversation-snippet { display: block; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; margin-top: 4px; font-size: 11px; font-weight: 400; color: var(--sidebar-muted); }
.conversation-delete { position: absolute; right: 5px; display: flex; height: 28px; width: 28px; align-items: center; justify-content: center; border-radius: 7px; color: var(--sidebar-muted); opacity: 0; }
.conversation-item:hover .conversation-delete, .conversation-item:focus-within .conversation-delete { opacity: 1; }
.conversation-delete:hover { background: rgba(255,255,255,.06); color: var(--brand-accent-danger); }
.history-empty { display: flex; align-items: center; gap: 8px; padding: 10px 15px; color: var(--sidebar-muted); font-size: 12px; line-height: 1.6; }
.sidebar-footer { background: rgba(0,0,0,.15); border-top: 1px solid rgba(255,255,255,.10); display: flex; flex-direction: column; gap: 8px; padding: 10px 12px 16px; }
.sidebar-signature { margin: 4px 5px 0; padding-top: 12px; border-top: 1px solid rgba(255,255,255,.06); color: rgba(255,255,255,.65); text-align: center; font-size: 10px; line-height: 1.6; }
.sidebar-signature span { color: rgba(255,255,255,.8); font-weight: 500; }
button:disabled { cursor: wait; opacity: .5; }
button, a { -webkit-tap-highlight-color: transparent; }
button:focus-visible, a:focus-visible { outline: 2px solid rgba(255,255,255,.65); outline-offset: 2px; }
.brand-expand { position: relative; }
.expand-symbol { display: none; }
.brand-expand:hover .brand-symbol { visibility: hidden; }
.brand-expand:hover .expand-symbol { position: absolute; display: block; }
@media (min-width: 768px) {
  .adito-sidebar { position: relative; width: var(--sidebar-expanded-width); transform: none; }
  .adito-sidebar.is-collapsed { width: 76px; }
  .is-collapsed .sidebar-header { justify-content: center; padding: 23px 0; }
  .is-collapsed .sidebar-actions { padding: 0 12px; }
  .is-collapsed .nav-item { justify-content: center; width: 44px; padding: 11px; margin-left: auto; margin-right: auto; }
  .is-collapsed .sidebar-footer { align-items: center; padding: 10px 10px 16px; }
  .is-collapsed .theme-toggle { width: 44px; }
  .is-collapsed .sidebar-signature { margin: 0; width: 44px; font-size: 8px; line-height: 1.5; }
  .is-collapsed .sidebar-signature span { display: block; }
}
@media (hover: none) { .conversation-delete { opacity: 1; } }
@media (prefers-reduced-motion: reduce) { .adito-sidebar { transition: none; } }
</style>
