import { registerDocument, addDocumentAnnotation } from "./api";

// one-time registration
chrome.runtime.onInstalled.addListener(async ({ reason }) => {
  // use for onboarding page
  if (reason === "install") {
    chrome.tabs.create({
      url: "index.html",
    });
  }

  chrome.contextMenus.create({
    enabled: true,
    title: "Process contents",
    id: "knowledge_agent.send_url",
    contexts: ["all"],
  });

  // ingest all pre-registered reading list items
  const items = await chrome.readingList.query({});
  await Promise.all(items.map(registerDocument));
});

// automatically ingest new reading list records, inclusive from other devices
chrome.readingList.onEntryAdded.addListener(async (entry) => {
  await registerDocument(entry);
});

chrome.contextMenus.onClicked.addListener(
  async ({ frameUrl, selectionText, linkUrl, menuItemId }, { title }) => {
    const hasSelectedText = selectionText !== undefined;
    const hasSelectedLink = linkUrl !== undefined;

    const itemHash = await registerDocument({
      url: frameUrl,
      title: title,
    });

    if (hasSelectedText) {
      await addDocumentAnnotation({
        hash: itemHash,
        annotation: selectionText,
      });
    }
  }
);

// open Chrome extension local UI
chrome.action.onClicked.addListener((tab) => {
  console.log(tab);
  chrome.tabs.create({
    url: chrome.runtime.getURL("index.html"),
    pinned: true,
  });
});
