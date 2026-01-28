const puppeteer = require('puppeteer');
const path = require('path');

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

async function exportSlides() {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    // Set viewport to 1920x1080 for nice export
    await page.setViewport({ width: 1920, height: 1080 });

    // Load the deck
    const filePath = path.join(__dirname, 'index.html');
    await page.goto(`file://${filePath}`, { waitUntil: 'networkidle0' });

    // Wait for fonts to load
    await delay(2000);

    // Get total number of slides
    const totalSlides = await page.evaluate(() => {
        return document.querySelectorAll('.slide').length;
    });

    console.log(`Exporting ${totalSlides} slides...`);

    // Export each slide
    for (let i = 1; i <= totalSlides; i++) {
        // Navigate to slide
        await page.evaluate((slideNum) => {
            document.querySelectorAll('.slide').forEach(s => s.classList.remove('active'));
            document.querySelector(`[data-slide="${slideNum}"]`).classList.add('active');
        }, i);

        await delay(500);

        // Screenshot
        const filename = `skool-assets/slides/slide-${String(i).padStart(2, '0')}.png`;
        await page.screenshot({ path: filename, fullPage: false });
        console.log(`Exported: ${filename}`);
    }

    await browser.close();
    console.log('Done!');
}

exportSlides().catch(console.error);
