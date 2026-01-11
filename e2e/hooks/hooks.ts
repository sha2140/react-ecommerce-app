import { Before, After } from '@cucumber/cucumber';
import { chromium } from 'playwright';
import * as path from 'path';
import * as fs from 'fs';
import { LoginPage } from '../pages/LoginPage.js';
import { ProductListPage } from '../pages/ProductListPage.js';
import { CartPage } from '../pages/CartPage.js';
import { CustomWorld } from '../support/world.js';

Before(async function (this: CustomWorld) {
  // Video recording disabled - enable after installing ffmpeg with: npx playwright install --with-deps
  // const reportsDir = path.join(process.cwd(), 'e2e', 'reports', 'videos');
  // if (!fs.existsSync(reportsDir)) {
  //   fs.mkdirSync(reportsDir, { recursive: true });
  // }
  
  this.browser = await chromium.launch({ 
    headless: process.env.CI ? true : false 
  });
  this.context = await this.browser.newContext();
  // To enable video recording, uncomment:
  // this.context = await this.browser.newContext({
  //   recordVideo: {
  //     dir: path.join(process.cwd(), 'e2e', 'reports', 'videos'),
  //     size: { width: 1280, height: 720 },
  //   },
  // });
  
  this.page = await this.context.newPage();
  this.loginPage = new LoginPage(this.page);
  this.productListPage = new ProductListPage(this.page);
  this.cartPage = new CartPage(this.page);
});

After(async function (this: CustomWorld, scenario: any) {
  // Capture screenshot on failure (only if page exists)
  if (this.page && (scenario.result?.status === 'FAILED' || scenario.result?.status === 'UNDEFINED')) {
    try {
      const screenshotsDir = path.join(process.cwd(), 'e2e', 'reports', 'screenshots');
      if (!fs.existsSync(screenshotsDir)) {
        fs.mkdirSync(screenshotsDir, { recursive: true });
      }
      
      const screenshotPath = path.join(
        screenshotsDir,
        `${scenario.pickle.name?.replace(/\s+/g, '-') || 'screenshot'}-${Date.now()}.png`
      );
      await this.page.screenshot({ path: screenshotPath, fullPage: true });
      
      // Attach screenshot to report
      const screenshotBuffer = fs.readFileSync(screenshotPath);
      await this.attach(screenshotBuffer, 'image/png');
    } catch (error) {
      // Screenshot capture failed, continue
    }
  }
  
  // Get video path and save it (only if page exists)
  if (this.page) {
    try {
      const video = await this.page.video();
      if (video) {
        const videoPath = await video.path();
        if (videoPath && fs.existsSync(videoPath)) {
          // Save video with scenario name
          const videoName = `${scenario.pickle.name?.replace(/\s+/g, '-') || 'video'}-${Date.now()}.webm`;
          const newVideoPath = path.join(path.dirname(videoPath), videoName);
          try {
            fs.renameSync(videoPath, newVideoPath);
          } catch (error) {
            // Video might already be saved
          }
        }
      }
    } catch (error) {
      // Video handling failed, continue
    }
  }
  
  // Close browser
  if (this.page) {
    try {
      await this.page.close();
    } catch (error) {
      // Page already closed
    }
  }
  if (this.context) {
    try {
      await this.context.close();
    } catch (error) {
      // Context already closed
    }
  }
  if (this.browser) {
    try {
      await this.browser.close();
    } catch (error) {
      // Browser already closed
    }
  }
});