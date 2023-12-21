console.log('This is a popup!');


chrome.readingList.onEntryAdded.addListener((entry) => {
    console.log(entry);
});
