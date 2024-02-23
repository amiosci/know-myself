export async function openExtensionPopup(this: WebdriverIO.Browser, extensionName: string, popupUrl = 'popup.html') {
    if (!((this.capabilities) as WebdriverIO.Capabilities).browserName?.includes('chrome')) {
        throw new Error('This command only works with Chrome')
    }
    await this.url('chrome://extensions/')

    const extensions = await this.$$('>>> extensions-item');
    const extensionNames = await extensions.map(async (ext) => (
        await ext.$('#name').getText()));
    console.log('Found extensions with name')
    // console.log(extensionNames);
    const extension: WebdriverIO.Element = await extensions.find(async (ext) => (
        await ext.$('#name').getText()) === extensionName
    )

    if (!extension) {
        const installedExtensions = await extensions.map((ext) => ext.$('#name').getText())
        throw new Error(`Couldn't find extension "${extensionName}", available installed extensions are "${installedExtensions.join('", "')}"`)
    }

    const extId = await extension.getAttribute('id')
    await this.url(`chrome-extension://${extId}/popup/${popupUrl}`)
}

declare global {
    namespace WebdriverIO {
        interface Browser {
            openExtensionPopup: typeof openExtensionPopup
        }
    }
}
