export const getDocumentAnnotations = async ({ hash }) => {
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

export const registerDocument = async ({ url, title }) => {
  const protocol = url.split("//")[0];
  if (protocol.indexOf("chrome") > -1) {
    return;
  }

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
  const hash = resultResponseBody["hash"];
  console.log(`${hash}: ${url}`);
  return hash;
};

const getApiHost = async () => {
  const apiHost = await chrome.storage.sync.get("kms.apihost");
  return apiHost["kms.apihost"] || "http://127.0.0.1:5000";
};
