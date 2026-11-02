export const PAGE_TITLE = "Empório da Música";
export const STORE_NAME = "Empório da Música";
export const STORE_TAGLINE = "Sua música começa aqui";
export const ASSISTANT_NAME = "Lia";
export const CUSTOMER_NAME = "Você";
export const GREETING = "Oi! Eu sou a Lia, atendimento virtual da Empório da Música. Posso ajudar com produtos, preços, pedidos, trocas e informações da loja.";
export const CONVERSATION_LABEL = "Conversa com o atendimento";
export const COMPOSER_PLACEHOLDER = "Escreva sua mensagem";
export const COMPOSER_LABEL = "Sua mensagem";
export const SEND_LABEL = "Enviar mensagem";
export const TYPING_LABEL = "Lia está digitando";
export const RETRY_LABEL = "Tentar de novo";
export const AVATAR_ALT = "";
export const NOT_FOUND_MESSAGE = "Esta página não existe.";
export const BACK_TO_CHAT_LABEL = "Voltar para o atendimento";
export const SERVICE_UNAVAILABLE_MESSAGE = "Nosso atendimento está indisponível neste momento. Tente de novo em alguns minutos.";
export const NO_CONNECTION_MESSAGE = "Sem conexão agora. Verifique sua internet e tente de novo.";
export const TOO_MANY_CONVERSATIONS_MESSAGE = "Estamos com muitas conversas agora. Tente de novo em instantes.";

export const FAILURE_MESSAGES = {
  authentication: SERVICE_UNAVAILABLE_MESSAGE,
  server: SERVICE_UNAVAILABLE_MESSAGE,
  connection: NO_CONNECTION_MESSAGE,
  rate_limit: TOO_MANY_CONVERSATIONS_MESSAGE,
} satisfies Record<string, string>;

export type UnavailableReason = keyof typeof FAILURE_MESSAGES;
