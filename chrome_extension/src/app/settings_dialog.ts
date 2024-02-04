import * as shoelace from '@shoelace-style/shoelace';
import { getApiHost, safeQuerySelector, addSafeEventListener } from "../utilities";

export const configureSettingsDialog = async () => {
  const settingsDialog: shoelace.SlDialog = safeQuerySelector(".settings-dialog");
  const settingsApiHost: shoelace.SlInput = safeQuerySelector(".settings-api-host", settingsDialog);

  const settingsSubmitButton = safeQuerySelector(".settings-submit", settingsDialog);
  addSafeEventListener(settingsSubmitButton, "click", async () => {
    await chrome.storage.sync.set({ "kms.apihost": settingsApiHost.value });

    settingsDialog.hide();
  });

  const settingsCloseButton = safeQuerySelector(".settings-close", settingsDialog);
  addSafeEventListener(settingsCloseButton, "click", () => {
    settingsDialog.hide();
  });

  const openSettingsButton = safeQuerySelector(".settings-open");
  addSafeEventListener(openSettingsButton, "click", async () => {
    settingsApiHost.value = await getApiHost();

    settingsDialog.show();
  });
};
