import { test, expect } from '@playwright/test';

test('visible content video recording test', async ({ page }) => {
  console.log('Starting video recording test...');
  
  // Navigate to a colorful page with visible content
  await page.goto('data:text/html,<html><head><title>Video Test</title><style>body{margin:0;padding:20px;font-family:Arial,sans-serif;background:linear-gradient(45deg,#FF6B6B,#4ECDC4,#45B7D1,#96CEB4);background-size:400% 400%;animation:gradient 4s ease infinite}@keyframes gradient{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}h1{color:white;text-shadow:2px 2px 4px rgba(0,0,0,0.5);font-size:2.5em;text-align:center;margin-bottom:30px}button{background:#FF6B6B;color:white;border:none;padding:15px 30px;margin:10px;border-radius:8px;font-size:18px;cursor:pointer;transition:all 0.3s ease}button:hover{background:#FF5252;transform:scale(1.05)}#status{background:rgba(255,255,255,0.9);padding:20px;border-radius:10px;margin:20px;text-align:center;font-size:18px;box-shadow:0 4px 6px rgba(0,0,0,0.1)}#counter{font-size:24px;font-weight:bold;color:#333}</style></head><body><h1>🎬 Playwright Video Recording Test</h1><button id="btn1" onclick="updateStatus(1)">ボタン 1</button><button id="btn2" onclick="updateStatus(2)">ボタン 2</button><button id="btn3" onclick="updateStatus(3)">ボタン 3</button><div id="status">クリックを待機中...</div><div id="counter">クリック数: 0</div><script>let clickCount = 0; function updateStatus(btnNum) { clickCount++; document.getElementById("status").innerHTML = `ボタン ${btnNum} がクリックされました！<br>時刻: ${new Date().toLocaleTimeString()}`; document.getElementById("counter").innerHTML = `クリック数: ${clickCount}`; document.body.style.filter = `hue-rotate(${clickCount * 30}deg)`; }</script></body></html>');
  
  // Wait for page to fully load
  await page.waitForLoadState('networkidle');
  await expect(page.locator('h1')).toContainText('Video Recording Test');
  
  console.log('Page loaded, starting interactions...');
  
  // Perform multiple interactions with delays for video recording
  await page.locator('#btn1').click();
  await page.waitForTimeout(1000);
  
  await page.locator('#btn2').click();
  await page.waitForTimeout(1000);
  
  await page.locator('#btn3').click();
  await page.waitForTimeout(1000);
  
  await page.locator('#btn1').click();
  await page.waitForTimeout(1000);
  
  await page.locator('#btn2').click();
  await page.waitForTimeout(1500);
  
  // Verify final state
  await expect(page.locator('#counter')).toContainText('クリック数: 5');
  
  console.log('Video recording test completed successfully');
});

test('simple navigation video test', async ({ page }) => {
  console.log('Starting simple navigation test...');
  
  // Navigate to a real website to ensure content is visible
  await page.goto('https://example.com');
  
  // Wait for content
  await page.waitForLoadState('networkidle');
  
  // Take screenshot to verify content is loading
  await page.screenshot({ path: 'test-results/navigation-test.png' });
  
  // Verify the page loaded
  await expect(page.locator('h1')).toBeVisible();
  
  // Add some delay for video recording
  await page.waitForTimeout(3000);
  
  console.log('Navigation test completed');
});