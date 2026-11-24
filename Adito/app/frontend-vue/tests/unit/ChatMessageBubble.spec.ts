import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ChatMessageBubble from '@/modules/chat/components/ChatMessageBubble.vue'
import type { ChatMessage } from '@/modules/chat/types'

function makeLoadingMessage(overrides: Partial<ChatMessage> = {}): ChatMessage {
  return {
    id: 'draft-1',
    type: 'ai',
    text: '',
    timestamp: '2026-11-24T15:00:00.000Z',
    isLoading: true,
    ...overrides,
  }
}

describe('modules/chat/components/ChatMessageBubble (loading)', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('exibe "Analisando sua pergunta..." e elementos de animação ao iniciar carregamento', () => {
    const wrapper = mount(ChatMessageBubble, {
      props: { message: makeLoadingMessage() },
      global: { stubs: { VueApexCharts: true } },
    })

    const statusRegion = wrapper.find('[role="status"]')
    expect(statusRegion.exists()).toBe(true)
    expect(statusRegion.text()).toContain('Analisando sua pergunta...')
    expect(wrapper.findAll('.status-dot')).toHaveLength(3)
    expect(wrapper.find('.loading-progress-bar').exists()).toBe(true)
    expect(wrapper.find('.loading-brand-ring').exists()).toBe(true)
    expect(wrapper.findAll('.skeleton-line')).toHaveLength(3)

    wrapper.unmount()
  })

  it('avança progressivamente pelas mensagens de status enquanto processa', async () => {
    const wrapper = mount(ChatMessageBubble, {
      props: { message: makeLoadingMessage({ loadingStatus: 'Analisando sua pergunta...' }) },
      global: { stubs: { VueApexCharts: true } },
    })

    expect(wrapper.find('.status-text').text()).toBe('Analisando sua pergunta...')

    vi.advanceTimersByTime(3000)
    await nextTick()
    expect(wrapper.find('.status-text').text()).toBe('Consultando a base de dados...')

    vi.advanceTimersByTime(3000)
    await nextTick()
    expect(wrapper.find('.status-text').text()).toBe('Processando os resultados...')

    vi.advanceTimersByTime(3000)
    await nextTick()
    expect(wrapper.find('.status-text').text()).toBe('Cruzando informações e indicadores...')

    vi.advanceTimersByTime(3000)
    await nextTick()
    expect(wrapper.find('.status-text').text()).toBe('Preparando sua resposta...')

    wrapper.unmount()
  })

  it('respeita status específico enviado pelo backend', () => {
    const wrapper = mount(ChatMessageBubble, {
      props: { message: makeLoadingMessage({ loadingStatus: 'Consultando dados acadêmicos...' }) },
      global: { stubs: { VueApexCharts: true } },
    })

    expect(wrapper.find('.status-text').text()).toBe('Consultando dados acadêmicos...')
    wrapper.unmount()
  })

  it('exibe "Gerando resposta..." sem skeleton quando o texto já está chegando por streaming', () => {
    const wrapper = mount(ChatMessageBubble, {
      props: {
        message: makeLoadingMessage({
          text: 'Foram encontrados 42 projetos',
          loadingStatus: 'Analisando sua pergunta...',
        }),
      },
      global: { stubs: { VueApexCharts: true } },
    })

    expect(wrapper.find('.status-text').text()).toBe('Gerando resposta...')
    expect(wrapper.find('.skeleton-group').exists()).toBe(false)
    expect(wrapper.find('.loading-progress-bar').exists()).toBe(false)
    wrapper.unmount()
  })

  it('remove indicador de carregamento e exibe aviso de IA abaixo da resposta concluída', () => {
    const wrapper = mount(ChatMessageBubble, {
      props: {
        message: makeLoadingMessage({
          id: 'ai-1',
          isLoading: false,
          text: 'Resposta concluída.',
        }),
      },
      global: { stubs: { VueApexCharts: true } },
    })

    expect(wrapper.find('[role="status"]').exists()).toBe(false)
    expect(wrapper.find('.loading-brand-ring').exists()).toBe(false)
    expect(wrapper.text()).toContain('O Adito é uma IA e pode cometer erros.')
    wrapper.unmount()
  })

  it('não exibe aviso de IA enquanto carrega, na mensagem de boas-vindas ou em mensagens do usuário', () => {
    const loadingWrapper = mount(ChatMessageBubble, {
      props: { message: makeLoadingMessage({ id: 'ai-loading', isLoading: true }) },
      global: { stubs: { VueApexCharts: true } },
    })
    expect(loadingWrapper.text()).not.toContain('O Adito é uma IA e pode cometer erros.')
    loadingWrapper.unmount()

    const welcomeWrapper = mount(ChatMessageBubble, {
      props: { message: makeLoadingMessage({ id: 'welcome', isLoading: false, text: 'Olá!' }) },
      global: { stubs: { VueApexCharts: true } },
    })
    expect(welcomeWrapper.text()).not.toContain('O Adito é uma IA e pode cometer erros.')
    welcomeWrapper.unmount()

    const userWrapper = mount(ChatMessageBubble, {
      props: { message: makeLoadingMessage({ id: 'user-1', type: 'user', isLoading: false, text: 'Oi' }) },
      global: { stubs: { VueApexCharts: true } },
    })
    expect(userWrapper.text()).not.toContain('O Adito é uma IA e pode cometer erros.')
    userWrapper.unmount()
  })
})
