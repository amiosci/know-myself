const getApiHost = async () => {
    const apiHost = await chrome.storage.sync.get('kms.apihost');
    return apiHost['kms.apihost'] || 'http://127.0.0.1:5000';
}

const init = async () => {
    const apiHost = await getApiHost();

    const resultsTable = document.querySelector('.results-table');
    Smart('.results-table', class {
        get properties() {
            return {
                sortMode: 'one',
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

    const tasksTable = document.querySelector('.tasks-table');
    Smart('.tasks-table', class {
        get properties() {
            return {
                sortMode: 'one',
                dataSource: new Smart.DataAdapter({
                    dataSource: {
                        method: 'GET',
                        url: `${apiHost}/tasks`,
                        async: false,
                        timeout: null
                    },
                    dataSourceType: 'json',
                    dataFields: [
                        'url: string',
                        'hash: string',
                        'status: string'
                    ]
                }),
                editing: false,
                columns: [
                    { label: 'URL', dataField: 'url', dataType: 'string', allowEdit: false },
                    { label: 'Current status', dataField: 'status', dataType: 'string', allowEdit: false },
                ]
            };
        }
    });
    tasksTable.addEventListener('cellClick', async (e) => {
        const rowHash = e.detail.row.hash;
        const rowUrl = e.detail.row.url;
        const rowStatus = e.detail.row.status;
    });

    const drawerElement = document.querySelector('.sidebar-drawer');
    const openDrawerButton = document.querySelector('.floating-toolbar-open-drawer');
    openDrawerButton.addEventListener('click', () => {
        drawerElement.show();
    });

    const detailsDialog = document.querySelector('.document-dialog');
    const summaryElement = detailsDialog.querySelector('.document-summary-content');
    const urlElement = detailsDialog.querySelector('.document-dialog-url');

    const newWindowButton = detailsDialog.querySelector('.new-window');
    newWindowButton.addEventListener('click', () => {
        detailsDialog.hide();
        window.open(urlElement.textContent);
    });

    resultsTable.addEventListener('cellClick', async (e) => {
        const rowHash = e.detail.row.hash;
        const rowUrl = e.detail.row.url;

        const getSummaryResponse = await fetch(`${apiHost}/summary/${rowHash}`, {
            method: 'GET'
        });

        const summaryResponse = await getSummaryResponse.json();

        summaryElement.textContent = summaryResponse.summary;
        urlElement.textContent = rowUrl;

        detailsDialog.show();
    });

    // settings page
    const settingsDialog = document.querySelector('.settings-dialog');
    const settingsApiHost = document.querySelector('.settings-api-host');

    const settingsSubmitButton = document.querySelector('.settings-submit');
    settingsSubmitButton.addEventListener('click', async () => {
        await chrome.storage.sync.set({'kms.apihost': settingsApiHost.value});

        settingsDialog.hide();
    });

    const settingsCloseButton = document.querySelector('.settings-close');
    settingsCloseButton.addEventListener('click', () => { settingsDialog.hide(); });

    const openSettingsButton = document.querySelector('.settings-open');
    openSettingsButton.addEventListener('click', async () => {
        settingsApiHost.value = await getApiHost();

        settingsDialog.show();
    });
}

document.readyState === 'complete' ? init() : window.onload = init;
