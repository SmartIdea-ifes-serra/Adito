<script setup lang="ts">
import { AlertTriangle, X } from 'lucide-vue-next'
import { nextTick, ref, useId, watch } from 'vue'

interface Props {
  isOpen: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  loading?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits(['confirm', 'close'])
const dialog = ref<HTMLElement | null>(null)
const titleId = useId()
const messageId = useId()
let previousFocus: HTMLElement | null = null

watch(() => props.isOpen, async (open) => {
  if (open) {
    previousFocus = document.activeElement as HTMLElement
    await nextTick()
    dialog.value?.querySelector<HTMLButtonElement>('[data-cancel]')?.focus()
  } else if (previousFocus?.isConnected) previousFocus.focus()
}, { immediate: true })

watch(() => props.loading, (loading) => { if (loading) dialog.value?.focus() })

function close() { if (!props.loading) emit('close') }
function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    close()
  }
  if (event.key !== 'Tab') return
  const buttons = dialog.value?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)')
  const first = buttons?.[0]
  const last = buttons?.[buttons.length - 1]
  if (!first) { event.preventDefault(); dialog.value?.focus(); return }
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
}
</script>

<template>
  <Teleport to="body">
  <transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div v-if="isOpen" class="fixed inset-0 z-[80] flex items-center justify-center p-4" @keydown="onKeydown">
      <!-- Backdrop — sem blur excessivo -->
      <div
        class="absolute inset-0 bg-black/50"
        @click="close"
      />

      <!-- Modal Content — dinâmico claro/escuro e largura adequada -->
      <div
        ref="dialog"
        role="dialog"
        aria-modal="true"
        tabindex="-1"
        :aria-busy="loading || undefined"
        :aria-labelledby="titleId"
        :aria-describedby="messageId"
        v-motion="{
          initial: { scale: 0.97, opacity: 0, y: 8 },
          enter: { scale: 1, opacity: 1, y: 0, transition: { duration: 180 } }
        }"
        class="relative w-full max-w-sm overflow-hidden rounded-xl border border-border-subtle bg-surface shadow-[rgba(0,0,0,0.12)_0px_0px_0px_1px,rgba(0,0,0,0.08)_0px_8px_24px] dark:border-white/[0.08]"
      >
        <button
          type="button"
          aria-label="Fechar confirmação"
          :disabled="loading"
          class="absolute right-3 top-3 rounded-md p-1.5 text-text-muted transition-colors hover:bg-surface-elevated hover:text-text-primary"
          @click="close"
        >
          <X class="h-4 w-4" />
        </button>

        <!-- Header -->
        <div class="border-b border-border-subtle p-5 pr-12 dark:border-white/[0.06]">
          <div class="mb-3 flex h-10 w-10 items-center justify-center rounded-lg border border-[#C50707]/25 bg-[#C50707]/10 dark:border-red-400/30 dark:bg-red-500/15">
            <AlertTriangle class="h-5 w-5 text-[#C50707] dark:text-red-300" />
          </div>
          <h3 :id="titleId" class="text-base font-semibold tracking-tight text-primary">
            {{ title }}
          </h3>
          <p :id="messageId" class="mt-1.5 text-sm leading-relaxed text-text-secondary">
            {{ message }}
          </p>
        </div>

        <!-- Actions -->
        <div class="flex gap-2 p-4">
          <button
            type="button"
            data-cancel
            :disabled="loading"
            class="btn-secondary flex-1 py-2 text-sm font-medium cursor-pointer"
            @click="close"
          >
            {{ cancelText || 'Cancelar' }}
          </button>
          <button
            type="button"
            :disabled="loading"
            class="flex flex-1 items-center justify-center rounded-lg bg-[#C50707] py-2 text-sm font-semibold text-white transition-colors hover:bg-[#9E0505] dark:bg-red-600 dark:hover:bg-red-500 cursor-pointer"
            @click="emit('confirm')"
          >
            {{ loading ? 'Excluindo…' : confirmText || 'Excluir' }}
          </button>
        </div>
      </div>
    </div>
  </transition>
  </Teleport>
</template>
