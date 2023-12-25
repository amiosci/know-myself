import DirectedGraph from "graphology";
import Sigma from "sigma";
import forceAtlas2 from 'graphology-layout-forceatlas2';
import FA2LayoutSupervisor from "graphology-layout-forceatlas2/worker";
import { connectedComponents, largestConnectedComponent } from 'graphology-components';
import { subgraph } from 'graphology-operators';
import Color from "colorjs.io";

import { removeAllChildNodes, addSafeEventlistener } from "./utilities";

export const configureDetailsDialog = () => {
    const detailsDialog = document.querySelector('.document-dialog');
    const summaryElement = detailsDialog.querySelector('.document-summary-content');
    const entitiesElement = detailsDialog.querySelector('.document-entities-content');
    const urlElement = detailsDialog.querySelector('.document-dialog-url');

    const newWindowButton = detailsDialog.querySelector('.new-window');
    newWindowButton.addEventListener('click', () => {
        detailsDialog.hide();
        window.open(urlElement.textContent);
    });

    // Graph context menu
    const graphContextMenuElement = document.querySelector('.graph-context-menu');
    const resetGraphContextMenu = () => {
        graphContextMenuElement.style.visibility = 'hidden';
        graphContextMenuElement.removeAttribute('selected-node');
    };

    addSafeEventlistener(graphContextMenuElement, 'sl-select', (event) => {
        const item = event.detail.item.value;
        const node = graphContextMenuElement.getAttribute('selected-node');
        console.log(`${node}: ${item}`);

        resetGraphContextMenu();
    });

    const graphContainerElement = detailsDialog.querySelector('.entity-graph-container');
    let graphRenderer = null;

    // reset dialog elements after animations finalize
    addSafeEventlistener(detailsDialog, 'sl-after-hide', (_) => {
        graphRenderer?.kill();
        graphRenderer = null;

        summaryElement.hide();
        entitiesElement.hide();

        removeAllChildNodes(graphContainerElement);
    });

    const renderGraphByName = (element, documentGraph, components) => {
        const componentGraph = subgraph(documentGraph, components);
        if (graphRenderer !== null) {
            debugger;
        }

        const primaryNode = largestConnectedComponent(componentGraph)[0];
        const graphSettings = forceAtlas2.inferSettings(componentGraph);
        const layout = new FA2LayoutSupervisor(componentGraph, {
            iterations: 5,
            settings: graphSettings,
        });

        layout.start();

        const state = {};
        graphRenderer = new Sigma(componentGraph, element, {
            nodeProgramClasses: {},
            edgeProgramClasses: {},
            // TODO: Remove and fix tab loading
            allowInvalidContainer: true,
            renderEdgeLabels: true,
            enableEdgeClickEvents: true,
        });
        const mouseCaptor = graphRenderer.getMouseCaptor();

        // highlight topic node by default
        componentGraph.setNodeAttribute(primaryNode, 'highlighted', true);

        const getNodeAtCoordinate = ({ x, y }) => {
            const nodeDistances = componentGraph.mapNodes((_, attr) => {
                const positionDeltas = {
                    x: Math.abs(attr.x - x),
                    y: Math.abs(attr.y - y)
                };

                const distance = positionDeltas.x * positionDeltas.y;
                return distance;
            });

            const closestNodeDistance = Math.min(...nodeDistances);
            const closestNodeIndex = nodeDistances.indexOf(closestNodeDistance);

            // roughly within the boundaries of the node
            const minimumDistance = 1;
            const distanceTolerance = 0.1;
            const nodeInContext = closestNodeDistance - minimumDistance < distanceTolerance;
            return [componentGraph.nodes()[closestNodeIndex], closestNodeDistance, nodeInContext];
        }

        const getEdgeAtCoordinate = ({ x, y }) => {
            // TODO: edge calculation requires recalculating line between node attributes and testing collision
            //          no position data is maintained for edges
            return ['', Number.POSITIVE_INFINITY]
        }

        // left-click removes any active context menu
        graphRenderer.on('clickStage', (_) => {
            resetGraphContextMenu();
        });

        // right-click adds context-menu if there is an intent to select a node
        mouseCaptor.addListener("rightClick", (event) => {
            event.preventSigmaDefault();
            event.original.preventDefault();

            // TODO: Make node events work on sigmajs
            const clickedPosition = graphRenderer.viewportToGraph(event);
            const [closestNode, _, nodeInContext] = getNodeAtCoordinate(clickedPosition);

            // always reset style before conditionally reparenting it
            resetGraphContextMenu();
            if (nodeInContext) {
                console.log(`creating context menu for ${closestNode}`);

                const canvasCoords = {
                    x: event.x,
                    y: event.y
                };

                graphContextMenuElement.setAttribute('selected-node', closestNode);

                // add context menu
                graphRenderer.getContainer().appendChild(graphContextMenuElement);
                Object.assign(graphContextMenuElement.style, {
                    left: `${Math.abs(canvasCoords.x)}px`,
                    top: `${Math.abs(canvasCoords.y)}px`,
                    visibility: 'initial',
                    position: 'absolute',
                });
            }
        });
        // fix support for node clicks
        mouseCaptor.addListener("click", (event) => {
            event.preventSigmaDefault();
            event.original.preventDefault();

            // TODO: test node events after sigmajs 3.0 exits beta
            const clickedPosition = graphRenderer.viewportToGraph(event);
            const [closestNode, nodeDistance, nodeInContext] = getNodeAtCoordinate(clickedPosition);

            if (nodeInContext) {
                console.log(`Toggling selection of node (${closestNode}: ${nodeDistance})`);
                const isHighlighted = !(componentGraph.getNodeAttribute(closestNode, 'highlighted') ?? false);
                componentGraph.setNodeAttribute(closestNode, 'highlighted', isHighlighted);
            }
        });
        // remove context-menu if you are moving the body
        mouseCaptor.addListener('mousemove', (event) => {
            const moving =
                graphRenderer.getCamera().isAnimated() ||
                mouseCaptor.isMoving ||
                mouseCaptor.draggedEvents ||
                mouseCaptor.currentWheelDirection;

            if (moving) {
                resetGraphContextMenu();
            }
        });

        // make labels slightly more legible
        graphRenderer.getCamera().setState({
            angle: 0.2,
        });

        // non-stage events won't work. Log them all until they do!
        const logEvent = (event, itemType, item, onMessage = console.log) => {
            let message = `Event "${event}"`;
            if (item && itemType) {
                const label = itemType === "node" ? componentGraph.getNodeAttribute(item, "label") : componentGraph.getEdgeAttribute(item, "label");
                message += `, ${itemType} ${label || "with no label"} (id "${item}")`;

                if (itemType === "edge") {
                    message += `, source ${componentGraph.getSourceAttribute(item, "label")}, target: ${componentGraph.getTargetAttribute(
                        item,
                        "label",
                    )}`;
                }
            }

            onMessage(message);
        }

        [
            "enterNode",
            "leaveNode",
            "downNode",
            "clickNode",
            "rightClickNode",
            "doubleClickNode",
            "wheelNode",
        ].forEach((eventType) => graphRenderer.on(eventType, ({ node }) => logEvent(eventType, "node", node)));

        [
            "downEdge",
            "clickEdge",
            "rightClickEdge",
            "doubleClickEdge",
            "wheelEdge",
            "enterEdge",
            "leaveEdge",
        ].forEach((eventType) => graphRenderer.on(eventType, ({ edge }) => logEvent(eventType, "edge", edge)));
    };

    const openForDocument = ({ summary, entities, url }) => {
        summaryElement.textContent = summary;
        urlElement.textContent = url;

        if (entities.length === 0) {
            entitiesElement.setAttribute('disabled', true);
        } else {
            entitiesElement.removeAttribute('disabled');
            const [graph, graphTabMap] = loadGraph(entities);

            // TODO: Support single entity mode?
            // tab mode
            const graphTabGroup = document.createElement('sl-tab-group');
            graphTabGroup.setAttribute('placement', 'start');
            graphContainerElement.appendChild(graphTabGroup);

            // render graph on tab change
            graphTabGroup.addEventListener('sl-tab-show', (event) => {
                const name = event.detail.name;
                const graphElement = detailsDialog.querySelector(`sl-tab-panel[name="${name}"]`).querySelector('.entity-graph');
                renderGraphByName(graphElement, graph, graphTabMap[name]);
            });

            // dispose graph handlers
            graphTabGroup.addEventListener('sl-tab-hide', (event) => {
                const name = event.detail.name;
                graphRenderer?.kill();
                graphRenderer = null;
            });

            // create tab per graph
            for (const [tabName, _] of Object.entries(graphTabMap)) {
                const graphTabElement = document.createElement('sl-tab');
                graphTabElement.setAttribute('slot', 'nav');
                graphTabElement.setAttribute('panel', tabName);
                graphTabElement.innerText = tabName;
                graphTabGroup.appendChild(graphTabElement);

                // create panel content
                const graphTabContentElement = document.createElement('sl-tab-panel');
                graphTabContentElement.setAttribute('name', tabName);
                graphTabGroup.appendChild(graphTabContentElement);

                // create graph container
                const graphElement = document.createElement('div');
                graphElement.classList.add('entity-graph');
                graphTabContentElement.appendChild(graphElement);
            }

            // Render graph on the newly displayed tab
            const entitiesAfterShowEvent = (event) => {
                // prevent internal events from bubbing into dialog closure handler
                if (event.target !== entitiesElement) {
                    return;
                }

                const name = detailsDialog.querySelector(`sl-tab[active]`).textContent;
                const graphElement = detailsDialog.querySelector(`sl-tab-panel[name="${name}"]`).querySelector('.entity-graph');
                renderGraphByName(graphElement, graph, graphTabMap[name]);
                graphRenderer.refresh();
            };
            entitiesElement.addEventListener('sl-after-show', entitiesAfterShowEvent);

            // stop graph rendering when display is collapsed
            const entitiesHideEvent = (event) => {
                // prevent internal events from bubbing into dialog closure handler
                if (event.target !== entitiesElement) {
                    return;
                }

                graphRenderer?.kill();
                graphRenderer = null;
            };
            entitiesElement.addEventListener('sl-hide', entitiesHideEvent);

            // remove graph-bound events on dialog closure
            detailsDialog.addEventListener('sl-after-hide', (event) => {
                if (event.target !== detailsDialog) {
                    return;
                }

                entitiesElement.removeEventListener('sl-after-show', entitiesAfterShowEvent);
                entitiesElement.removeEventListener('sl-hide', entitiesHideEvent);
            });
        }

        detailsDialog.show();

    };

    return openForDocument;
};

