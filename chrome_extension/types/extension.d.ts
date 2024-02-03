declare namespace kms {
    export interface RecorderRequest {
        type: string;
        target: string;

        // The target frame identifier
        data: number;
    }

    export interface RecorderResponse {
        type: string;
        target: string;
        data: {
            tabId: number;
            url: string;
        }
    }

    export interface ResultTableRowEvent extends Event {
        detail: {
            row: {
                hash: string;
                url: string;
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
}