(() => {
  const SEND_BUTTON_LABEL = "__SEND_BUTTON_LABEL__";
  const SKIP_LINK_LABEL = "__SKIP_LINK_LABEL__";
  const CONNECTION_LOST_LABEL = "__CONNECTION_LOST_LABEL__";
  const COMPOSER_SELECTOR = 'textarea[data-testid="stChatInputTextArea"]';
  const COMPOSER_BOX_SELECTOR = '[data-testid="stChatInput"]';
  const SEND_BUTTON_SELECTOR = '[data-testid="stChatInputSubmitButton"]';
  const SKIP_LINK_SELECTOR = '[data-testid="stSkipToContent"]';
  const CONNECTION_DIALOG_SELECTOR = '[data-testid="stDialog"]';
  const CONNECTION_DIALOG_TITLE_SELECTOR = `${CONNECTION_DIALOG_SELECTOR} h2`;
  const RETRY_BUTTON_SELECTOR = ".st-key-resend button";
  const CUSTOMER_MESSAGE_SELECTOR = ".customer-text";
  const MAIN_SELECTOR = ".stMain";
  const DIALOG_DISMISS_EVENTS = ["keydown", "click"];
  const SCROLL_TOLERANCE_PX = 2;
  const root = document.documentElement;

  if (root.dataset.chatBehaviorInstalled) return;
  root.dataset.chatBehaviorInstalled = "true";
  root.lang = "pt-BR";

  let composerWasUsable = false;
  let customerMessageCount = 0;
  let hadRetryButton = false;
  let followingConversation = false;
  let observedComposerBox = null;
  let composerTop = 0;

  const scrollConversationToEnd = () => {
    const main = document.querySelector(MAIN_SELECTOR);
    main.scrollTop = main.scrollHeight;
  };

  const localizeNativeTexts = () => {
    const sendButton = document.querySelector(SEND_BUTTON_SELECTOR);
    if (sendButton && sendButton.getAttribute("aria-label") !== SEND_BUTTON_LABEL) {
      sendButton.setAttribute("aria-label", SEND_BUTTON_LABEL);
    }
    const skipLink = document.querySelector(SKIP_LINK_SELECTOR);
    if (skipLink && skipLink.textContent !== SKIP_LINK_LABEL) skipLink.textContent = SKIP_LINK_LABEL;
    const dialogTitle = document.querySelector(CONNECTION_DIALOG_TITLE_SELECTOR);
    if (dialogTitle && dialogTitle.textContent !== CONNECTION_LOST_LABEL) dialogTitle.textContent = CONNECTION_LOST_LABEL;
  };

  const focusComposerWhenUsable = () => {
    const composer = document.querySelector(COMPOSER_SELECTOR);
    const usable = Boolean(composer) && !composer.disabled && !document.querySelector(CONNECTION_DIALOG_SELECTOR);
    const becameUsable = usable && !composerWasUsable;
    composerWasUsable = usable;
    if (becameUsable && document.getSelection().isCollapsed) composer.focus({ preventScroll: true });
  };

  const resumeConversationOnRetry = ({ target }) => {
    if (!target.closest(RETRY_BUTTON_SELECTOR)) return;
    followingConversation = true;
    document.querySelector(COMPOSER_SELECTOR).focus({ preventScroll: true });
  };

  const followConversation = () => {
    const messageCount = document.querySelectorAll(CUSTOMER_MESSAGE_SELECTOR).length;
    const hasRetryButton = Boolean(document.querySelector(RETRY_BUTTON_SELECTOR));
    if (messageCount > customerMessageCount || (hasRetryButton && !hadRetryButton)) followingConversation = true;
    customerMessageCount = messageCount;
    hadRetryButton = hasRetryButton;
    if (followingConversation) scrollConversationToEnd();
  };

  const trackCustomerScroll = ({ target }) => {
    if (target !== document.querySelector(MAIN_SELECTOR)) return;
    const distanceToEnd = target.scrollHeight - target.clientHeight - target.scrollTop;
    followingConversation = distanceToEnd <= SCROLL_TOLERANCE_PX;
  };

  const keepRetryButtonAboveComposer = ([{ target: composerBox }]) => {
    const previousTop = composerTop;
    composerTop = composerBox.getBoundingClientRect().top;
    const retryButton = document.querySelector(RETRY_BUTTON_SELECTOR);
    if (!retryButton) return;
    const buttonBottom = retryButton.getBoundingClientRect().bottom;
    if (buttonBottom <= previousTop && buttonBottom > composerTop) scrollConversationToEnd();
  };

  const composerResizeObserver = new ResizeObserver(keepRetryButtonAboveComposer);

  const observeComposerBox = () => {
    const composerBox = document.querySelector(COMPOSER_BOX_SELECTOR);
    if (!composerBox || composerBox === observedComposerBox) return;
    composerResizeObserver.observe(composerBox);
    observedComposerBox = composerBox;
  };

  const handleDomChange = () => {
    localizeNativeTexts();
    focusComposerWhenUsable();
    followConversation();
    observeComposerBox();
  };

  const keepConnectionDialogOpen = (event) => {
    const dismisses = event.type !== "keydown" || event.key === "Escape";
    if (dismisses && document.querySelector(CONNECTION_DIALOG_SELECTOR)) event.stopImmediatePropagation();
  };

  handleDomChange();
  window.addEventListener("click", resumeConversationOnRetry);
  window.addEventListener("scroll", trackCustomerScroll, true);
  DIALOG_DISMISS_EVENTS.forEach((eventName) => window.addEventListener(eventName, keepConnectionDialogOpen, true));
  new MutationObserver(handleDomChange).observe(document.body, {
    subtree: true,
    childList: true,
    attributes: true,
    attributeFilter: ["aria-label", "disabled"],
  });
})();
