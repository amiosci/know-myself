export const getApiHost = async () => {
    const apiHost = await chrome.storage.sync.get('kms.apihost');
    return apiHost['kms.apihost'] || 'http://127.0.0.1:5000';
}

export const removeAllChildNodes = (parent) => {
    while (parent.firstChild) {
        parent.removeChild(parent.firstChild);
    }
}

export const addSafeEventListener = (element, eventName, eventHandler) => {
    element.addEventListener(eventName, (event) => {
        if (event.target !== element) {
            return;
        }

        eventHandler(event);
    });

    // return to capture inline methods
    return eventHandler;
};