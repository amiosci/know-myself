export const registerDocument = async ({ url, title }) => {
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

export const addDocumentAnnotation = async ({ hash, annotation }) => {
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

export const getDocumentAnnotation = async ({ hash }) => {
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

export const removeDocumentAnnotation = async ({ hash, annotation }) => {
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

const getApiHost = async () => {
  const apiHost = await chrome.storage.sync.get("kms.apihost");
  return apiHost["kms.apihost"] || "http://127.0.0.1:5000";
};
