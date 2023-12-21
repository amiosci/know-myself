const apiHost = 'http://127.0.0.1:5000';

const init = () => {
    // Init table
    Smart('#table', class {
        get properties() {
            return {
                sortMode: "one",
                dataSource: new Smart.DataAdapter({
                    dataSource: {
                        method: "GET",
                        url: `${apiHost}/process`,
                        async: false,

                        // also default
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

    table.addEventListener('cellClick', async (e) => {
        const rowHash = e.detail.row.hash;
        const rowUrl = e.detail.row.url;

        const getSummaryResponse = await fetch(`${apiHost}/summary/${rowHash}`, {
            method: "GET"
        }
        );
        const summaryResponse = await getSummaryResponse.json();

        const dialog = document.getElementById("summaryDialog");
        const summaryElement = dialog.querySelector("#summary");
        summaryElement.textContent = summaryResponse.summary;

        const urlElement = dialog.querySelector("#dialog_url")
        urlElement.textContent = rowUrl;

        dialog.showModal();
        dialog.querySelector("#cancel").addEventListener("click", () => {
            dialog.close();
        });

        dialog.querySelector("#open").addEventListener("click", () => {
            dialog.close();
            window.open(rowUrl);
        });
    });
}

document.readyState === 'complete' ? init() : window.onload = init;
