## Know MySelf

With KMS you can run a local [langchain](https://api.python.langchain.com/en/stable/langchain_api_reference.html)-based processing pipeline on documents originated from Chrome browsing experience.

### Description

Using [Ollama](https://github.com/jmorganca/ollama), this provides a local-only experience with direct integration into your daily browsing experience. The documents are cached into a local filesystem to support reprocessing against new prompts/models/APIs.

Redis and Postgres are used for the Celery task backend, and persistence layer respectively.

Current integrations support summarization.

#### Desired/In Progress pipeline integrations

[] Knowledge graph generation
  [x] Entity Relation Extraction with persistence
  [] "Encourage hallucinations -> fact check entity relations" loops to discover novel connections?
[] Multi-modal integrations over content
  [] Capture non-text content/use multi-modal extraction approaches
  [x] Support image QA

#### Desired/In Progress web extension integrations

[] Annotating tabs by context-menu over selected text
[] Bookmark folder watching, in addition to reading list
[] Firefox integration (builder already supports)
[] Knowledge graph integration
  [x] Expose entity relations
  [x] Support graph node click events
  [x] Support graph context menu
  [] Find supporting/contradicting documents
[] Conversational web browsing
  [] Asking for supplementary details
  [] Fact checking the selection
  [] Support realm-based personas

### Current recommended usage

This was developed on a single device, and currently encourages the API and an instance of the Chrome extension running on a device with a sufficient GPU to run large ML models (developed against a 16GB 4080).

With the chrome extension loaded and not installed through your profile, any changes to the tracked resources (Reading List currently) will automatically be ingested and available through the pinned extension tab. This provides a mobile-friendly experience to adding articles/documents to the processing pipeline solely through your cross-device synced Chrome profile.

### How to run

#### Prerequisites

* Python 3.11
  * Virtual environment recommended
* Docker
* Pwsh
* A GPU that supports large ML models

#### Start backend

`pwsh ./run_backend.ps1`

This will start a locally backed up Postgres and Redis server.

#### Run API server

Configure virtualenv
`PIPENV_VENV_IN_PROJECT=1 pipenv install`

`flask --app api/flask_app.py run`

This will start the local API that is used by the Web Browser extension.

#### Run processing server

`cd api; celery --app celery_app worker --loglevel INFO --concurrency=1`

Note: `--concurrency=1` is recommended to reduce burden on the system while running large ML models.

By using a network-addressible backends (Redis, Postgres, DocumentStore), this can be run on multiple devices capable of running these models. This scaling factor is limited by Celery.

#### Run Chrome extension

`cd chrome_extension; npm start`


#### Run Firefox extension

**Not implemented**

`cd chrome_extension; npm run start:firefox`

**Not implemented**

#### Cleanup TODO
[x] Trim exported `requirements.txt`
