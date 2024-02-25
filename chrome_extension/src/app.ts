import { configureDetailsDialog } from "./details_dialog";
import { configureSettingsDialog } from "./settings_dialog";
import { createResultsTable, createTasksTable } from "./tables";
import { getDocumentSummary, getDocumentEntities, reprocessTask } from "./api";

import './app.scss';

const init = async () => {
  const openForDocument = configureDetailsDialog();
  await configureSettingsDialog();

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
};

document.readyState === "complete" ? init() : (window.onload = init);
