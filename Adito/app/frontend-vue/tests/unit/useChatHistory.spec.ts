import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'

const callMock = vi.fn()

vi.mock('@/common/api/core', () => ({
  call: (...args: unknown[]) => callMock(...args),
}))

import { createConversation, useChatHistory } from '@/modules/chat/composables/useChatHistory'
import { provideChatWorkspace, useChatWorkspace } from '@/modules/chat/composables/useChatWorkspace'

const backendConversation = (id: string, title = id, messages: unknown[] = []) => ({
  id,
  title,
  created_at: '2026-11-18T10:00:00Z',
  updated_at: '2026-11-18T10:00:00Z',
  messages,
})

describe('modules/chat/composables/useChatHistory', () => {
  beforeEach(() => {
    callMock.mockReset()
    localStorage.clear()
  })

  it('createConversation cria conversa local com mensagem de boas-vindas do Adito', () => {
    const conv = createConversation()
    expect(conv.id.startsWith('local-')).toBe(true)
    expect(conv.title).toBe('Nova Conversa')
    expect(conv.messages).toHaveLength(1)
    expect(conv.messages[0].id).toBe('welcome')
    expect(conv.messages[0].text).toContain('Adito')
  })

  it('limpa chaves antigas de histórico no localStorage ao inicializar', () => {
    localStorage.setItem('adito_chat_history:legado', '[]')
    localStorage.setItem('outra_chave', 'manter')
    callMock.mockResolvedValueOnce([])

    useChatHistory()

    expect(localStorage.getItem('adito_chat_history:legado')).toBeNull()
    expect(localStorage.getItem('outra_chave')).toBe('manter')
  })

  it('syncFromBackend carrega conversas e reexecuta linhas pendentes via chat.message_rows', async () => {
    callMock.mockImplementation(async (method: string) => {
      if (method === 'chat.conversations.list') {
        return [
          {
            id: 'conv-1',
            title: 'Bolsas 2024',
            contexto: 'ctx-1',
            created_at: '2026-11-18T10:00:00Z',
            messages: [
              { id: 'u1', role: 'user', content: 'Quantas bolsas em 2024?', created_at: '2026-11-18T10:00:01Z' },
              {
                id: 'a1',
                role: 'assistant',
                content: 'Foram 120 bolsas.',
                created_at: '2026-11-18T10:00:02Z',
                metadata: { sql: 'SELECT COUNT(*) AS total FROM vfact_orientacao_bolsa_resolved', type: 'analysis' },
              },
            ],
          },
        ]
      }
      if (method === 'chat.message_rows') {
        return { data: [{ total: 120 }] }
      }
      return null
    })

    const { conversations, currentConversation, syncFromBackend } = useChatHistory()
    await syncFromBackend()
    await new Promise((r) => setTimeout(r, 0))

    expect(conversations.value).toHaveLength(1)
    expect(currentConversation.value.title).toBe('Bolsas 2024')
    const aiMsg = currentConversation.value.messages[2]
    expect(aiMsg.table).toEqual([{ total: 120 }])
    expect(aiMsg.isScalarResult).toBe(true)
    expect(aiMsg.needsRows).toBe(false)
  })

  it('handleNewConversation, replaceConversationId e handleDeleteConversation mantêm estado consistente', async () => {
    callMock.mockResolvedValue([])
    const history = useChatHistory()
    await history.syncFromBackend()
    const initialId = history.currentConvId.value!

    await new Promise((r) => setTimeout(r, 5))
    history.handleNewConversation()
    expect(history.conversations.value).toHaveLength(2)

    const newLocalId = history.currentConvId.value!
    expect(newLocalId).not.toBe(initialId)
    history.replaceConversationId(newLocalId, 'conv-remota')
    expect(history.currentConvId.value).toBe('conv-remota')

    await history.handleDeleteConversation('conv-remota')
    expect(callMock).toHaveBeenCalledWith('chat.conversations.delete', { id: 'conv-remota' })
    expect(history.currentConvId.value).toBe(initialId)
  })

  it('gera ids distintos mesmo quando várias conversas são criadas no mesmo instante', () => {
    vi.spyOn(Date, 'now').mockReturnValue(123)
    const ids = Array.from({ length: 10 }, () => createConversation().id)
    expect(new Set(ids).size).toBe(10)
  })

  it('deduplica a carga inicial e preserva a nova conversa criada enquanto ela está pendente', async () => {
    let resolveList!: (data: unknown[]) => void
    callMock.mockReturnValue(new Promise((resolve) => { resolveList = resolve }))
    const history = useChatHistory()
    const loading = history.syncFromBackend()
    expect(callMock).toHaveBeenCalledTimes(1)
    expect(history.isHistoryLoading.value).toBe(true)

    history.handleNewConversation()
    const draftId = history.currentConvId.value
    history.updateCurrentConversation((conversation) => ({ ...conversation, title: 'Meu rascunho' }))
    resolveList([backendConversation('salva', 'Conversa salva')])
    await loading

    expect(history.currentConvId.value).toBe(draftId)
    expect(history.currentConversation.value.title).toBe('Meu rascunho')
    expect(history.conversations.value.some((conversation) => conversation.id === 'salva')).toBe(true)
    expect(history.isHistoryLoading.value).toBe(false)
  })

  it('preserva o envio no rascunho inicial enquanto a lista de conversas está pendente', async () => {
    let resolveList!: (data: unknown[]) => void
    callMock.mockReturnValue(new Promise((resolve) => { resolveList = resolve }))
    const history = useChatHistory()
    const loading = history.syncFromBackend()
    const draftId = history.currentConvId.value!
    history.updateCurrentConversation((conversation) => ({
      ...conversation,
      title: 'Pergunta em andamento',
      messages: [...conversation.messages, {
        id: 'novo-envio', type: 'user', text: 'Pergunta em andamento', timestamp: new Date().toISOString(),
      }],
    }))
    resolveList([backendConversation('anterior')])
    await loading

    expect(history.currentConvId.value).toBe(draftId)
    expect(history.currentConversation.value.messages.at(-1)?.text).toBe('Pergunta em andamento')
    expect(history.conversations.value.some((conversation) => conversation.id === 'anterior')).toBe(true)
  })

  it('mantém a conversa que ganhou id do servidor durante a carga de uma lista desatualizada', async () => {
    let resolveList!: (data: unknown[]) => void
    callMock.mockReturnValue(new Promise((resolve) => { resolveList = resolve }))
    const history = useChatHistory()
    const loading = history.syncFromBackend()
    const draftId = history.currentConvId.value!
    history.updateCurrentConversation((conversation) => ({
      ...conversation,
      title: 'Pergunta nova',
      messages: [...conversation.messages, {
        id: 'novo-envio', type: 'user', text: 'Pergunta nova', timestamp: new Date().toISOString(),
      }],
    }))
    history.replaceConversationId(draftId, 'recem-salva')
    resolveList([backendConversation('anterior')])
    await loading
    history.updateCurrentConversation((conversation) => ({
      ...conversation,
      messages: [...conversation.messages, {
        id: 'nova-resposta', type: 'ai', text: 'Resposta recebida', timestamp: new Date().toISOString(),
      }],
    }))

    expect(history.currentConvId.value).toBe('recem-salva')
    expect(history.currentConversation.value.title).toBe('Pergunta nova')
    expect(history.currentConversation.value.messages.at(-1)?.text).toBe('Resposta recebida')
    expect(history.conversations.value.find((conversation) => conversation.id === 'anterior')?.messages).toHaveLength(1)
  })

  it('preserva a seleção e as linhas já carregadas ao atualizar o histórico', async () => {
    const savedMessage = {
      id: 'a2', role: 'assistant', content: 'Resultado', created_at: '2026-11-18T10:00:01Z',
      metadata: { sql: 'SELECT 5 AS total' },
    }
    callMock.mockImplementation(async (method: string) => method === 'chat.message_rows'
      ? { data: [{ total: 5 }] }
      : [backendConversation('primeira'), backendConversation('segunda', 'Segunda', [savedMessage])])
    const history = useChatHistory()
    await history.syncFromBackend()
    history.setCurrentConvId('segunda')
    await flushPromises()
    await history.syncFromBackend()

    expect(history.currentConvId.value).toBe('segunda')
    expect(history.currentConversation.value.messages[1].table).toEqual([{ total: 5 }])
    expect(callMock.mock.calls.filter(([method]) => method === 'chat.message_rows')).toHaveLength(1)
  })

  it('carrega os resultados da próxima conversa quando a conversa ativa é excluída', async () => {
    callMock.mockImplementation(async (method: string) => {
      if (method === 'chat.conversations.list') return [
        backendConversation('primeira'),
        backendConversation('segunda', 'Segunda', [{
          id: 'a2', role: 'assistant', content: 'Resultado', created_at: '2026-11-18T10:00:01Z',
          metadata: { sql: 'SELECT 5 AS total' },
        }]),
      ]
      if (method === 'chat.message_rows') return { data: [{ total: 5 }] }
      return null
    })
    const history = useChatHistory()
    await history.syncFromBackend()
    await history.handleDeleteConversation('primeira')

    expect(history.currentConvId.value).toBe('segunda')
    expect(history.currentConversation.value.messages[1].table).toEqual([{ total: 5 }])
  })

  it('informa falha sem apagar o rascunho e permite tentar carregar novamente', async () => {
    callMock.mockRejectedValue(new Error('offline'))
    const history = useChatHistory()
    const draftId = history.currentConvId.value
    await history.syncFromBackend()
    expect(history.historyError.value).toContain('Não foi possível')
    expect(history.currentConvId.value).toBe(draftId)
    expect(history.isHistoryLoading.value).toBe(false)

    callMock.mockResolvedValue([backendConversation('salva')])
    await history.syncFromBackend()
    expect(history.historyError.value).toBeNull()
    expect(history.currentConvId.value).toBe('salva')
  })

  it('mantém uma única sessão entre a sidebar e as remontagens da tela de chat', async () => {
    callMock.mockResolvedValue([])
    let sidebarWorkspace!: ReturnType<typeof useChatWorkspace>
    const chatWorkspaces: ReturnType<typeof useChatWorkspace>[] = []
    const Sidebar = defineComponent({ setup() {
      sidebarWorkspace = useChatWorkspace()
      return () => h('aside')
    } })
    const Chat = defineComponent({ setup() {
      chatWorkspaces.push(useChatWorkspace())
      return () => h('main')
    } })
    const Layout = defineComponent({
      props: { showChat: Boolean },
      setup(props) {
        provideChatWorkspace()
        return () => h('div', [h(Sidebar), props.showChat ? h(Chat) : h('section')])
      },
    })
    const wrapper = mount(Layout, { props: { showChat: true } })
    await flushPromises()
    sidebarWorkspace.history.handleNewConversation()
    const selectedId = sidebarWorkspace.history.currentConvId.value
    await wrapper.setProps({ showChat: false })
    await wrapper.setProps({ showChat: true })

    expect(chatWorkspaces).toHaveLength(2)
    expect(chatWorkspaces.every((workspace) => workspace === sidebarWorkspace)).toBe(true)
    expect(chatWorkspaces[1].history.currentConvId.value).toBe(selectedId)
    expect(callMock.mock.calls.filter(([method]) => method === 'chat.conversations.list')).toHaveLength(1)
    wrapper.unmount()
  })
})
