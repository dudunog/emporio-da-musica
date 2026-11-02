(() => {
  const RUN_NONCE = "__RUN_NONCE__";
  const SEND_BUTTON_LABEL = "__SEND_BUTTON_LABEL__";
  const SKIP_LINK_LABEL = "__SKIP_LINK_LABEL__";
  const CONNECTION_LOST_LABEL = "__CONNECTION_LOST_LABEL__";
  const COMPOSER_SELECTOR = 'textarea[data-testid="stChatInputTextArea"]';
  const SEND_BUTTON_SELECTOR = '[data-testid="stChatInputSubmitButton"]';
  const SKIP_LINK_SELECTOR = '[data-testid="stSkipToContent"]';
  const CONNECTION_DIALOG_TITLE_SELECTOR = '[data-testid="stDialog"] h2';
  const POLL_INTERVAL_MS = 100;
  const MAX_ATTEMPTS = 600;
  const root = document.documentElement;

  root.lang = "pt-BR";
  root.dataset.composerRun = RUN_NONCE;

  const focusComposerWhenReady = () => {
    const startedRun = root.dataset.composerRun;
    let attempts = 0;
    const timer = setInterval(() => {
      attempts += 1;
      if (root.dataset.composerRun !== startedRun || attempts >= MAX_ATTEMPTS) {
        clearInterval(timer);
        return;
      }
      const composer = document.querySelector(COMPOSER_SELECTOR);
      if (!composer || composer.disabled) return;
      clearInterval(timer);
      composer.focus({ preventScroll: true });
    }, POLL_INTERVAL_MS);
  };

  let connectionDialogOpen = false;

  const localizeNativeTexts = () => {
    const sendButton = document.querySelector(SEND_BUTTON_SELECTOR);
    if (sendButton && sendButton.getAttribute("aria-label") !== SEND_BUTTON_LABEL) {
      sendButton.setAttribute("aria-label", SEND_BUTTON_LABEL);
    }
    const skipLink = document.querySelector(SKIP_LINK_SELECTOR);
    if (skipLink && skipLink.textContent !== SKIP_LINK_LABEL) {
      skipLink.textContent = SKIP_LINK_LABEL;
    }
    const dialogTitle = document.querySelector(CONNECTION_DIALOG_TITLE_SELECTOR);
    if (dialogTitle && dialogTitle.textContent !== CONNECTION_LOST_LABEL) {
      dialogTitle.textContent = CONNECTION_LOST_LABEL;
    }
    if (connectionDialogOpen && !dialogTitle) focusComposerWhenReady();
    connectionDialogOpen = Boolean(dialogTitle);
  };

  if (!root.dataset.nativeTextsObserved) {
    root.dataset.nativeTextsObserved = "true";
    localizeNativeTexts();
    new MutationObserver(localizeNativeTexts).observe(document.body, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ["aria-label"],
    });
  }

  focusComposerWhenReady();
})();
