import { call } from "@/common/api/core";
import { buildChart, isScalarResultData } from "@/modules/chat/composables/useChatApi";
import type { ChatMessage, Conversation } from "@/modules/chat/types";
import { computed, ref } from "vue";

const STORAGE_PREFIX = "adito_chat_history";

function createWelcomeMessage(): ChatMessage {
  return {
    id: "welcome",
    type: "ai",
    text: "Olá! Sou o Adito, seu assistente para consultar os dados de pesquisa e extensão do IFES Campus Serra. Como posso ajudar você hoje?",
    timestamp: new Date().toISOString(),
  };
}

export function createConversation(): Conversation {
  const now = new Date().toISOString();
  return {
    id: `local-${crypto.randomUUID()}`,
    title: "Nova Conversa",
    contextoId: null,
    messages: [createWelcomeMessage()],
    createdAt: now,
    updatedAt: now,
  };
}

function mapBackendMessage(message: any): ChatMessage {
  const metadata = message.metadata || {};
  // O histórico não guarda linhas; loadRows() reexecuta o SQL no dados.db.
  const table: Array<Record<string, any>> = [];
  const isScalarResult = false;

  return {
    id: String(message.id),
    type: message.role === "user" ? "user" : "ai",
    text:
      message.role === "user"
        ? message.content
        : metadata.type === "fallback"
          ? ""
          : message.content,
    timestamp: message.created_at,
    sql: metadata.sql,
    table,
    chart: null,
    isScalarResult,
    needsRows: message.role !== "user" && !!metadata.sql,
    isFallback: metadata.type === "fallback",
    isChat: metadata.type === "chat",
    fallbackScore: metadata.score,
    fallbackMessage: metadata.message,
    explanation: metadata.explanation,
    suggestions: metadata.suggestions,
    related_attributes: metadata.related_attributes,
    fieldFormats: metadata.field_formats,
  };
}

function mapBackendConversation(conversation: any): Conversation {
  return {
    id: String(conversation.id),
    title: conversation.title || "Nova Conversa",
    contextoId: conversation.contexto ? String(conversation.contexto) : null,
    messages: [
      createWelcomeMessage(),
      ...(conversation.messages || []).map(mapBackendMessage),
    ],
    createdAt: conversation.createdAt || conversation.created_at,
    updatedAt:
      conversation.updatedAt ||
      conversation.updated_at ||
      conversation.created_at,
  };
}

function clearLegacyChatStorage() {
  for (let index = localStorage.length - 1; index >= 0; index -= 1) {
    const key = localStorage.key(index);
    if (key?.startsWith(`${STORAGE_PREFIX}:`)) {
      localStorage.removeItem(key);
    }
  }
}

