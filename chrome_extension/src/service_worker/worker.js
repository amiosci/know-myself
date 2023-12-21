
const createSummarySync = async ({ hash, url, title }) => {
    const apiHost = await chrome.storage.sync.get("kms.apihost") || 'http://127.0.0.1:5000';

    const hasSummaryResponse = await fetch(`${apiHost}/summary/${hash}`, {
        method: "GET"
    });

    const readingListSummaryResponse = await hasSummaryResponse.json();

    if (readingListSummaryResponse.hasSummary) {
        console.log(`Fetching existing for ${url}`);
        const getSummaryResponse = await fetch(`${apiHost}/summary/${hash}`, {
            method: "GET"
        });
        const summaryResponse = await getSummaryResponse.json();
        console.log(summaryResponse.summary);
        return;
    }

    const createSummaryResponse = await fetch(`${apiHost}/summary/${hash}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            "url": url,
            "title": title
        }),
    });

    const createSummaryJson = await createSummaryResponse.json();
    console.log(createSummaryJson);
}

const registerSummarizeTask = async ({ url, title }) => {
    const registerResultResponse = await fetch(`${apiHost}/process`, {
        method: "POST",
        signal: AbortSignal.timeout(3600 * 1000), // 1h
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            "url": url,
            "title": title
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
}

// one-time registration
chrome.runtime.onInstalled.addListener(async () => {
    chrome.contextMenus.create({
        enabled: true,
        title: 'Process contents',
        id: 'knowledge_agent.send_url',
        contexts: ['all'],
    });

    chrome.contextMenus.onClicked.addListener(async (info, tab) => {
        await processReadingListItem({
            url: info.frameUrl,
            title: tab.title
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

// Chrome extension local UI
chrome.action.onClicked.addListener(() => {
    chrome.tabs.create({ url: chrome.runtime.getURL("index.html"), pinned: true });
});