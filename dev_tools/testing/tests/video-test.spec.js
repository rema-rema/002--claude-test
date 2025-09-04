import { test, expect } from '@playwright/test';

test('colorful video recording test', async ({ page }) => {
  console.log('Starting colorful video test...');
  
  // Navigate to a very colorful and animated page
  const htmlContent = `
    <html>
      <head>
        <title>Colorful Video Test</title>
        <style>
          body {
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4, #FECA57, #FF9FF3);
            background-size: 400% 400%;
            animation: gradient 4s ease infinite;
            min-height: 100vh;
          }
          
          @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
          }
          
          h1 {
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            font-size: 3em;
            text-align: center;
            margin-bottom: 30px;
            animation: bounce 2s infinite;
          }
          
          @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-30px); }
            60% { transform: translateY(-15px); }
          }
          
          button {
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            color: white;
            border: none;
            padding: 20px 40px;
            margin: 15px;
            border-radius: 50px;
            font-size: 20px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
          }
          
          button:hover {
            transform: scale(1.1) rotate(5deg);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
          }
          
          #status {
            background: rgba(255,255,255,0.9);
            padding: 30px;
            border-radius: 20px;
            margin: 30px auto;
            text-align: center;
            font-size: 24px;
            max-width: 600px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
          }
          
          #counter {
            font-size: 36px;
            font-weight: bold;
            color: #333;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
          }
          
          .pulse {
            animation: pulse 1s infinite;
          }
          
          @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
          }
        </style>
      </head>
      <body>
        <h1>🎬 カラフル動画テスト 🎬</h1>
        
        <div style="text-align: center;">
          <button id="btn1" onclick="updateStatus(1)">🔴 RED BUTTON</button>
          <button id="btn2" onclick="updateStatus(2)">🟢 GREEN BUTTON</button>
          <button id="btn3" onclick="updateStatus(3)">🔵 BLUE BUTTON</button>
        </div>
        
        <div id="status">
          <div>ボタンクリックを待機中...</div>
          <div id="counter">クリック数: 0</div>
        </div>
        
        <script>
          let clickCount = 0;
          
          function updateStatus(btnNum) {
            clickCount++;
            
            const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1'];
            const emojis = ['🔴', '🟢', '🔵'];
            
            document.getElementById("status").innerHTML = \`
              <div class="pulse">ボタン \${btnNum} (\${emojis[btnNum-1]}) がクリックされました！</div>
              <div>時刻: \${new Date().toLocaleTimeString()}</div>
              <div id="counter">クリック数: \${clickCount}</div>
            \`;
            
            // Change background filter for visual effect
            document.body.style.filter = \`hue-rotate(\${clickCount * 45}deg) brightness(\${1 + clickCount * 0.1})\`;
            
            // Add temporary border color change
            document.getElementById("status").style.border = \`5px solid \${colors[btnNum-1]}\`;
            
            setTimeout(() => {
              document.getElementById("status").style.border = 'none';
            }, 1000);
          }
        </script>
      </body>
    </html>
  `;
  
  await page.goto(\`data:text/html,\${encodeURIComponent(htmlContent)}\`);
  
  // Wait for page to fully load and animations to start
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);
  
  // Verify page loaded correctly
  await expect(page.locator('h1')).toContainText('カラフル動画テスト');
  
  console.log('Page loaded, starting colorful interactions...');
  
  // Perform multiple colorful interactions
  await page.locator('#btn1').click();
  await page.waitForTimeout(1500);
  
  await page.locator('#btn2').click();
  await page.waitForTimeout(1500);
  
  await page.locator('#btn3').click();
  await page.waitForTimeout(1500);
  
  await page.locator('#btn1').click();
  await page.waitForTimeout(1500);
  
  await page.locator('#btn3').click();
  await page.waitForTimeout(1500);
  
  await page.locator('#btn2').click();
  await page.waitForTimeout(2000);
  
  // Final verification
  await expect(page.locator('#counter')).toContainText('クリック数: 6');
  
  console.log('Colorful video test completed successfully!');
});

test('external website test', async ({ page }) => {
  console.log('Starting external website test...');
  
  // Navigate to a real website with content
  await page.goto('https://playwright.dev/');
  
  // Wait for content to load
  await page.waitForLoadState('networkidle');
  
  // Take a screenshot to verify content
  await page.screenshot({ path: 'test-results/playwright-homepage.png' });
  
  // Interact with the page
  if (await page.locator('text=Docs').isVisible()) {
    await page.locator('text=Docs').click();
    await page.waitForTimeout(2000);
  }
  
  // Wait for video recording
  await page.waitForTimeout(3000);
  
  console.log('External website test completed');
});