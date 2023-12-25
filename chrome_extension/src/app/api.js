import { getApiHost } from "./utilities";

export const getDocumentSummary = async (documentHash) => {
    const apiHost = await getApiHost();
    const getSummaryResponse = await fetch(`${apiHost}/summary/${documentHash}`, {
        method: 'GET'
    });

    const summaryResponse = await getSummaryResponse.json();
    return summaryResponse;;
};

export const getDocumentEntities = async (documentHash) => {
    const apiHost = await getApiHost();
    const getEntitiesResponse = await fetch(`${apiHost}/entities/${documentHash}`, {
        method: 'GET'
    });

    const graphData = await getEntitiesResponse.json();
    return graphData;
};

export const getTaskMetrics = async (taskId) => {
    const apiHost = await getApiHost();
    const getTaskMetricsResponse = await fetch(`${apiHost}/tasks/${taskId}/metrics`, {
        method: 'GET'
    });

    const taskMetrics = await getTaskMetricsResponse.json();
    return taskMetrics;;
};