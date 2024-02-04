declare namespace kms {
    export interface RecorderRequest {
        type: string
        target: string

        // The target frame identifier
        data: number
    }

    export interface RecorderResponse {
        type: string
        target: string
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
                value: string
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