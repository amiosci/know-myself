import DirectedGraph from "graphology";
import Sigma from "sigma";
import ForceSupervisor from "graphology-layout-force/worker";
import { connectedComponents } from 'graphology-components';
import { subgraph } from 'graphology-operators';
import Color from "colorjs.io";

const getApiHost = async () => {
    const apiHost = await chrome.storage.sync.get('kms.apihost');
    return apiHost['kms.apihost'] || 'http://127.0.0.1:5000';
}

const removeAllChildNodes = (parent) => {
    while (parent.firstChild) {
        parent.removeChild(parent.firstChild);
    }
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

    const detailsDialog = document.querySelector('.document-dialog');
    const summaryElement = detailsDialog.querySelector('.document-summary-content');
    const entitiesElement = detailsDialog.querySelector('.document-entities-content');
    const urlElement = detailsDialog.querySelector('.document-dialog-url');

    const graphContainerElement = document.querySelector('.entity-graph-container');
    let graphRenderer = null;

    // reset dialog elements after animations finalize
    detailsDialog.addEventListener('sl-after-hide', (event) => {
        if (event.target !== detailsDialog) {
            return;
        }

        graphRenderer?.kill();
        graphRenderer = null;

        summaryElement.hide();
        entitiesElement.hide();

        removeAllChildNodes(graphContainerElement);
    });

    const newWindowButton = detailsDialog.querySelector('.new-window');
    newWindowButton.addEventListener('click', () => {
        detailsDialog.hide();
        window.open(urlElement.textContent);
    });

    const BLUE = new Color("#727EE0");
    const RED = new Color("#FA4F40");

    const loadGraph = (graphData) => {
        const graph = new DirectedGraph({
            multi: true,
        });

        for (const node of graphData) {
            ['entity', 'target'].forEach((nodeProperty) => {
                if (!graph.hasNode(node[nodeProperty])) {
                    graph.addNode(node[nodeProperty], {
                        size: 15,
                        label: node[nodeProperty],
                    });
                }
            });

            graph.addEdge(node['entity'], node['target'], {
                type: "line",
                label: node['relationship'],
                size: 2,
            });
        }

        const connectionMap = {};
        let maxConnections = 0;
        [...graph.edgeEntries()].forEach(graphEdge => {
            const target = graphEdge.target;

            const nodeConnections = (connectionMap[target] ?? 0) + 1;
            connectionMap[target] = nodeConnections;
            maxConnections = Math.max(nodeConnections, maxConnections);
        });

        const nodeColorRange = BLUE.steps(RED, {
            outputSpace: 'srgb',
            // Add 1 to support nodes without connections
            steps: maxConnections + 1
        });

        // set default positions
        graph.nodes().forEach((node, i) => {
            const angle = (i * 2 * Math.PI) / graph.order;

            // no record exists if the node isn't a target
            const nodeColorIndex = connectionMap[node] ?? 0;
            const nodeColorHex = nodeColorRange[nodeColorIndex].toString({ format: "hex" });

            graph.setNodeAttribute(node, "x", 100 * Math.cos(angle));
            graph.setNodeAttribute(node, "y", 100 * Math.sin(angle));
            graph.setNodeAttribute(node, "color", nodeColorHex);
        });

        // Render relevant graphs
        const componentMinimumSize = 3;
        const componentNodes = connectedComponents(graph).filter(x => x.length >= componentMinimumSize);

        const graphTabMap = {};
        for (const component of componentNodes) {
            component.sort((x, y) => (connectionMap[y] ?? 0) - (connectionMap[x] ?? 0));
            const primaryNode = component[0];
            graphTabMap[primaryNode] = component;
        }


        return [graph, graphTabMap];
    };

    const renderGraphByName = (element, graph, components) => {
        let draggedNode = null;
        const componentGraph = subgraph(graph, components);
        if (graphRenderer !== null) {
            debugger;
        }

        const layout = new ForceSupervisor(componentGraph, {
            isNodeFixed: (_, attr) => attr.highlighted
        });

        layout.start();

        graphRenderer = new Sigma(componentGraph, element, {
            nodeProgramClasses: {},
            edgeProgramClasses: {},
            allowInvalidContainer: true,
            renderEdgeLabels: true,
        });

        graphRenderer.on("downNode", (e) => {
            debugger;
            draggedNode = e.node;
            componentGraph.setNodeAttribute(draggedNode, "highlighted", true);
        });

        graphRenderer.getMouseCaptor().on("mouseup", () => {
            debugger;
            if (draggedNode) {
                componentGraph.removeNodeAttribute(draggedNode, "highlighted");
            }

            draggedNode = null;
        });
    }


    resultsTable.addEventListener('cellClick', async (e) => {
        const rowHash = e.detail.row.hash;
        const rowUrl = e.detail.row.url;

        const getSummaryResponse = await fetch(`${apiHost}/summary/${rowHash}`, {
            method: 'GET'
        });

        const summaryResponse = await getSummaryResponse.json();

        summaryElement.textContent = summaryResponse.summary;
        urlElement.textContent = rowUrl;

        const getEntitiesResponse = await fetch(`${apiHost}/entities/${rowHash}`, {
            method: 'GET'
        });

        const graphData = await getEntitiesResponse.json();

        if (graphData.length === 0) {
            entitiesElement.setAttribute('disabled', true);
        } else {
            entitiesElement.removeAttribute('disabled');
            const [graph, graphTabMap] = loadGraph(graphData);

            // tab mode
            const graphTabGroup = document.createElement('sl-tab-group');
            graphTabGroup.setAttribute('placement', 'start');
            graphContainerElement.appendChild(graphTabGroup);

            graphTabGroup.addEventListener('sl-tab-show', (event) => {
                const name = event.detail.name;
                const graphElement = detailsDialog.querySelector(`sl-tab-panel[name="${name}"]`).querySelector('.entity-graph');
                renderGraphByName(graphElement, graph, graphTabMap[name]);
            });

            graphTabGroup.addEventListener('sl-tab-hide', (event) => {
                const name = event.detail.name;
                graphRenderer?.kill();
                graphRenderer = null;
            });

            for (const [tabName, _] of Object.entries(graphTabMap)) {
                const graphTabElement = document.createElement('sl-tab');
                graphTabElement.setAttribute('slot', 'nav');
                graphTabElement.setAttribute('panel', tabName);
                graphTabElement.innerText = tabName;
                graphTabGroup.appendChild(graphTabElement);

                const graphTabContentElement = document.createElement('sl-tab-panel');
                graphTabContentElement.setAttribute('name', tabName);
                graphTabGroup.appendChild(graphTabContentElement);

                const graphElement = document.createElement('div');
                graphElement.classList.add('entity-graph');
                graphTabContentElement.appendChild(graphElement);
            }

            const entitiesAfterShowEvent = (event) => {
                // prevent internal events from bubbing into dialog closure handler
                if (event.target !== entitiesElement) {
                    return;
                }

                const name = detailsDialog.querySelector(`sl-tab[active]`).textContent;
                const graphElement = detailsDialog.querySelector(`sl-tab-panel[name="${name}"]`).querySelector('.entity-graph');
                renderGraphByName(graphElement, graph, graphTabMap[name]);
            };
            entitiesElement.addEventListener('sl-after-show', entitiesAfterShowEvent);

            const entitiesHideEvent = (event) => {
                // prevent internal events from bubbing into dialog closure handler
                if (event.target !== entitiesElement) {
                    return;
                }

                graphRenderer?.kill();
                graphRenderer = null;
            };
            entitiesElement.addEventListener('sl-hide', entitiesHideEvent);

            detailsDialog.addEventListener('sl-after-hide', (event) => {
                if (event.target !== detailsDialog) {
                    return;
                }

                entitiesElement.removeEventListener('sl-after-show', entitiesAfterShowEvent);
                entitiesElement.removeEventListener('sl-hide', entitiesHideEvent);
            })
        }

        summaryElement.textContent = summaryResponse.summary;
        urlElement.textContent = rowUrl;

        detailsDialog.show();
    });

    // settings page
    const settingsDialog = document.querySelector('.settings-dialog');
    const settingsApiHost = settingsDialog.querySelector('.settings-api-host');

    const settingsSubmitButton = settingsDialog.querySelector('.settings-submit');
    settingsSubmitButton.addEventListener('click', async () => {
        await chrome.storage.sync.set({ 'kms.apihost': settingsApiHost.value });

        settingsDialog.hide();
    });

    const settingsCloseButton = settingsDialog.querySelector('.settings-close');
    settingsCloseButton.addEventListener('click', () => { settingsDialog.hide(); });

    const openSettingsButton = document.querySelector('.settings-open');
    openSettingsButton.addEventListener('click', async () => {
        settingsApiHost.value = await getApiHost();

        settingsDialog.show();
    });
}

document.readyState === 'complete' ? init() : window.onload = init;
