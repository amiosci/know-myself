export const createResultsTable = (apiHost) => {
    const resultsTable = document.querySelector('.results-table');
    Smart('.results-table', class {
        get properties() {
            return {
                sortMode: 'one',
                editing: true,
                keyboardNavigation: true,
                dataSource: new Smart.DataAdapter({
                    dataSource: {
                        method: 'GET',
                        url: `${apiHost}/process`,
                        async: false,
                        timeout: null
                    },
                    dataSourceType: 'json',
                    dataFields: [
                        'url: string',
                        'hash: string',
                        'has_summary: bool'
                    ]
                }),
                editing: false,
                columns: [
                    { label: 'URL', dataField: 'url', dataType: 'string', allowEdit: false },
                    { label: 'Hash', dataField: 'hash', dataType: 'string', allowEdit: false },
                    { label: 'Summary Processed', dataField: 'has_summary', dataType: 'string', allowEdit: false },
                ]
            };
        }
    });

    return resultsTable;
};

export const createTasksTable = (apiHost) => {
    const tasksTable = document.querySelector('.tasks-table');
    Smart('.tasks-table', class {
        get properties() {
            return {
                sortMode: 'one',
                dataSource: new Smart.DataAdapter({
                    dataSource: {
                        method: 'GET',
                        url: `${apiHost}/tasks?filter=complete`,
                        async: false,
                        timeout: null
                    },
                    dataSourceType: 'json',
                    dataFields: [
                        'url: string',
                        'hash: string',
                        'task_name: string',
                        'status: string'
                    ]
                }),
                editing: false,
                columns: [
                    { label: 'URL', dataField: 'url', dataType: 'string', allowEdit: false },
                    { label: 'Task Name', dataField: 'task_name', dataType: 'string', allowEdit: false },
                    { label: 'Current status', dataField: 'status', dataType: 'string', allowEdit: false },
                ]
            };
        }
    });

    return tasksTable;
};