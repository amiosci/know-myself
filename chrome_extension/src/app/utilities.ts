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
  const safeEvent = (event: Type) => {
    if (event.target !== element) {
      return;
    }

    eventHandler(event);
  };

  element.addEventListener(eventName, safeEvent);

  // return to capture inline methods
  return safeEvent;
};