export function useChatHistory() {
  const conversations = ref<Conversation[]>([]);
  const currentConvId = ref<string | null>(null);
  const isHistoryLoading = ref(false);
  const historyError = ref<string | null>(null);
  let syncPromise: Promise<void> | null = null;
  let selectionRevision = 0;
  const loadingRows = new Set<string>();

  const resetToEmptyConversation = () => {
    conversations.value = [createConversation()];
    currentConvId.value = conversations.value[0]?.id || null;
  };

  clearLegacyChatStorage();
  resetToEmptyConversation();
  const initialConversationId = currentConvId.value;

  const updateMessage = (convId: string, messageId: string, patch: Partial<ChatMessage>) => {
    conversations.value = conversations.value.map((conversation) =>
      conversation.id !== convId
        ? conversation
        : {
            ...conversation,
            messages: conversation.messages.map((message) =>
              message.id === messageId ? { ...message, ...patch } : message,
            ),
          },
    );
  };

  /** Recarrega as linhas das respostas da conversa aberta (o histórico só guarda o SQL). */
  const loadRows = async (convId: string | null) => {
    const conversation = conversations.value.find((c) => c.id === convId);
    if (!conversation || convId?.startsWith("local-")) return;

    const pending = conversation.messages.filter((m) => m.needsRows && !loadingRows.has(m.id));
    await Promise.all(
      pending.map(async (message) => {
        loadingRows.add(message.id);
        try {
          const data = await call("chat.message_rows", { id: message.id });
          const rows = data.data || [];
          const isScalarResult = isScalarResultData(rows);
          updateMessage(convId!, message.id, {
            needsRows: false,
            table: rows,
            isScalarResult,
            chart: isScalarResult ? null : buildChart(rows),
          });
        } catch (error: any) {
          const detail = error?.response?.data?.message || "os dados mudaram; refaça a pergunta";
          updateMessage(convId!, message.id, {
            needsRows: false,
            text: `${message.text}\n\n_Não foi possível recarregar os dados: ${detail}._`,
          });
        } finally {
          loadingRows.delete(message.id);
        }
      }),
    );
  };

  const syncFromBackend = (): Promise<void> => {
    if (syncPromise) return syncPromise;
    isHistoryLoading.value = true;
    historyError.value = null;
    const revisionAtStart = selectionRevision;
    const conversationsAtStart = new Map(conversations.value.map((conversation) => [conversation.id, conversation]));

    syncPromise = (async () => {
      try {
        const data = await call("chat.conversations.list");
        if (!Array.isArray(data)) throw new Error("Histórico indisponível");

        const remoteConversations: Conversation[] = data.map(mapBackendConversation);
        const previous = new Map(conversations.value.map((conversation) => [conversation.id, conversation]));
        // Mantém respostas em andamento e resultados já recarregados numa atualização do histórico.
        const mergedRemote = remoteConversations.map((conversation) => {
          const cached = previous.get(conversation.id);
          if (cached && (conversationsAtStart.get(conversation.id) !== cached ||
            Date.parse(cached.updatedAt) > Date.parse(conversation.updatedAt))) return cached;
          return {
            ...conversation,
            messages: conversation.messages.map((message) => {
              const cachedMessage = cached?.messages.find((item) => item.id === message.id);
              return message.needsRows && cachedMessage && !cachedMessage.needsRows
                ? { ...message, ...cachedMessage }
                : message;
            }),
          };
        });
        const remoteIds = new Set(remoteConversations.map((conversation) => conversation.id));
        const pendingConversations = conversations.value.filter((conversation) => {
          if (remoteIds.has(conversation.id)) return false;
          // Uma resposta pode salvar um rascunho enquanto a lista antiga ainda está chegando.
          if (!conversation.id.startsWith("local-")) {
            return conversationsAtStart.get(conversation.id) !== conversation;
          }
          // Substitui apenas o rascunho inicial intocado; nunca descarta um chat criado pelo usuário.
          return !(conversation.id === initialConversationId &&
            conversation.messages.length === 1 && remoteConversations.length > 0 &&
            selectionRevision === 0);
        });
        conversations.value = [...pendingConversations, ...mergedRemote];
        if (conversations.value.length === 0) resetToEmptyConversation();
        if (!conversations.value.some((conversation) => conversation.id === currentConvId.value)) {
          currentConvId.value = conversations.value[0]?.id || null;
        } else if (revisionAtStart === selectionRevision && selectionRevision === 0 && remoteConversations.length > 0) {
          currentConvId.value = mergedRemote[0]?.id || currentConvId.value;
        }
        await loadRows(currentConvId.value);
      } catch {
        // Os rascunhos e a conversa selecionada continuam acessíveis se o núcleo estiver offline.
        historyError.value = "Não foi possível carregar as conversas.";
      } finally {
        isHistoryLoading.value = false;
        syncPromise = null;
      }
    })();
    return syncPromise;
  };

  syncFromBackend();

  const handleNewConversation = () => {
    selectionRevision += 1;
    const newConversation = createConversation();
    conversations.value = [newConversation, ...conversations.value];
    currentConvId.value = newConversation.id;
  };

  const handleDeleteConversation = async (id: string) => {
    if (!conversations.value.some((conversation) => conversation.id === id)) return;
    if (!id.startsWith("local-")) {
      await call("chat.conversations.delete", { id });
    }
    const updated = conversations.value.filter((c) => c.id !== id);
    if (updated.length === 0) {
      const next = createConversation();
      conversations.value = [next];
      currentConvId.value = next.id;
      return;
    }

    conversations.value = updated;
    if (currentConvId.value === id) {
      selectionRevision += 1;
      currentConvId.value = updated[0].id;
      await loadRows(currentConvId.value);
    }
  };

  const updateCurrentConversation = (
    updater: (conversation: Conversation) => Conversation,
  ) => {
    // Uma interação com o rascunho inicial também o torna a seleção do usuário.
    selectionRevision += 1;
    conversations.value = conversations.value.map((conversation) => {
      if (conversation.id !== currentConvId.value) return conversation;
      return updater(conversation);
    });
  };

  const replaceConversationId = (oldId: string, newId: string) => {
    selectionRevision += 1;
    conversations.value = conversations.value.map((conversation) =>
      conversation.id === oldId ? { ...conversation, id: newId } : conversation,
    );
    if (currentConvId.value === oldId) currentConvId.value = newId;
  };

  const setCurrentConvId = (id: string) => {
    if (!conversations.value.some((conversation) => conversation.id === id)) return;
    selectionRevision += 1;
    currentConvId.value = id;
    loadRows(id);
  };

  const setConversationContexto = (convId: string, contextoId: string | null) => {
    conversations.value = conversations.value.map((conversation) =>
      conversation.id === convId ? { ...conversation, contextoId } : conversation,
    );
  };

  const currentConversation = computed(
    () =>
      conversations.value.find((c) => c.id === currentConvId.value) ||
      conversations.value[0],
  );

  return {
    conversations,
    currentConvId,
    setCurrentConvId,
    handleNewConversation,
    handleDeleteConversation,
    updateCurrentConversation,
    replaceConversationId,
    setConversationContexto,
    currentConversation,
    syncFromBackend,
    isHistoryLoading,
    historyError,
  };
}
