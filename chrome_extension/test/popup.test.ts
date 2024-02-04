import { browser } from '@wdio/globals'

// describe('Extension Popup', () => {
//     it('should open', async () => {
//         await browser.openExtensionPopup('Know Myself')
//     });
// });

describe('my awesome website', () => {
    it('should do some assertions', async () => {
        await browser.url('https://news.ycombinator.com/')
        console.log(await browser.getTitle());
        // await expect(browser).toHaveTitle('WebdriverIO · Next-gen browser and mobile automation test framework for Node.js | WebdriverIO')
    })
})
