<script setup lang="ts">
import { ref } from 'vue'
import {
  MessageSquare,
  FlaskConical,
  Handshake,
  Users,
  BookOpen,
  Award,
  GraduationCap,
  TrendingUp,
  Package,
  BarChart2,
  UserCheck,
  Percent,
  ArrowRight
} from 'lucide-vue-next'
import brandIcon from '@/common/assets/brand-icon.png'
import type { ChatMessage, Conversation } from '@/modules/chat/types'
import ChatMessageBubble from '@/modules/chat/components/ChatMessageBubble.vue'

interface StarterCategory {
  key: string
  label: string
  subtitle?: string
  questions: string[]
}

const props = defineProps<{
  messages: ChatMessage[]
  currentConversation?: Conversation
  loading: boolean
  healthOnline: boolean | null
  starterCategories: StarterCategory[]
}>()

const emit = defineEmits<{
  (e: 'open-conversations'): void
  (e: 'toggle-sql', id: string): void
  (e: 'pin', message: ChatMessage): void
  (e: 'suggest', question: string): void
}>()

const categoryIcons: Record<string, unknown> = {
  pesquisa: FlaskConical,
  extensao: Handshake,
  grupos: Users,
  producao: BookOpen,
  editais: Award,
  pesquisadores: GraduationCap,
  receita: TrendingUp,
  produtos: Package,
  clientes: Users,
  canais: BarChart2,
  vendedores: UserCheck,
  margens: Percent,
}

const selected = ref<string | null>(null)

const selectedCategory = () =>
  props.starterCategories.find(c => c.key === selected.value) ?? null

function select(key: string) {
  selected.value = selected.value === key ? null : key
}
</script>

