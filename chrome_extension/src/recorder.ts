chrome.runtime.onMessage.addListener(async (message: kms.RecorderRequest) => {
    if (message.target === 'offscreen') {
        switch (message.type) {
            case 'start-recording':
                startRecording(message.data);
                break;
            case 'stop-recording':
                stopRecording();
                break;
            default:
                throw new Error(`Unrecognized message: ${message.type}`);
        }
    }
});

let recorder: MediaRecorder | null = null;
let data: Blob[] = [];

const startRecording = async (streamId: number) => {
    if (recorder?.state === 'recording') {
        throw new Error('Called startRecording while recording is in progress.');
    }

    const media = await navigator.mediaDevices.getUserMedia({
        // audio: {
        //     mandatory: {
        //         chromeMediaSource: 'tab',
        //         chromeMediaSourceId: streamId
        //     }
        // },
        video: {
            // @ts-ignore: Valid according to Chrome spec
            // https://developer.chrome.com/docs/extensions/reference/api/tabCapture#stream-ids
            mandatory: {
                chromeMediaSource: 'tab',
                chromeMediaSourceId: streamId
            }
        }
    });

    // Continue to play the captured audio to the user.
    const output = new AudioContext();
    const source = output.createMediaStreamSource(media);
    source.connect(output.destination);

    // Start recording.
    recorder = new MediaRecorder(media, { mimeType: 'video/webm' });
    recorder.ondataavailable = (event) => {
        data.push(event.data);
        debugger;
    };
    recorder.onstop = () => {
        const blob = new Blob(data, { type: 'video/webm' });
        const blobUrl = URL.createObjectURL(blob);
        window.open(blobUrl, '_blank');

        const recorderResponse: kms.RecorderResponse = {
            type: 'recording-completed',
            target: 'recorder-parent',
            data: {
                tabId: streamId,
                url: blobUrl,
            }
        };

        chrome.runtime.sendMessage(recorderResponse);


        // Clear state ready for next recording
        recorder = null;
        data = [];
    };
    recorder.start();

    // Record the current state in the URL. This provides a very low-bandwidth
    // way of communicating with the service worker (the service worker can check
    // the URL of the document and see the current recording state). We can't
    // store that directly in the service worker as it may be terminated while
    // recording is in progress. We could write it to storage but that slightly
    // increases the risk of things getting out of sync.
    window.location.hash = 'recording';
}

const stopRecording = async () => {
    if (recorder === null) {
        throw new Error('Recorder not started');
    }

    recorder.stop();

    // Stopping the tracks makes sure the recording icon in the tab is removed.
    recorder.stream.getTracks().forEach((t) => t.stop());

    // Update current state in URL
    window.location.hash = '';

    // Note: In a real extension, you would want to write the recording to a more
    // permanent location (e.g IndexedDB) and then close the offscreen document,
    // to avoid keeping a document around unnecessarily. Here we avoid that to
    // make sure the browser keeps the Object URL we create (see above) and to
    // keep the sample fairly simple to follow.
}