import Graph from "graphology";
import Sigma from "sigma";
import ForceSupervisor from "graphology-layout-force/worker";
import getNodeProgramImage from "sigma/rendering/programs/node-image";

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
                editing: true,
                // selection: true,
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
    const entitiesElement = detailsDialog.querySelector('.document-entities-content');
    const urlElement = detailsDialog.querySelector('.document-dialog-url');

    const RED = "#FA4F40";
    const BLUE = "#727EE0";
    const GREEN = "#5DB346";

    const graphElement = document.querySelector('.entity-graph');
    let renderer = null;

    // reset dialog elements after animations finalize
    detailsDialog.addEventListener('sl-after-hide', (event) => {
        if (event.target !== detailsDialog) {
            return;
        }

        renderer?.kill();
        renderer = null;
        summaryElement.hide();
        entitiesElement.hide();
    });

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

        const getEntitiesResponse = await fetch(`${apiHost}/entities/${rowHash}`, {
            method: 'GET'
        });

        const graphData = await getEntitiesResponse.json();

        const graph = new Graph({
            multi: true,
        });
        const n = graphData.length;
        for (const node of graphData) {
            ['entity', 'target'].forEach((nodeProperty) => {
                if (!graph.hasNode(node[nodeProperty])) {
                    graph.addNode(node[nodeProperty], {
                        size: 15,
                        label: node[nodeProperty],
                        color: RED,
                    });
                }
            });

            graph.addEdge(node['entity'], node['target'], {
                type: "line",
                label: node['relationship'],
                size: 20,
            });
        }

        graph.nodes().forEach((node, i) => {
            const angle = (i * 2 * Math.PI) / graph.order;
            graph.setNodeAttribute(node, "x", 100 * Math.cos(angle));
            graph.setNodeAttribute(node, "y", 100 * Math.sin(angle));
        });

        const layout = new ForceSupervisor(graph);
        renderer = new Sigma(graph, graphElement, {
            nodeProgramClasses: {
                image: getNodeProgramImage(),
                // border: NodeProgramBorder,
            },
            allowInvalidContainer: true,
            renderEdgeLabels: true,
        });

        layout.start();

        summaryElement.textContent = summaryResponse.summary;
        urlElement.textContent = rowUrl;

        detailsDialog.show();
    });

    // settings page
    const settingsDialog = document.querySelector('.settings-dialog');
    const settingsApiHost = document.querySelector('.settings-api-host');

    const settingsSubmitButton = document.querySelector('.settings-submit');
    settingsSubmitButton.addEventListener('click', async () => {
        await chrome.storage.sync.set({ 'kms.apihost': settingsApiHost.value });

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
