(() => {
  const RUN_NONCE = "__RUN_NONCE__";
  const SEND_BUTTON_LABEL = "__SEND_BUTTON_LABEL__";
  const SKIP_LINK_LABEL = "__SKIP_LINK_LABEL__";
  const COMPOSER_SELECTOR = 'textarea[data-testid="stChatInputTextArea"]';
  const SEND_BUTTON_SELECTOR = '[data-testid="stChatInputSubmitButton"]';
  const SKIP_LINK_SELECTOR = '[data-testid="stSkipToContent"]';
  const POLL_INTERVAL_MS = 100;
  const MAX_ATTEMPTS = 600;
  const root = document.documentElement;

  root.lang = "pt-BR";
  root.dataset.composerRun = RUN_NONCE;

  const labelControls = () => {
    const sendButton = document.querySelector(SEND_BUTTON_SELECTOR);
    if (sendButton) sendButton.setAttribute("aria-label", SEND_BUTTON_LABEL);
    const skipLink = document.querySelector(SKIP_LINK_SELECTOR);
    if (skipLink) skipLink.textContent = SKIP_LINK_LABEL;
  };

  let attempts = 0;
  const timer = setInterval(() => {
    attempts += 1;
    labelControls();
    const composer = document.querySelector(COMPOSER_SELECTOR);
    const superseded = root.dataset.composerRun !== RUN_NONCE;
    if (superseded || attempts >= MAX_ATTEMPTS) {
      clearInterval(timer);
      return;
    }
    if (!composer || composer.disabled) return;
    clearInterval(timer);
    composer.focus({ preventScroll: true });
  }, POLL_INTERVAL_MS);
})();
