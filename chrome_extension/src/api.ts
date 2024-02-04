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

export const getTaskProcessingResults = async (): Promise<kms.TaskProcessingResult[]> => {
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

export const getProcessingQueue = async (): Promise<kms.TaskQueueRecord[]> => {
  const apiHost = await getApiHost();
  const apiResponse = await fetch(`${apiHost}/tasks?type=pending&type=failed`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  const apiResponseBody = await apiResponse.json();
  return apiResponseBody;
};

export const getTaskMetrics = async (taskId: string) => {
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

export const reprocessTask = async (taskId: string) => {
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

export const registerDocument = async ({ url, title }: kms.CreateDocumentRequest) => {
  const apiHost = await getApiHost();
  const registerResultResponse = await fetch(`${apiHost}/process`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      url: url,
      title: title,
    }),
  });

  const resultResponseBody = await registerResultResponse.json();
  console.log(resultResponseBody);
  return resultResponseBody["hash"];
};

export const addDocumentAnnotation = async ({ hash, annotation }: kms.DocumentReference) => {
  const apiHost = await getApiHost();
  const addAnnotationResponse = await fetch(
    `${apiHost}/documents/${hash}/annotations`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        annotation: annotation,
      }),
    }
  );

  const responseBody = await addAnnotationResponse.json();
  console.log(responseBody);
};

export const getDocumentAnnotation = async ({ hash }: kms.DocumentReference) => {
  const apiHost = await getApiHost();
  const getAnnotationResponse = await fetch(
    `${apiHost}/documents/${hash}/annotations`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  const responseBody = await getAnnotationResponse.json();
  console.log(responseBody);
  return responseBody["annotations"];
};

export const removeDocumentAnnotation = async ({ hash, annotation }: kms.DocumentReference) => {
  const apiHost = await getApiHost();
  const removeAnnotationResponse = await fetch(
    `${apiHost}/documents/${hash}/annotations`,
    {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        annotation: annotation,
      }),
    }
  );

  const responseBody = await removeAnnotationResponse.json();
  console.log(responseBody);
};

export const getDocumentAnnotations = async ({ hash }: kms.DocumentReference) => {
  const apiHost = await getApiHost();
  const getAnnotationResponse = await fetch(
    `${apiHost}/documents/${hash}/annotations`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  const responseBody = await getAnnotationResponse.json();
  console.log(responseBody);
  return responseBody["annotations"];
};
