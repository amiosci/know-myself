import { configureDetailsDialog } from "./details_dialog";
import { configureSettingsDialog } from "./settings_dialog";
import { createResultsTable, createTasksTable } from "./tables";
import { getDocumentSummary, getDocumentEntities, reprocessTask } from "./api";

const init = async () => {
  const openForDocument = configureDetailsDialog();

  await createResultsTable({
    onRowClicked: async (rowData: kms.TaskProcessingResult) => {
      const rowHash = rowData.hash;
      const rowUrl = rowData.url;

      const summaryResponse = await getDocumentSummary(rowHash);
      const graphData = await getDocumentEntities(rowHash);

      openForDocument({
        summary: summaryResponse.summary,
        entities: graphData,
        url: rowUrl,
      });
    }
  });

  await createTasksTable({
    onProcessRequest: async (taskIds: string[]) => {
      await Promise.all(taskIds.map(reprocessTask));
    },
  });

  await configureSettingsDialog();
};

document.readyState === "complete" ? init() : (window.onload = init);
