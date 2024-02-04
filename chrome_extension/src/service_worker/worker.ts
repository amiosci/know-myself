import { registerDocument, addDocumentAnnotation } from "./api";

// one-time registration
chrome.runtime.onInstalled.addListener(async ({ reason }) => {
  // use for onboarding page
  if (reason === "install") {
    chrome.tabs.create({
      url: "index.html",
    });
  }

  const contextMenuOptions: { [menuId: string]: string } = {
    "knowledge_agent.send_url": "Process Contents",
    "knowledge_agent.add_annotation": "Add Annotation",
  };

  for (const menuId in contextMenuOptions) {
    if (Object.hasOwnProperty.call(contextMenuOptions, menuId)) {
      const menuTitle = contextMenuOptions[menuId];

      chrome.contextMenus.create({
        enabled: true,
        title: menuTitle,
        id: menuId,
        contexts: ["all"],
      });
    }
  }

  // ingest all pre-registered reading list items
  const items = await chrome.readingList.query({});
  await Promise.all(items.map(registerDocument));
});

// automatically ingest new reading list records, inclusive from other devices
chrome.readingList.onEntryAdded.addListener(async (entry) => {
  await registerDocument(entry);
});

const toggleRecording = async (id: number) => {
  const existingContexts = await chrome.runtime.getContexts({});

  const offscreenDocument = existingContexts.find(
    (c) => c.contextType === 'OFFSCREEN_DOCUMENT'
  );

  let recording = false;
  if (!offscreenDocument) {
    chrome.offscreen.createDocument({
      url: 'recorder.html',
      reasons: [chrome.offscreen.Reason.USER_MEDIA],
      justification: 'Recording from chrome.tabCapture API',
    });
  } else {
    recording = offscreenDocument.documentUrl.endsWith('#recording');
  }

  if (recording) {
    chrome.runtime.sendMessage({
      type: 'stop-recording',
      target: 'offscreen'
    });
    chrome.action.setIcon({ path: 'icons/not-recording.png' });
    return;
  }

  // Get a MediaStream for the active tab.
  chrome.tabCapture.getMediaStreamId({
    targetTabId: id
  }, (streamId) => {
    // Send the stream ID to the offscreen document to start recording.
    chrome.runtime.sendMessage({
      type: 'start-recording',
      target: 'offscreen',
      data: streamId
    });
  });
};

chrome.runtime.onMessage.addListener(async (message: kms.RecorderResponse) => {
  if (message.target === 'recorder-parent') {
    switch (message.type) {
      case 'recording-completed':
        // save recording?
        // extract image?
        const recordingResponse = message.data;
        console.log(recordingResponse);
        break;
      default:
        throw new Error(`Unrecognized message: ${message.type}`);
    }
  }
});
chrome.contextMenus.onClicked.addListener(
  async ({ frameUrl, selectionText, linkUrl, menuItemId, frameId }, { title }) => {
    const hasSelectedText = selectionText !== undefined;
    const hasSelectedLink = linkUrl !== undefined;

    // we need a hash to add an annotation.
    // TODO: Register document without implicit processing requests
    if (
      menuItemId === "knowledge_agent.add_annotation" ||
      menuItemId === "knowledge_agent.send_url"
    ) {
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

      return;
    }

    if (menuItemId === "knowledge_agent.capture_document") {
      await toggleRecording(frameId);
    }
  }
);
