const sharp = require('sharp');
const path = require('path');

const inputPath = path.join(__dirname, '../attached_assets/nora_logo_1768041475636.jpg');
const outputPath = path.join(__dirname, '../attached_assets/nora_logo_transparent.png');

async function removeBackground() {
  try {
    const { data, info } = await sharp(inputPath)
      .raw()
      .toBuffer({ resolveWithObject: true });

    const { width, height, channels } = info;
    
    const rgba = Buffer.alloc(width * height * 4);
    
    for (let i = 0; i < width * height; i++) {
      const r = data[i * channels];
      const g = data[i * channels + 1];
      const b = data[i * channels + 2];
      
      const isTeal = (
        r < 80 && 
        g > 40 && g < 120 && 
        b > 40 && b < 120 &&
        Math.abs(g - b) < 30
      );
      
      const isDarkTeal = (
        r < 50 && 
        g > 30 && g < 90 && 
        b > 30 && b < 90
      );
      
      const isVeryDark = (r < 30 && g < 50 && b < 50);
      
      const isBackground = isTeal || isDarkTeal || isVeryDark;
      
      if (isBackground) {
        rgba[i * 4] = 0;
        rgba[i * 4 + 1] = 0;
        rgba[i * 4 + 2] = 0;
        rgba[i * 4 + 3] = 0;
      } else {
        rgba[i * 4] = 25;
        rgba[i * 4 + 1] = 25;
        rgba[i * 4 + 2] = 25;
        rgba[i * 4 + 3] = 255;
      }
    }
    
    await sharp(rgba, { raw: { width, height, channels: 4 } })
      .png()
      .toFile(outputPath);
    
    console.log('Background removed successfully!');
    console.log('Output saved to:', outputPath);
  } catch (error) {
    console.error('Error:', error);
  }
}

removeBackground();
