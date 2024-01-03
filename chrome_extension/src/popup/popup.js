import { registerDocument } from "./api";

const getCurrentTab = async () => {
  const queryOptions = { active: true, lastFocusedWindow: true };
  const [tab] = await chrome.tabs.query(queryOptions);
  console.log(tab);
  return tab;
};

const init = async () => {
  const extensionUrl = `chrome-extension://${chrome.runtime.id}`;
  const extensionHome = `${extensionUrl}/index.html`;

  const openSettingsButton = document.querySelector(".open-extension-page");
  openSettingsButton.addEventListener("click", async () => {
    window.open(extensionHome);
  });

  const processCurrentPageButton = document.querySelector(
    ".process-current-page"
  );
  processCurrentPageButton.addEventListener("click", async () => {
    const { title, url } = await getCurrentTab();
    await registerDocument({
      url,
      title,
    });
  });
};

document.readyState === "complete" ? init() : (window.onload = init);
