const getApiHost = async () => {
    const apiHost = await chrome.storage.sync.get('kms.apihost');
    return apiHost['kms.apihost'] || 'http://127.0.0.1:5000';
}

const registerSummarizeTask = async ({ url, title }) => {
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

const processReadingListItem = async ({ url, title }) => {
    const protocol = url.split('//')[0];
    if (protocol.indexOf('chrome') > -1) {
        return;
    }

    const hash = await registerSummarizeTask({ url, title });
    console.log(`${hash}: ${url}`);
    return hash;
}

// one-time registration
chrome.runtime.onInstalled.addListener(async () => {
    chrome.contextMenus.create({
        enabled: true,
        title: 'Process contents',
        id: 'knowledge_agent.send_url',
        contexts: ['all'],
    });

    chrome.contextMenus.onClicked.addListener(async ({ frameUrl }, { title }) => {
        debugger;
        await processReadingListItem({
            url: frameUrl,
            title: title
        });
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