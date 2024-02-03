import * as shoelace from '@shoelace-style/shoelace';
import { getApiHost } from "./utilities";

export const configureSettingsDialog = async () => {
  const settingsDialog: shoelace.SlDialog = document.querySelector(".settings-dialog");
  const settingsApiHost: shoelace.SlInput = settingsDialog.querySelector(".settings-api-host");

  const settingsSubmitButton = settingsDialog.querySelector(".settings-submit");
  settingsSubmitButton.addEventListener("click", async () => {
    await chrome.storage.sync.set({ "kms.apihost": settingsApiHost.value });

    settingsDialog.hide();
  });

  const settingsCloseButton = settingsDialog.querySelector(".settings-close");
  settingsCloseButton.addEventListener("click", () => {
    settingsDialog.hide();
  });

  const openSettingsButton = document.querySelector(".settings-open");
  openSettingsButton.addEventListener("click", async () => {
    settingsApiHost.value = await getApiHost();

    settingsDialog.show();
  });
};
