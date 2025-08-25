import fs from 'fs/promises';
import path from 'path';

export class CapacityMonitor {
  constructor(targetDir = './test-results') {
    this.targetDir = targetDir;
    this.thresholdGB = 1; // 1GB閾値
  }

  async checkCapacity() {
    try {
      const stats = await this.analyzeDirectory();
      
      return {
        currentSize: stats.totalSize,
        currentSizeFormatted: this.formatBytes(stats.totalSize),
        isOverThreshold: stats.totalSize > this.thresholdGB * 1024 * 1024 * 1024,
        fileCount: stats.fileCount,
        oldestFiles: stats.filesByAge.slice(-10), // 古い順で10ファイル
        largestFiles: stats.filesBySize.slice(0, 10), // 大きい順で10ファイル
        thresholdGB: this.thresholdGB
      };
    } catch (error) {
      throw new Error(`容量チェック中にエラーが発生しました: ${error.message}`);
    }
  }

  async analyzeDirectory() {
    const files = await this.getAllFiles(this.targetDir);
    
    const fileStats = await Promise.all(
      files.map(async (file) => {
        try {
          const stat = await fs.stat(file);
          return {
            path: file,
            relativePath: path.relative(this.targetDir, file),
            size: stat.size,
            createdAt: stat.birthtime,
            modifiedAt: stat.mtime
          };
        } catch (error) {
          // ファイルアクセスエラーは警告として扱い、処理を継続
          console.warn(`ファイル情報取得に失敗: ${file} - ${error.message}`);
          return null;
        }
      })
    );

    // null（エラー）要素を除外
    const validFileStats = fileStats.filter(stat => stat !== null);

    return {
      totalSize: validFileStats.reduce((sum, file) => sum + file.size, 0),
      fileCount: validFileStats.length,
      filesByAge: validFileStats.sort((a, b) => a.createdAt - b.createdAt),
      filesBySize: validFileStats.sort((a, b) => b.size - a.size)
    };
  }

  async getAllFiles(dir) {
    try {
      // ディレクトリが存在しない場合は空配列を返す
      const stat = await fs.stat(dir);
      if (!stat.isDirectory()) {
        return [];
      }
    } catch (error) {
      if (error.code === 'ENOENT') {
        return []; // ディレクトリが存在しない
      }
      throw error;
    }

    const files = [];
    const items = await fs.readdir(dir, { withFileTypes: true });
    
    for (const item of items) {
      const fullPath = path.join(dir, item.name);
      if (item.isDirectory()) {
        // 再帰的にサブディレクトリを探索
        const subFiles = await this.getAllFiles(fullPath);
        files.push(...subFiles);
      } else if (item.isFile()) {
        files.push(fullPath);
      }
    }
    
    return files;
  }

  formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // CLI実行用
  async runCLI() {
    console.log('🔍 テスト結果フォルダ容量チェック中...\n');
    
    try {
      const result = await this.checkCapacity();
      
      console.log(`📁 対象ディレクトリ: ${this.targetDir}`);
      console.log(`📊 現在の使用量: ${result.currentSizeFormatted} (${result.fileCount}ファイル)`);
      console.log(`⚠️  閾値: ${this.thresholdGB}GB\n`);
      
      if (result.isOverThreshold) {
        console.log('🚨 容量が閾値を超えています！\n');
        
        if (result.oldestFiles.length > 0) {
          console.log('💡 削除推奨ファイル（古い順）:');
          result.oldestFiles.forEach((file, i) => {
            console.log(`  ${i+1}. ${file.relativePath} (${this.formatBytes(file.size)}) - ${file.createdAt.toLocaleDateString()}`);
          });
          console.log();
        }

        if (result.largestFiles.length > 0) {
          console.log('📦 大容量ファイル（サイズ順）:');
          result.largestFiles.slice(0, 5).forEach((file, i) => {
            console.log(`  ${i+1}. ${file.relativePath} (${this.formatBytes(file.size)})`);
          });
        }
      } else {
        console.log('✅ 容量は正常範囲内です');
      }
    } catch (error) {
      console.error('❌ エラーが発生しました:', error.message);
      process.exit(1);
    }
  }
}

// CLI実行時の処理
if (import.meta.url === `file://${process.argv[1]}`) {
  const monitor = new CapacityMonitor();
  monitor.runCLI();
}