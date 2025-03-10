/**
 * @file svg_to_png.js
 * @description 将SVG图标转换为PNG格式
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 检查是否安装了必要的依赖
try {
  require.resolve('svg2png');
} catch (e) {
  console.log('正在安装svg2png依赖...');
  execSync('npm install svg2png --save-dev');
  console.log('svg2png安装完成');
}

const svg2png = require('svg2png');

// 配置
const inputFile = path.join(__dirname, '../resources/icon.svg');
const outputFile = path.join(__dirname, '../resources/icon.png');
const size = 128; // 输出PNG的尺寸

async function convertSvgToPng() {
  try {
    console.log(`正在读取SVG文件: ${inputFile}`);
    const sourceBuffer = fs.readFileSync(inputFile);
    
    console.log(`正在转换SVG到PNG (${size}x${size}像素)...`);
    const pngBuffer = await svg2png(sourceBuffer, { width: size, height: size });
    
    console.log(`正在保存PNG文件: ${outputFile}`);
    fs.writeFileSync(outputFile, pngBuffer);
    
    console.log('转换完成!');
    console.log(`PNG图标已保存到: ${outputFile}`);
  } catch (error) {
    console.error('转换过程中发生错误:', error);
  }
}

convertSvgToPng(); 