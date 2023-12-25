import { getApiHost, addSafeEventlistener } from "./utilities";
import { configureDetailsDialog } from "./details_dialog";
import { configureSettingsDialog } from './settings_dialog';
import { createResultsTable, createTasksTable } from "./tables";

const init = async () => {
    const apiHost = await getApiHost();

    const tasksTable = createTasksTable(apiHost);
    tasksTable.addEventListener('cellClick', (e) => {
        const rowHash = e.detail.row.hash;
        const rowUrl = e.detail.row.url;
        const rowStatus = e.detail.row.status;
    });

    const resultsTable = createResultsTable(apiHost);

    const openForDocument = configureDetailsDialog();
    configureSettingsDialog();

    addSafeEventlistener(resultsTable, 'cellClick', async (e) => {
        const rowHash = e.detail.row.hash;
        const rowUrl = e.detail.row.url;

        // populate summary content
        const getSummaryResponse = await fetch(`${apiHost}/summary/${rowHash}`, {
            method: 'GET'
        });

        const summaryResponse = await getSummaryResponse.json();

        // populate entities graph
        const getEntitiesResponse = await fetch(`${apiHost}/entities/${rowHash}`, {
            method: 'GET'
        });

        const graphData = await getEntitiesResponse.json();

        openForDocument({
            summary: summaryResponse.summary,
            entities: graphData,
            url: rowUrl,
        });
    });
}

document.readyState === 'complete' ? init() : window.onload = init;
