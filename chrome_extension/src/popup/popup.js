const init = async () => {
  const extensionUrl = `chrome-extension://${chrome.runtime.id}`;
  const extensionHome = `${extensionUrl}/index.html`;

  const openSettingsButton = document.querySelector(".open-extension-page");
  openSettingsButton.addEventListener("click", async () => {
    window.open(extensionHome);
  });
};

document.readyState === "complete" ? init() : (window.onload = init);
