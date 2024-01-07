import { getApiHost, addSafeEventListener } from "./utilities";
import { configureDetailsDialog } from "./details_dialog";
import { configureSettingsDialog } from "./settings_dialog";
import { createResultsTable, createTasksTable } from "./tables";
import { getDocumentSummary, getDocumentEntities, reprocessTask } from "./api";

const init = async () => {
  const apiHost = await getApiHost();
  const resultsTable = createResultsTable(apiHost);
  const tasksTable = createTasksTable(apiHost, {
    onProcessRequest: async (taskIds) => {
      await Promise.all(taskIds.map(reprocessTask));
    },
  });

  const openForDocument = configureDetailsDialog();
  await configureSettingsDialog();

  addSafeEventListener(resultsTable, "cellClick", async (e) => {
    const rowHash = e.detail.row.hash;
    const rowUrl = e.detail.row.url;

    const summaryResponse = await getDocumentSummary(rowHash);
    const graphData = await getDocumentEntities(rowHash);

    openForDocument({
      summary: summaryResponse.summary,
      entities: graphData,
      url: rowUrl,
    });
  });
};

document.readyState === "complete" ? init() : (window.onload = init);