<template>
  <div class="relative flex h-full flex-1 flex-col overflow-hidden transition-colors bg-transparent">
    <div class="lg:hidden sticky top-0 z-20 flex items-center justify-between border-b border-border-subtle bg-surface/92 px-4 py-3 backdrop-blur-md shadow-sm">
      <div class="flex items-center gap-2 overflow-hidden">
        <img :src="brandIcon" class="h-4 w-4 shrink-0" />
        <h2 class="truncate text-xs font-semibold text-primary">{{ currentConversation?.title }}</h2>
      </div>
      <button
        class="flex shrink-0 items-center gap-1.5 rounded-md border border-accent/20 bg-accent/8 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-accent transition-colors hover:bg-accent/14"
        @click="emit('open-conversations')"
      >
        <MessageSquare class="h-3 w-3" />
        Conversas
      </button>
    </div>

    <div class="flex-1 overflow-y-auto p-4 min-h-[300px] bg-transparent md:p-6 scroll-fade-mask">
      <div
        v-if="messages.length === 1 && messages[0]?.id === 'welcome' && !loading"
        class="mx-auto flex h-full max-w-xl flex-col items-center justify-center gap-6 text-center"
      >
        <div class="flex flex-col items-center gap-3">
          <img :src="brandIcon" class="h-12 w-12 opacity-90" />
          <div>
            <h4 class="text-lg font-semibold text-text-primary">Como posso ajudar?</h4>
            <p class="mt-1 text-sm text-text-secondary">Escolha uma área institucional do IFES ou digite sua pergunta.</p>
          </div>
        </div>

        <!-- Category grid -->
        <div class="w-full grid grid-cols-2 sm:grid-cols-3 gap-3">
          <button
            v-for="category in starterCategories"
            :key="category.key"
            :class="[
              'group flex flex-col items-center gap-2 rounded-xl border px-3.5 py-4 transition-all duration-200',
              selected === category.key
                ? 'border-[var(--brand-primary)] bg-[var(--accent-light)] text-[var(--brand-primary)] shadow-sm -translate-y-0.5'
                : 'border-[var(--border-subtle)] bg-[#FFFFFF] dark:bg-[var(--bg-surface)] text-[var(--neutral-dark)] hover:-translate-y-0.5 hover:border-[var(--brand-primary)]/45 hover:shadow-[var(--shadow-card-hover)]'
            ]"
            @click="select(category.key)"
          >
            <div
              :class="[
                'flex h-9 w-9 items-center justify-center rounded-full border transition-colors duration-200',
                selected === category.key
                  ? 'border-[var(--brand-primary)]/30 bg-[var(--brand-primary)]/15'
                  : 'border-[var(--brand-primary)]/12 bg-[var(--brand-primary)]/8 group-hover:border-[var(--brand-primary)]/25 group-hover:bg-[var(--brand-primary)]/12'
              ]"
            >
              <component
                :is="categoryIcons[category.key]"
                :class="[
                  'h-4.5 w-4.5 transition-colors duration-200',
                  selected === category.key
                    ? 'text-[var(--brand-primary)] dark:text-[#68d388]'
                    : 'text-text-secondary group-hover:text-[var(--brand-primary)] dark:group-hover:text-[#68d388]'
                ]"
                stroke-width="1.75"
              />
            </div>
            <div class="flex flex-col items-center gap-0.5">
              <span class="text-xs font-semibold leading-tight">{{ category.label }}</span>
              <span
                v-if="category.subtitle"
                class="text-[10px] text-text-muted leading-tight"
              >
                {{ category.subtitle }}
              </span>
            </div>
          </button>
        </div>

        <!-- Questions panel -->
        <transition
          enter-active-class="transition-all duration-200 ease-out"
          enter-from-class="opacity-0 translate-y-2"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition-all duration-150 ease-in"
          leave-from-class="opacity-100 translate-y-0"
          leave-to-class="opacity-0 translate-y-2"
        >
          <div
            v-if="selectedCategory()"
            class="w-full rounded-xl border border-[var(--border-subtle)] bg-[#FFFFFF] dark:bg-[var(--bg-surface)] overflow-hidden shadow-xs"
          >
            <div class="flex items-center justify-between border-b border-[var(--border-subtle)] bg-[var(--bg-app)]/60 px-4 py-3 text-left">
              <span class="text-xs font-semibold uppercase tracking-widest text-[var(--brand-primary)] dark:text-[#68d388]">
                {{ selectedCategory()?.label }}
              </span>
              <span v-if="selectedCategory()?.subtitle" class="text-[11px] text-text-muted">
                {{ selectedCategory()?.subtitle }}
              </span>
            </div>
            <div class="divide-y divide-[var(--border-subtle)]">
              <button
                v-for="question in selectedCategory()?.questions"
                :key="question"
                class="group flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition-colors hover:bg-[var(--accent-light)]/60"
                @click="emit('suggest', question)"
              >
                <span class="text-sm text-text-secondary group-hover:text-[var(--neutral-dark)] transition-colors">
                  {{ question }}
                </span>
                <ArrowRight class="h-3.5 w-3.5 shrink-0 text-[var(--brand-primary)] opacity-0 group-hover:opacity-100 transition-opacity" stroke-width="2" />
              </button>
            </div>
          </div>
        </transition>
      </div>

      <div class="mx-auto flex w-full max-w-[980px] flex-col space-y-5 md:space-y-6">
        <ChatMessageBubble
          v-for="message in (messages.length === 1 && messages[0]?.id === 'welcome' && !loading ? [] : messages)"
          :key="message.id"
          :message="message"
          @toggle-sql="emit('toggle-sql', $event)"
          @pin="emit('pin', $event)"
          @suggest="emit('suggest', $event)"
        />
      </div>

      <div id="chat-bottom-anchor" />
    </div>
  </div>
</template>

<style scoped>
.scroll-fade-mask {
  mask-image: linear-gradient(
    to bottom,
    transparent 0%,
    black 40px,
    black calc(100% - 40px),
    transparent 100%
  );
  -webkit-mask-image: linear-gradient(
    to bottom,
    transparent 0%,
    black 40px,
    black calc(100% - 40px),
    transparent 100%
  );
}
</style>
