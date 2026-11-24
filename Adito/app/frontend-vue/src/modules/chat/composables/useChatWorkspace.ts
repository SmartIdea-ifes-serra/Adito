import { inject, provide, type InjectionKey } from 'vue'
import { useChatApi } from '@/modules/chat/composables/useChatApi'
import { useChatHistory } from '@/modules/chat/composables/useChatHistory'

type ChatWorkspace = {
  history: ReturnType<typeof useChatHistory>
  chatApi: ReturnType<typeof useChatApi>
  isStreaming: ReturnType<typeof useChatApi>['isLoading']
}

const chatWorkspaceKey: InjectionKey<ChatWorkspace> = Symbol('adito-chat-workspace')

/** Uma única sessão de chat para a navegação e a tela de conversa. */
export function provideChatWorkspace(): ChatWorkspace {
  const chatApi = useChatApi()
  const workspace = {
    history: useChatHistory(),
    chatApi,
    isStreaming: chatApi.isLoading,
  }
  provide(chatWorkspaceKey, workspace)
  return workspace
}

export function useChatWorkspace(): ChatWorkspace {
  const workspace = inject(chatWorkspaceKey)
  if (!workspace) throw new Error('O chat precisa estar dentro do layout do Adito.')
  return workspace
}
