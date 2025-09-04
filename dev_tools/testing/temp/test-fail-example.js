// 意図的に失敗するテストケース
import assert from 'assert';

function testFailExample() {
    console.log('テスト開始: 意図的失敗ケース');
    
    // 意図的に失敗するテスト
    assert.strictEqual(2 + 2, 5, 'このテストは意図的に失敗します');
    
    console.log('このログは表示されません');
}

try {
    testFailExample();
    console.log('✅ テスト成功');
} catch (error) {
    console.error('❌ テスト失敗:', error.message);
    process.exit(1);
}