const getApiHost = async () => {
    const apiHost = await chrome.storage.sync.get('kms.apihost');
    return apiHost['kms.apihost'] || 'http://127.0.0.1:5000';
}

const registerDocument = async ({ url, title }) => {
    const apiHost = await getApiHost();
    const registerResultResponse = await fetch(`${apiHost}/process`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            'url': url,
            'title': title
        }),
    });

    const resultResponseBody = await registerResultResponse.json();
    console.log(resultResponseBody);
    return resultResponseBody['hash'];
}

const processReadingListItem = async ({ url, title }, { } = {}) => {
    const protocol = url.split('//')[0];
    if (protocol.indexOf('chrome') > -1) {
        return;
    }

    const hash = await registerDocument({ url, title });
    console.log(`${hash}: ${url}`);
    return hash;
}

const addDocumentAnnotation = async ({ hash, annotation }) => {
    const apiHost = await getApiHost();
    const addAnnotationResponse = await fetch(`${apiHost}/documents/${hash}/annotations`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            'annotation': annotation,
        }),
    });

    const responseBody = await addAnnotationResponse.json();
    console.log(responseBody);
}

const getDocumentAnnotation = async ({ hash }) => {
    const apiHost = await getApiHost();
    const getAnnotationResponse = await fetch(`${apiHost}/documents/${hash}/annotations`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    });

    const responseBody = await getAnnotationResponse.json();
    console.log(responseBody);
    return responseBody['annotations'];
}

const removeDocumentAnnotation = async ({ hash, annotation }) => {
    const apiHost = await getApiHost();
    const removeAnnotationResponse = await fetch(`${apiHost}/documents/${hash}/annotations`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            'annotation': annotation,
        }),
    });

    const responseBody = await removeAnnotationResponse.json();
    console.log(responseBody);
}

// one-time registration
chrome.runtime.onInstalled.addListener(async () => {
    chrome.contextMenus.create({
        enabled: true,
        title: 'Process contents',
        id: 'knowledge_agent.send_url',
        contexts: ['all'],
    });

    chrome.contextMenus.onClicked.addListener(async (
        { frameUrl, selectionText, linkUrl, menuItemId },
        { title }
    ) => {
        // save selection as annotation
        console.log(selectionText);
        console.log(linkUrl ?? "No link selected");

        const hasSelectedText = selectionText !== undefined;
        const hasSelectedLink = linkUrl !== undefined;

        const itemHash = await processReadingListItem({
            url: frameUrl,
            title: title
        });

        if (hasSelectedText) {
            await addDocumentAnnotation({
                hash: itemHash,
                annotation: selectionText
            });
        }
    });

    // ingest all pre-registered reading list items
    const items = await chrome.readingList.query({});
    await Promise.all(items.map(processReadingListItem));
});

// automatically ingest new reading list records, inclusive from other devices
chrome.readingList.onEntryAdded.addListener(async (entry) => {
    await processReadingListItem(entry);
});

// open Chrome extension local UI
chrome.action.onClicked.addListener(() => {
    chrome.tabs.create({ url: chrome.runtime.getURL('index.html'), pinned: true });
});