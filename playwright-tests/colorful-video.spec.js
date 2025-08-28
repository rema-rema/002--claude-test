import { test, expect } from '@playwright/test';

test('colorful interactive video test', async ({ page }) => {
  console.log('🎬 Starting colorful video test...');
  
  // Create a very colorful and visually interesting page
  const colorfulHtml = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>Colorful Test Page</title>
        <style>
          body {
            margin: 0;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #feca57, #ff9ff3);
            background-size: 400% 400%;
            animation: rainbow 3s ease infinite;
            font-family: Arial, sans-serif;
            color: white;
            text-align: center;
            padding: 50px;
          }
          
          @keyframes rainbow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
          }
          
          h1 {
            font-size: 4em;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.5);
            animation: bounce 2s infinite;
          }
          
          @keyframes bounce {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
          }
          
          .button {
            display: inline-block;
            padding: 20px 40px;
            margin: 20px;
            background: rgba(255,255,255,0.2);
            border: 3px solid white;
            border-radius: 50px;
            color: white;
            font-size: 24px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
          }
          
          .button:hover {
            transform: scale(1.1) rotate(5deg);
            background: rgba(255,255,255,0.4);
            box-shadow: 0 0 30px rgba(255,255,255,0.5);
          }
          
          #display {
            margin: 40px auto;
            padding: 30px;
            background: rgba(255,255,255,0.9);
            color: #333;
            border-radius: 20px;
            max-width: 600px;
            font-size: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
          }
          
          .clicked {
            animation: flash 0.5s ease;
          }
          
          @keyframes flash {
            0% { background-color: #ffff00; transform: scale(1); }
            50% { background-color: #ff00ff; transform: scale(1.2); }
            100% { background-color: inherit; transform: scale(1); }
          }
        </style>
      </head>
      <body>
        <h1>🌈 COLORFUL VIDEO TEST 🌈</h1>
        
        <div class="button" id="btn1" onclick="handleClick(1, '#ff6b6b')">🔴 RED</div>
        <div class="button" id="btn2" onclick="handleClick(2, '#4ecdc4')">🟢 GREEN</div>
        <div class="button" id="btn3" onclick="handleClick(3, '#45b7d1')">🔵 BLUE</div>
        
        <div id="display">
          <div>Click colorful buttons above!</div>
          <div id="counter">Clicks: 0</div>
        </div>
        
        <script>
          let clickCount = 0;
          
          function handleClick(buttonNum, color) {
            clickCount++;
            
            // Visual feedback
            const btn = document.getElementById('btn' + buttonNum);
            btn.classList.add('clicked');
            setTimeout(() => btn.classList.remove('clicked'), 500);
            
            // Update display
            document.getElementById('display').innerHTML = \`
              <div style="color: \` + color + \`; font-weight: bold; font-size: 28px;">
                Button \` + buttonNum + \` clicked! ⭐
              </div>
              <div>Time: \` + new Date().toLocaleTimeString() + \`</div>
              <div id="counter" style="font-size: 32px; margin-top: 20px;">
                Total Clicks: \` + clickCount + \` 🎯
              </div>
            \`;
            
            // Change page hue
            document.body.style.filter = \`hue-rotate(\` + (clickCount * 30) + \`deg) brightness(\` + (1 + clickCount * 0.1) + \`)\`;
            
            console.log(\`Button \` + buttonNum + \` clicked! Total: \` + clickCount);
          }
        </script>
      </body>
    </html>
  `;
  
  // Navigate to the colorful page
  await page.goto(`data:text/html,${encodeURIComponent(colorfulHtml)}`);
  
  // Wait for page to load
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // Verify the page loaded
  await expect(page.locator('h1')).toContainText('COLORFUL VIDEO TEST');
  
  console.log('🌈 Page loaded! Starting interactions...');
  
  // Perform colorful interactions with pauses for video recording
  await page.click('#btn1');
  console.log('🔴 Clicked RED button');
  await page.waitForTimeout(1500);
  
  await page.click('#btn2'); 
  console.log('🟢 Clicked GREEN button');
  await page.waitForTimeout(1500);
  
  await page.click('#btn3');
  console.log('🔵 Clicked BLUE button');
  await page.waitForTimeout(1500);
  
  await page.click('#btn1');
  console.log('🔴 Clicked RED again');
  await page.waitForTimeout(1500);
  
  await page.click('#btn3');
  console.log('🔵 Clicked BLUE again');
  await page.waitForTimeout(1500);
  
  // Final verification
  await expect(page.locator('#counter')).toContainText('Total Clicks: 5');
  
  // Extra time for video recording
  await page.waitForTimeout(2000);
  
  console.log('✅ Colorful video test completed successfully!');
});