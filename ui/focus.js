(() => {
  const RUN_NONCE = "__RUN_NONCE__";
  const SEND_BUTTON_LABEL = "__SEND_BUTTON_LABEL__";
  const SKIP_LINK_LABEL = "__SKIP_LINK_LABEL__";
  const CONNECTION_LOST_LABEL = "__CONNECTION_LOST_LABEL__";
  const COMPOSER_SELECTOR = 'textarea[data-testid="stChatInputTextArea"]';
  const COMPOSER_BOX_SELECTOR = '[data-testid="stChatInput"]';
  const SEND_BUTTON_SELECTOR = '[data-testid="stChatInputSubmitButton"]';
  const SKIP_LINK_SELECTOR = '[data-testid="stSkipToContent"]';
  const CONNECTION_DIALOG_SELECTOR = '[data-testid="stDialog"]';
  const CONNECTION_DIALOG_TITLE_SELECTOR = `${CONNECTION_DIALOG_SELECTOR} h2`;
  const RESEND_SELECTOR = ".st-key-resend";
  const RESEND_BUTTON_SELECTOR = `${RESEND_SELECTOR} button`;
  const TYPING_SELECTOR = ".typing";
  const CUSTOMER_MESSAGE_SELECTOR = ".customer-text";
  const MAIN_SELECTOR = ".stMain";
  const DIALOG_DISMISS_EVENTS = ["keydown", "pointerdown", "pointerup", "mousedown", "mouseup", "click", "touchstart", "touchend"];
  const POLL_INTERVAL_MS = 100;
  const MAX_ATTEMPTS = 600;
  const SCROLL_TOLERANCE_PX = 2;
  const root = document.documentElement;

  root.lang = "pt-BR";
  root.dataset.composerRun = RUN_NONCE;

  const scrollConversationToEnd = () => {
    const main = document.querySelector(MAIN_SELECTOR);
    main.scrollTop = main.scrollHeight;
    return main.scrollTop;
  };

  const revealResendButton = () => {
    if (document.querySelector(RESEND_SELECTOR)) scrollConversationToEnd();
  };

  const focusUnlessTextIsSelected = (composer) => {
    if (document.getSelection().isCollapsed) composer.focus({ preventScroll: true });
  };

  const focusComposerWhenReady = () => {
    revealResendButton();
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
      focusUnlessTextIsSelected(composer);
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

  let composerWasDisabled = false;

  const refocusReenabledComposer = () => {
    const composer = document.querySelector(COMPOSER_SELECTOR);
    if (!composer) return;
    const reenabled = composerWasDisabled && !composer.disabled;
    composerWasDisabled = composer.disabled;
    if (reenabled && document.activeElement === document.body) focusUnlessTextIsSelected(composer);
  };

  let customerMessageCount = document.querySelectorAll(CUSTOMER_MESSAGE_SELECTOR).length;
  let turnInProgress = false;
  let turnStartedOnRun = RUN_NONCE;
  let followingTurn = false;
  let followedScrollTop = 0;

  const followConversationTurn = () => {
    const typing = Boolean(document.querySelector(TYPING_SELECTOR));
    const currentCount = document.querySelectorAll(CUSTOMER_MESSAGE_SELECTOR).length;
    if (currentCount > customerMessageCount || (typing && !turnInProgress)) {
      turnInProgress = true;
      turnStartedOnRun = root.dataset.composerRun;
      followingTurn = true;
    }
    customerMessageCount = currentCount;
    if (followingTurn) followedScrollTop = scrollConversationToEnd();
    if (root.dataset.composerRun === turnStartedOnRun) return;
    turnInProgress = false;
    followingTurn = false;
  };

  const trackCustomerScroll = ({ target }) => {
    if (!turnInProgress || target !== document.querySelector(MAIN_SELECTOR)) return;
    const distanceToEnd = target.scrollHeight - target.clientHeight - target.scrollTop;
    if (distanceToEnd <= SCROLL_TOLERANCE_PX) {
      followingTurn = true;
      followedScrollTop = target.scrollTop;
      return;
    }
    if (target.scrollTop < followedScrollTop - SCROLL_TOLERANCE_PX) followingTurn = false;
  };

  let composerBox = null;
  let composerBoxTop = 0;

  const keepResendButtonAboveComposer = () => {
    const previousTop = composerBoxTop;
    composerBoxTop = composerBox.getBoundingClientRect().top;
    const resendButton = document.querySelector(RESEND_BUTTON_SELECTOR);
    if (!resendButton) return;
    const buttonBottom = resendButton.getBoundingClientRect().bottom;
    if (buttonBottom <= previousTop && buttonBottom > composerBoxTop) scrollConversationToEnd();
  };

  const composerResizeObserver = new ResizeObserver(keepResendButtonAboveComposer);

  const observeComposerBox = () => {
    const currentBox = document.querySelector(COMPOSER_BOX_SELECTOR);
    if (!currentBox || currentBox === composerBox) return;
    composerResizeObserver.disconnect();
    composerBox = currentBox;
    composerBoxTop = currentBox.getBoundingClientRect().top;
    composerResizeObserver.observe(currentBox);
  };

  const handleDomChange = () => {
    localizeNativeTexts();
    followConversationTurn();
    refocusReenabledComposer();
    observeComposerBox();
  };

  const keepConnectionDialogOpen = (event) => {
    const dismisses = event.type !== "keydown" || event.key === "Escape";
    if (dismisses && document.querySelector(CONNECTION_DIALOG_SELECTOR)) event.stopImmediatePropagation();
  };

  if (!root.dataset.nativeTextsObserved) {
    root.dataset.nativeTextsObserved = "true";
    handleDomChange();
    window.addEventListener("scroll", trackCustomerScroll, true);
    DIALOG_DISMISS_EVENTS.forEach((eventName) => window.addEventListener(eventName, keepConnectionDialogOpen, true));
    const domObserver = new MutationObserver(handleDomChange);
    domObserver.observe(document.body, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ["aria-label", "disabled"],
    });
    domObserver.observe(root, { attributes: true, attributeFilter: ["data-composer-run"] });
  }

  focusComposerWhenReady();
})();
