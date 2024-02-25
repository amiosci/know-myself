import { addSafeEventListener, safeQuerySelector } from "./utilities";
import { getProcessingQueue, getTaskProcessingResults } from "./api";

import { GridOptions, IRowNode, RowClickedEvent, createGrid } from 'ag-grid-community';
import "ag-grid-community/styles/ag-grid.css";

type ResultsTableEvents = {
  onRowClicked: (rowData: kms.TaskProcessingResult) => void;
}

export const createResultsTable = async (events: ResultsTableEvents) => {
  const resultsTable = safeQuerySelector<HTMLElement>(".results-table");
  const resultsTableData = await getTaskProcessingResults();

  const gridOptions: GridOptions = {
    rowData: resultsTableData, columnDefs: [
      { field: 'url' },
      { field: 'hash' },
      { field: 'has_summary' },
      { field: 'last_updated' },
    ],
    pagination: true,
  };
  const resultsGrid = createGrid<kms.TaskProcessingResult>(resultsTable, gridOptions);

  resultsGrid.addEventListener('rowClicked',
    (event: RowClickedEvent<kms.TaskProcessingResult>) => {
      events.onRowClicked(event.data!);
    });

  return resultsGrid;
};

type CreateTasksTableRequest = {
  onProcessRequest: (taskIds: string[]) => Promise<void>
}

export const createTasksTable = async ({ onProcessRequest }: CreateTasksTableRequest) => {
  const tasksTable = safeQuerySelector<HTMLElement>(".tasks-table");
  const pendingTasksData = await getProcessingQueue();

  const canSelectRow = (rowData: IRowNode<kms.TaskQueueRecord>): boolean => {
    const retriableStates = ["FAILED", "TIMEOUT"];
    return retriableStates.includes(rowData.data!.status);
  };

  const gridOptions: GridOptions<kms.TaskQueueRecord> = {
    rowData: pendingTasksData, columnDefs: [
      { field: 'url' },
      { field: 'task_name' },
      { field: 'status' },
      { field: 'status_reason' },
      { field: 'updated_at' },
    ],
    pagination: true,
    rowMultiSelectWithClick: true,
    rowSelection: 'multiple',
    isRowSelectable: canSelectRow,
  };
  const tasksGrid = createGrid<kms.TaskQueueRecord>(tasksTable, gridOptions);
  const reprocessButtonElement = safeQuerySelector<HTMLButtonElement>(
    ".reprocess-failed-tasks"
  );

  addSafeEventListener(tasksTable, "change", (e) => {
    const selectedTasks = tasksGrid.getSelectedRows();
    const disableReprocessButton = selectedTasks.length === 0;
    reprocessButtonElement.disabled = disableReprocessButton;
  });

  addSafeEventListener(reprocessButtonElement, "click", async (e) => {
    const selectedTasks = tasksGrid.getSelectedRows();
    const taskIds = selectedTasks.map(
      (x) => x.task_id
    );

    debugger;
    await onProcessRequest(taskIds);
  });

  const refreshButtonElement = safeQuerySelector(
    ".refresh-processing-queue"
  );

  addSafeEventListener(refreshButtonElement, "click", async (e) => {
    const updatedDataSource = await getProcessingQueue();
    tasksGrid.updateGridOptions({
      rowData: updatedDataSource
    });
  });

  return tasksTable;
};