const loadGraph = (graphData) => {
    const graph = new DirectedGraph({
        multi: true,
    });

    const BLUE = new Color("#727EE0");
    const RED = new Color("#FA4F40");

    for (const node of graphData) {
        ['entity', 'target'].forEach((nodeProperty) => {
            if (!graph.hasNode(node[nodeProperty])) {
                graph.addNode(node[nodeProperty], {
                    size: 10,
                    label: node[nodeProperty],
                });
            }
        });

        graph.addEdge(node['target'], node['entity'], {
            type: "line",
            label: node['relationship'],
            size: 2,
        });
    }

    const connectionMap = {};
    let maxConnections = 0;

    graph.forEachEdge((edge, attributes, source, target, sourceAttributes, targetAttributes, undirected) => {
        const nodeConnections = (connectionMap[target] ?? 0) + 1;
        connectionMap[target] = nodeConnections;
        maxConnections = Math.max(nodeConnections, maxConnections);
        targetAttributes.size += 1;
    });

    const nodeColorRange = BLUE.steps(RED, {
        outputSpace: 'srgb',
        // Add 1 to support nodes without connections
        steps: maxConnections + 1
    });

    let i = 1;
    graph.forEachNode((node, attributes) => {
        // no record exists if the node isn't a target
        const nodeColorIndex = connectionMap[node] ?? 0;
        const nodeColorHex = nodeColorRange[nodeColorIndex].toString({ format: "hex" });

        const phi = ((i++) * 2 * Math.PI) / graph.order;
        const positionMultiplier = 100;

        attributes.x = positionMultiplier * Math.cos(phi);
        attributes.y = positionMultiplier * Math.sin(phi);
        attributes.color = nodeColorHex;
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