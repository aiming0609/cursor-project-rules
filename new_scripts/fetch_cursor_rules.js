/**
 * Cursor Directory Rules Fetcher
 * 
 * 这个脚本用于从cursor.directory网站获取规则数据，并将其整理成rules.db.json格式。
 * 脚本会将新获取的规则数据与现有规则数据合并，避免重复。
 * 
 * 使用方法：
 * 1. 确保Node.js已安装
 * 2. 运行命令：node fetch_cursor_rules.js
 * 
 * 脚本会自动读取现有的rules.db.json文件，添加新的规则数据，并保存回文件。
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// 获取当前rules.db.json文件
const rulesDbPath = path.join(__dirname, '..', 'rules_data', 'rules.db.json');
let currentRules = [];

try {
  if (fs.existsSync(rulesDbPath)) {
    const rulesDbContent = fs.readFileSync(rulesDbPath, 'utf8');
    currentRules = JSON.parse(rulesDbContent);
    console.log(`已加载现有规则数据，共${currentRules.length}条规则`);
  } else {
    console.log('未找到现有规则数据文件，将创建新文件');
    // 确保rules_data目录存在
    const rulesDir = path.dirname(rulesDbPath);
    if (!fs.existsSync(rulesDir)) {
      fs.mkdirSync(rulesDir, { recursive: true });
      console.log(`创建目录: ${rulesDir}`);
    }
    // 创建一个空的规则数组作为初始数据
    fs.writeFileSync(rulesDbPath, '[]', 'utf8');
    console.log('已创建空的规则数据文件');
    currentRules = [];
  }
} catch (error) {
  console.error('读取现有规则数据时出错:', error);
  process.exit(1);
}

// cursor.directory API端点和网页URL
const CURSOR_API_URL = 'https://cursor.sh/api/rules/db'; // 尝试直接API
const CURSOR_DIRECTORY_URL = 'https://cursor.directory'; // 网站首页
const CURSOR_RULES_PAGE = 'https://cursor.directory/rules'; // 规则页面

/**
 * 从URL获取数据的通用函数
 * @param {string} url - 要获取数据的URL
 * @returns {Promise<string>} - 响应数据
 */
function fetchData(url) {
  return new Promise((resolve, reject) => {
    console.log(`正在从 ${url} 获取数据...`);
    
    https.get(url, (response) => {
      // 处理重定向
      if (response.statusCode >= 300 && response.statusCode < 400 && response.headers.location) {
        console.log(`重定向到: ${response.headers.location}`);
        return resolve(fetchData(response.headers.location));
      }
      
      // 检查响应状态
      if (response.statusCode !== 200) {
        return reject(new Error(`请求失败，状态码: ${response.statusCode}`));
      }

      let data = '';
      
      // 接收数据
      response.on('data', (chunk) => {
        data += chunk;
      });
      
      // 数据接收完成
      response.on('end', () => {
        resolve(data);
      });
    }).on('error', (error) => {
      reject(error);
    });
  });
}

/**
 * 从cursor.directory API获取规则数据
 * @returns {Promise<Array>} - 规则数据数组
 */
async function fetchRulesFromAPI() {
  try {
    console.log('尝试从API获取规则数据...');
    const data = await fetchData(CURSOR_API_URL);
    const rules = JSON.parse(data);
    
    if (Array.isArray(rules)) {
      console.log(`API成功获取 ${rules.length} 条规则`);
      return rules;
    } else {
      console.warn('API返回的数据不是数组，将尝试其他方法');
      return [];
    }
  } catch (error) {
    console.warn(`从API获取规则失败: ${error.message}`);
    return [];
  }
}

/**
 * 从cursor.directory网页抓取规则数据
 * @returns {Promise<Array>} - 规则数据数组
 */
