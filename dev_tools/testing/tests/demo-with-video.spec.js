import { test, expect } from '@playwright/test';

test('interactive demo test with video recording', async ({ page }) => {
  // Navigate to a demo page with interactive elements
  await page.goto('data:text/html,<html><head><title>Demo Test Page</title><style>body{font-family:Arial;padding:20px;background:linear-gradient(45deg,#f0f8ff,#e6f3ff)}button{padding:10px 20px;margin:10px;background:#007acc;color:white;border:none;border-radius:5px;cursor:pointer}button:hover{background:#005999}#status{margin:20px;padding:10px;border:2px solid #ccc;border-radius:5px;min-height:50px}</style></head><body><h1>Interactive Demo Page</h1><p>This page demonstrates Playwright test automation with video recording</p><button id="clickMe" onclick="updateStatus()">Click Me!</button><button id="changeColor" onclick="changeBackground()">Change Background</button><div id="status">Status: Ready for interaction</div><script>function updateStatus(){document.getElementById("status").innerHTML="Status: Button was clicked at "+new Date().toLocaleTimeString()+"<br>✅ Test interaction successful!"}function changeBackground(){document.body.style.background="linear-gradient(45deg,#ffe6f0,#fff0e6)";document.getElementById("status").innerHTML+="<br>🎨 Background color changed!"}</script></body></html>');
  
  // Wait for page to load and take initial screenshot
  await page.waitForLoadState('networkidle');
  await expect(page.locator('h1')).toHaveText('Interactive Demo Page');
  
  // Take a screenshot before interaction
  await page.screenshot({ path: 'test-results/demo-initial.png' });
  
  // Interact with the first button
  await page.locator('#clickMe').click();
  
  // Wait for status update and verify
  await expect(page.locator('#status')).toContainText('Button was clicked');
  await page.waitForTimeout(1000);
  
  // Interact with the second button
  await page.locator('#changeColor').click();
  
  // Wait for background change and verify
  await expect(page.locator('#status')).toContainText('Background color changed');
  await page.waitForTimeout(1000);
  
  // Take final screenshot
  await page.screenshot({ path: 'test-results/demo-final.png' });
  
  // Add some delay to make video recording more meaningful
  await page.waitForTimeout(2000);
  
  console.log('Demo test completed with video recording');
});

test('form interaction demo', async ({ page }) => {
  // Navigate to a form demo page
  await page.goto('data:text/html,<html><head><title>Form Demo</title><style>body{font-family:Arial;padding:20px;background:#f5f5f5}form{background:white;padding:20px;border-radius:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1);max-width:400px}input,textarea{width:100%;padding:8px;margin:8px 0;border:1px solid #ddd;border-radius:4px}button{background:#28a745;color:white;padding:10px 20px;border:none;border-radius:4px;cursor:pointer}button:hover{background:#218838}#result{margin-top:20px;padding:10px;background:#e8f5e9;border-radius:4px;display:none}</style></head><body><h1>Contact Form Demo</h1><form id="demoForm"><label>Name:<input type="text" id="name" required></label><label>Email:<input type="email" id="email" required></label><label>Message:<textarea id="message" rows="4" required></textarea></label><button type="submit">Submit Form</button></form><div id="result"></div><script>document.getElementById("demoForm").addEventListener("submit",function(e){e.preventDefault();const name=document.getElementById("name").value;const email=document.getElementById("email").value;const message=document.getElementById("message").value;document.getElementById("result").style.display="block";document.getElementById("result").innerHTML="<h3>✅ Form Submitted Successfully!</h3><p><strong>Name:</strong> "+name+"</p><p><strong>Email:</strong> "+email+"</p><p><strong>Message:</strong> "+message+"</p><p>Timestamp: "+new Date().toLocaleString()+"</p>"})</script></body></html>');
  
  // Fill out the form
  await page.fill('#name', 'Playwright Test User');
  await page.fill('#email', 'test@example.com');
  await page.fill('#message', 'This is a test message from Playwright automation with video recording.');
  
  // Submit the form
  await page.locator('button[type="submit"]').click();
  
  // Verify the result
  await expect(page.locator('#result')).toContainText('Form Submitted Successfully');
  await expect(page.locator('#result')).toContainText('Playwright Test User');
  
  // Wait for the interaction to be clearly visible in video
  await page.waitForTimeout(2000);
  
  console.log('Form demo test completed with video recording');
});