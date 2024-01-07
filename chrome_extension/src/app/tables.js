import { addSafeEventListener } from "./utilities";
import { getProcessingQueue, getTaskProcessingResults } from "./api";

export const createResultsTable = async () => {
  const resultsTable = document.querySelector(".results-table");
  const resultsTableDataSource = await getTaskProcessingResults();
  Smart(
    ".results-table",
    class {
      get properties() {
        return {
          sortMode: "one",
          editing: true,
          keyboardNavigation: true,
          dataSource: new Smart.DataAdapter({
            dataSource: resultsTableDataSource,
            dataSourceType: "json",
            dataFields: ["url: string", "hash: string", "has_summary: bool"],
          }),
          editing: false,
          columns: [
            {
              label: "URL",
              dataField: "url",
              dataType: "string",
              allowEdit: false,
            },
            {
              label: "Hash",
              dataField: "hash",
              dataType: "string",
              allowEdit: false,
            },
            {
              label: "Summary Processed",
              dataField: "has_summary",
              dataType: "string",
              allowEdit: false,
            },
          ],
        };
      }
    }
  );

  return resultsTable;
};

export const createTasksTable = async ({ onProcessRequest }) => {
  const tasksTable = document.querySelector(".tasks-table");

  const configureSelectionDisabled = () => {
    const retriableStates = ["FAILED", "TIMEOUT"];
    tasksTable.dataSource.dataItemById
      .filter((x) => !retriableStates.includes(x["status"]))
      .map((x) => x.$.index)
      .map((x) => tasksTable.disableSelect(x));
  };

  const pendingTaskDataSource = await getProcessingQueue();
  Smart(
    ".tasks-table",
    class {
      get properties() {
        return {
          sortMode: "one",
          dataSource: new Smart.DataAdapter({
            dataSource: pendingTaskDataSource,
            dataSourceType: "json",
            dataFields: [
              "url: string",
              "hash: string",
              "task_name: string",
              "task_id: string",
              "status: string",
              "status_reason: string",
            ],
          }),
          selection: true,
          editing: false,
          columns: [
            {
              label: "URL",
              dataField: "url",
              dataType: "string",
              allowEdit: false,
            },
            {
              label: "Task Name",
              dataField: "task_name",
              dataType: "string",
              allowEdit: false,
            },
            {
              label: "Current Status",
              dataField: "status",
              dataType: "string",
              allowEdit: false,
            },
            {
              label: "Status Reason",
              dataField: "status_reason",
              dataType: "string",
              allowEdit: false,
            },
          ],
          onLoad: () => {
            configureSelectionDisabled();
          },
        };
      }
    }
  );

  const reprocessButtonElement = document.querySelector(
    ".reprocess-failed-tasks"
  );

  addSafeEventListener(tasksTable, "change", (e) => {
    const selectedTasks = tasksTable.getSelection();
    const disableReprocessButton = selectedTasks.length === 0;
    reprocessButtonElement.disabled = disableReprocessButton;
  });

  addSafeEventListener(reprocessButtonElement, "click", async (e) => {
    const selectedTasks = tasksTable.getSelection();
    const taskIds = selectedTasks.map(
      (x) => tasksTable.dataSource.dataItemById[x]["task_id"]
    );
    await onProcessRequest(taskIds);
  });

  return tasksTable;
};
