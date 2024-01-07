import { addSafeEventListener } from "./utilities";

export const createResultsTable = (apiHost) => {
  const resultsTable = document.querySelector(".results-table");
  Smart(
    ".results-table",
    class {
      get properties() {
        return {
          sortMode: "one",
          editing: true,
          keyboardNavigation: true,
          dataSource: new Smart.DataAdapter({
            dataSource: {
              method: "GET",
              url: `${apiHost}/process`,
              async: false,
              timeout: null,
            },
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

export class TaskTableEventHandler {}

export const createTasksTable = (apiHost, { onProcessRequest }) => {
  const tasksTable = document.querySelector(".tasks-table");

  const configureSelectionEnabled = () => {
    tasksTable.enableSelect(
      tasksTable.dataSource.dataItemById
        .filter((x) => ["FAILED", "TIMEOUT"].includes(x["status"]))
        .map((x) => x.boundIndex)
    );
  };
  Smart(
    ".tasks-table",
    class {
      get properties() {
        return {
          sortMode: "one",
          dataSource: new Smart.DataAdapter({
            dataSource: {
              method: "GET",
              url: `${apiHost}/tasks?filter=complete`,
              async: false,
              timeout: null,
            },
            dataSourceType: "json",
            dataFields: [
              "url: string",
              "hash: string",
              "task_name: string",
              "task_id: string",
              "status: string",
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
              label: "Current status",
              dataField: "status",
              dataType: "string",
              allowEdit: false,
            },
          ],
          onLoad: () => {
            configureSelectionEnabled();
          },
        };
      }
    }
  );

  const reprocessButtonElement = document.querySelector(
    ".reproces-failed-tasks"
  );

  addSafeEventListener(tasksTable, "cellClick", (e) => {
    const rowHash = e.detail.row.hash;
    const rowUrl = e.detail.row.url;
    const rowStatus = e.detail.row.status;
    const rowTaskId = e.detail.row.taskId;
    const rowId = e.detail.id;

    const selectedTasks = tasksTable.getSelection();
    const hasPreviousSelected = selectedTasks.length > 0;
    let enableReprocessButton = true;
    if (hasPreviousSelected) {
      const hasSingleSelected = selectedTasks.length === 1;
      if (hasSingleSelected && selectedTasks[0] == rowId) {
        enableReprocessButton = false;
      }
    }

    reprocessButtonElement.disabled = !enableReprocessButton;
  });

  addSafeEventListener(tasksTable, "page", (e) => {
    // maybe not needed now?
    configureSelectionEnabled();
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
