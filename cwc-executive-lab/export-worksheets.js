const puppeteer = require('puppeteer');
const path = require('path');

const worksheets = [
    'plateau-diagnostic.html',
    'stuck-loop.html',
    'career-growth-roadmap.html',
    'relationship-map.html',
    'momentum-planner.html'
];

async function exportWorksheets() {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    for (const worksheet of worksheets) {
        const filePath = path.join(__dirname, worksheet);
        const pdfName = worksheet.replace('.html', '.pdf');
        const outputPath = path.join(__dirname, 'skool-assets', 'worksheets', pdfName);

        console.log(`Converting ${worksheet}...`);

        await page.goto(`file://${filePath}`, { waitUntil: 'networkidle0' });

        await page.pdf({
            path: outputPath,
            format: 'Letter',
            printBackground: true,
            margin: { top: '0.5in', right: '0.5in', bottom: '0.5in', left: '0.5in' }
        });

        console.log(`Exported: ${outputPath}`);
    }

    await browser.close();
    console.log('Done!');
}

exportWorksheets().catch(console.error);
