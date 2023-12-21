const apiHost = 'http://127.0.0.1:5000';

const init = () => {
    Smart('#table', class {
        get properties() {
            return {
                sortMode: "one",
                dataSource: new Smart.DataAdapter({
                    dataSource: {
                        method: "GET",
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

    const table = document.querySelector('#table');
    const dialog = document.querySelector('.summary-dialog');
    const newWindowButton = dialog.querySelector('.new-window');
    const summaryElement = dialog.querySelector(".summary-content");
    const urlElement = dialog.querySelector(".summary-dialog-url");

    newWindowButton.addEventListener('click', () => {
        dialog.hide();
        window.open(urlElement.textContent);
    });

    table.addEventListener('cellClick', async (e) => {
        const rowHash = e.detail.row.hash;
        const rowUrl = e.detail.row.url;

        const getSummaryResponse = await fetch(`${apiHost}/summary/${rowHash}`, {
            method: "GET"
        });

        const summaryResponse = await getSummaryResponse.json();

        summaryElement.textContent = summaryResponse.summary;
        urlElement.textContent = rowUrl;

        dialog.show();
    });
}

document.readyState === 'complete' ? init() : window.onload = init;
