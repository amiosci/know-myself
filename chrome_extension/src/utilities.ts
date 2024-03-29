export const getApiHost = async () => {
  const apiHost = await chrome.storage.sync.get("kms.apihost");
  return apiHost["kms.apihost"] || "http://127.0.0.1:5000";
};

export const removeAllChildNodes = (parent: Element) => {
  while (parent.firstChild) {
    parent.removeChild(parent.firstChild);
  }
};

export const addSafeEventListener = <Type extends Event>(
  element: Element, eventName: string, eventHandler: (event: Type) => void) => {
  function safeEvent(this: Element, event: Event) {
    if (event.target !== element) {
      return;
    }

    eventHandler(event as Type);
  };

  element.addEventListener(eventName, safeEvent);

  // return to capture inline methods
  return safeEvent;
};

export const safeQuerySelector = <Type extends Element | HTMLElement = Element>(selector: string, parentElement: Element | Document = document): Type => {
  const element = parentElement.querySelector(selector);
  if (element === null) {
    throw new ReferenceError(`No element found for ${selector}`);
  }

  return element as Type;
};