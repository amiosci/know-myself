import { getApiHost } from "./utilities";

export const getDocumentSummary = async (documentHash: string) => {
  const apiHost = await getApiHost();
  const getSummaryResponse = await fetch(`${apiHost}/summary/${documentHash}`, {
    method: "GET",
  });

  const summaryResponse = await getSummaryResponse.json();
  return summaryResponse;
};

export const getDocumentEntities = async (documentHash: string) => {
  const apiHost = await getApiHost();
  const getEntitiesResponse = await fetch(
    `${apiHost}/entities/${documentHash}`,
    {
      method: "GET",
    }
  );

  const graphData = await getEntitiesResponse.json();
  return graphData;
};

export const getTaskProcessingResults = async () => {
  const apiHost = await getApiHost();
  const apiResponse = await fetch(`${apiHost}/process`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  const apiResponseBody = await apiResponse.json();
  return apiResponseBody;
};

type ProcessingQueueResponse = {

};
export const getProcessingQueue = async (): Promise<ProcessingQueueResponse> => {
  const apiHost = await getApiHost();
  const apiResponse = await fetch(`${apiHost}/tasks?type=pending&type=failed`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  const apiResponseBody: ProcessingQueueResponse = await apiResponse.json();
  return apiResponseBody;
};

export const getTaskMetrics = async (taskId) => {
  const apiHost = await getApiHost();
  const getTaskMetricsResponse = await fetch(
    `${apiHost}/tasks/${taskId}/metrics`,
    {
      method: "GET",
    }
  );

  const taskMetrics = await getTaskMetricsResponse.json();
  return taskMetrics;
};

export const reprocessTask = async (taskId) => {
  const apiHost = await getApiHost();
  const apiResponse = await fetch(`${apiHost}/tasks/${taskId}/action`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      action: "reprocess",
    }),
  });

  const apiResponseBody = await apiResponse.json();
  return apiResponseBody;
};
