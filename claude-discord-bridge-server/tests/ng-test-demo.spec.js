// NG テストケースのデモ - 意図的に失敗するテスト
import { test, expect } from '@playwright/test';

test.describe('NG Test Demo', () => {
  test('意図的に失敗するテスト - 数値比較', async () => {
    const actual = 2 + 2;
    const expected = 5; // 意図的に間違った期待値
    
    expect(actual).toBe(expected);
  });

  test('意図的に失敗するテスト - 文字列比較', async () => {
    const greeting = "Hello World";
    
    expect(greeting).toBe("Goodbye World"); // 意図的に間違った期待値
  });

  test('意図的に失敗するテスト - 配列長', async () => {
    const array = [1, 2, 3];
    
    expect(array).toHaveLength(5); // 意図的に間違った長さ
  });
});