import { registerDocument, getDocumentAnnotations } from "./api";
import { safeQuerySelector } from "./utilities";

const getCurrentTab = async () => {
  const queryOptions = { active: true, lastFocusedWindow: true };
  const [tab] = await chrome.tabs.query(queryOptions);
  console.log(tab);
  return tab;
};

const init = async () => {
  const extensionUrl = `chrome-extension://${chrome.runtime.id}`;
  const extensionHome = `${extensionUrl}/index.html`;

  const openSettingsButton = safeQuerySelector(".open-extension-page");
  openSettingsButton.addEventListener("click", async () => {
    window.open(extensionHome);
  });

  const processCurrentPageButton = safeQuerySelector(
    ".process-current-page"
  );
  processCurrentPageButton.addEventListener("click", async () => {
    const { title, url } = await getCurrentTab();
    if (title === undefined || url === undefined) {
      return;
    }
    await registerDocument({
      url,
      title,
    });
  });

  const documentAnnotationList = safeQuerySelector(
    ".document-annotation-list"
  );

  const annotations = await getDocumentAnnotations({
    hash: '' // TODO: Get document hash
  });
  for (const annotation of annotations) {
    console.log(annotation);
  }
};

document.readyState === "complete" ? init() : (window.onload = init);