async function scrapeRulesFromWebsite() {
  try {
    console.log('尝试从网页抓取规则数据...');
    const html = await fetchData(CURSOR_RULES_PAGE);
    
    // 提取JSON数据 - 查找包含规则数据的script标签
    const scriptRegex = /<script\s+id="__NEXT_DATA__"\s+type="application\/json">([^<]+)<\/script>/;
    const match = html.match(scriptRegex);
    
    if (match && match[1]) {
      const jsonData = JSON.parse(match[1]);
      
      // 根据网站结构提取规则数据
      // 这里的路径可能需要根据实际网站结构调整
      const rules = jsonData.props?.pageProps?.rules || 
                    jsonData.props?.pageProps?.initialData?.rules || 
                    [];
      
      if (Array.isArray(rules) && rules.length > 0) {
        console.log(`网页成功抓取 ${rules.length} 条规则`);
        
        // 转换为我们需要的格式
        return rules.map(rule => ({
          title: rule.title || rule.name || '',
          slug: rule.slug || rule.id || '',
          tags: rule.tags || [],
          libs: rule.libraries || rule.libs || [],
          content: rule.content || rule.description || '',
          author: rule.author || {
            name: "Cursor Directory",
            url: "https://cursor.directory",
            avatar: "https://cdn.midday.ai/cursor/favicon.png"
          }
        }));
      }
    }
    
    console.warn('在网页中未找到规则数据');
    return [];
  } catch (error) {
    console.warn(`从网页抓取规则失败: ${error.message}`);
    return [];
  }
}

/**
 * 尝试从github页面抓取规则数据
 * @returns {Promise<Array>} - 规则数据数组
 */
async function scrapeRulesFromGitHub() {
  try {
    console.log('尝试从GitHub获取规则数据...');
    
    // Cursor可能在GitHub上有规则仓库
    const githubRepoUrl = 'https://raw.githubusercontent.com/getcursor/rules/main/rules.json';
    
    try {
      const data = await fetchData(githubRepoUrl);
      const rules = JSON.parse(data);
      
      if (Array.isArray(rules) && rules.length > 0) {
        console.log(`从GitHub成功获取 ${rules.length} 条规则`);
        return rules;
      }
    } catch (error) {
      console.warn(`从GitHub获取规则失败: ${error.message}`);
    }
    
    return [];
  } catch (error) {
    console.warn(`从GitHub抓取规则失败: ${error.message}`);
    return [];
  }
}

/**
 * 将从网站获取的规则数据与现有规则合并
 * @param {Array} existingRules - 现有规则数据
 * @param {Array} newRules - 新获取的规则数据
 * @returns {Array} - 合并后的规则数据
 */
function mergeRules(existingRules, newRules) {
  const mergedRules = [...existingRules];
  
  // 使用slug作为唯一标识符
  const existingSlugs = new Set(existingRules.map(rule => rule.slug));
  
  for (const newRule of newRules) {
    if (newRule.slug && !existingSlugs.has(newRule.slug)) {
      mergedRules.push(newRule);
      existingSlugs.add(newRule.slug);
    }
  }
  
  return mergedRules;
}

/**
 * 主函数
 */
async function main() {
  try {
    // 1. 从API获取规则
    let fetchedRules = await fetchRulesFromAPI();
    
    // 2. 如果API获取失败，尝试从网页抓取
    if (fetchedRules.length === 0) {
      fetchedRules = await scrapeRulesFromWebsite();
    }
    
    // 3. 如果网页抓取也失败，尝试从GitHub获取
    if (fetchedRules.length === 0) {
      fetchedRules = await scrapeRulesFromGitHub();
    }
    
    // 4. 如果所有方法都失败，返回警告
    if (fetchedRules.length === 0) {
      console.warn('无法从任何来源获取规则数据');
      console.log('规则数据库保持不变');
      return;
    }
    
    // 5. 合并规则
    const mergedRules = mergeRules(currentRules, fetchedRules);
    
    // 6. 保存合并后的规则数据
    fs.writeFileSync(rulesDbPath, JSON.stringify(mergedRules, null, 2));
    console.log(`已成功更新规则数据，共 ${mergedRules.length} 条规则，新增 ${mergedRules.length - currentRules.length} 条`);
  } catch (error) {
    console.error('更新规则数据时出错:', error);
    process.exit(1);
  }
}

// 执行主函数
main(); 