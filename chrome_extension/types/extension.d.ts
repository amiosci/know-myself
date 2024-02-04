declare namespace kms {
    export interface EntityRelation {
        [key: string]: string
        entity: string
        target: string
        relationship: string
    }

    export interface CreateDocumentRequest {
        url: string
        title: string
    }

    export interface DocumentReference {
        hash: string
        annotation?: string
    }

    export interface RecorderRequest {
        type: "start-recording" | "stop-recording"
        target: string

        // The target frame identifier
        data: number
    }

    export interface RecorderResponse {
        type: "recording-completed"
        target: "recorder-parent"
        data: {
            tabId: number
            url: string
        }
    }

    export interface ResultTableRowEvent extends Event {
        detail: {
            row: {
                hash: string
                url: string
            }
        }
    }

    export interface GraphSelectEvent extends Event {
        detail: {
            item: {
                value: "documents" | "update" | "delete"
            }
        }
    }

    export interface TaskProcessingResult {
        url: string
        hash: string
        has_summary: boolean
        last_updated: string
    }

    export interface TaskQueueRecord {
        url: string
        hash: string
        task_name: string
        task_id: string
        status: string
        status_reason: string
        updated_at: string
    }
}