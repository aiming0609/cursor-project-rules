const https = require('https');
const fs = require('fs');

console.log('开始获取cursor.directory规则数据...');

// 尝试获取所有规则列表
https.get('https://cursor.directory/api/rules/all', (res) => {
  let data = '';

  // 接收数据片段
  res.on('data', (chunk) => {
    data += chunk;
  });

  // 数据接收完成
  res.on('end', () => {
    try {
      // 将数据写入文件
      fs.writeFileSync('rules_data.json', data);
      console.log('数据已成功保存到rules_data.json文件');
    } catch (error) {
      console.error('保存数据时出错:', error);
    }
  });
}).on('error', (error) => {
  console.error('获取数据时出错:', error);
}); 