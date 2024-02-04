
declare namespace chrome.readingList {
    export interface ReadingListItem {
        url: string;
        title: string;
    }

    export interface QueryRequest {

    }

    export function query(filter: QueryRequest): Promise<ReadingListItem[]>;

    export interface EntryAddedEvent extends chrome.events.Event<(entry: ReadingListItem) => void> { }

    export var onEntryAdded: EntryAddedEvent;
}


