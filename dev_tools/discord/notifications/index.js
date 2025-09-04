/**
 * Playwright-Discord マルチチャンネル通知システム
 * メインエントリーポイント
 */

export { ChannelConfigManager } from './channel-config-manager.js';
export { EnvParser } from './env-parser.js';
export { MultiChannelNotifier } from './multi-channel-notifier.js';
export { SessionDetector } from './session-detector.js';
export { default as PlaywrightChannelReporter } from './playwright-channel-reporter.js';

/**
 * システム全体の初期化と設定検証
 * @param {Object} options 初期化オプション
 * @returns {Promise<Object>} 初期化済みコンポーネント群
 */
export async function initializeMultiChannelSystem(options = {}) {
  console.log('🚀 Initializing Playwright-Discord Multichannel System...');

  try {
    // 設定解析
    const { EnvParser } = await import('./env-parser.js');
    const config = EnvParser.parseAllConfigurations();
    
    if (!config.isValid) {
      console.warn('⚠️ Configuration warnings detected:', config.warnings);
      if (config.errors.length > 0) {
        throw new Error(`Configuration errors: ${config.errors.join(', ')}`);
      }
    }

    // コンポーネント初期化
    const { ChannelConfigManager } = await import('./channel-config-manager.js');
    const { SessionDetector } = await import('./session-detector.js');
    const { MultiChannelNotifier } = await import('./multi-channel-notifier.js');
    const { default: PlaywrightChannelReporter } = await import('./playwright-channel-reporter.js');

    const channelManager = new ChannelConfigManager();
    const sessionDetector = new SessionDetector(options.sessionDetector);
    const multiChannelNotifier = new MultiChannelNotifier(options.notifier);
    const reporter = new PlaywrightChannelReporter(options.reporter);

    console.log('✅ Multichannel system initialized successfully');
    console.log(`📊 Detected ${Object.keys(config.channels).length} channels:`, Object.keys(config.channels));

    return {
      channelManager,
      sessionDetector,
      multiChannelNotifier,
      reporter,
      config
    };

  } catch (error) {
    console.error('❌ Failed to initialize multichannel system:', error);
    throw error;
  }
}

/**
 * システムヘルスチェック
 * @returns {Promise<Object>} ヘルス状況
 */
export async function performHealthCheck() {
  console.log('🏥 Performing system health check...');
  
  const health = {
    timestamp: new Date().toISOString(),
    status: 'healthy',
    checks: {},
    warnings: [],
    errors: []
  };

  try {
    // 設定チェック
    const { EnvParser } = await import('./env-parser.js');
    const config = EnvParser.parseAllConfigurations();
    
    health.checks.configuration = {
      status: config.isValid ? 'pass' : 'warn',
      channelCount: Object.keys(config.channels).length,
      errors: config.errors,
      warnings: config.warnings
    };

    if (!config.isValid) {
      health.status = 'degraded';
      health.warnings.push('Configuration issues detected');
    }

    // チャンネル接続チェック
    const { ChannelConfigManager } = await import('./channel-config-manager.js');
    const channelManager = new ChannelConfigManager();
    
    const channelStats = channelManager.getConfigStats();
    health.checks.channels = {
      status: channelStats.totalChannels > 0 ? 'pass' : 'fail',
      totalChannels: channelStats.totalChannels,
      cacheStatus: channelStats.isCached ? 'cached' : 'fresh'
    };

    if (channelStats.totalChannels === 0) {
      health.status = 'unhealthy';
      health.errors.push('No channels configured');
    }

    // セッション検出チェック
    const { SessionDetector } = await import('./session-detector.js');
    const sessionDetector = new SessionDetector();
    
    try {
      const currentSession = await sessionDetector.detectCurrentSession();
      health.checks.sessionDetection = {
        status: 'pass',
        currentSession,
        detectionMethods: sessionDetector.config.detectionMethods
      };
    } catch (error) {
      health.checks.sessionDetection = {
        status: 'fail',
        error: error.message
      };
      health.status = 'unhealthy';
      health.errors.push('Session detection failed');
    }

    console.log(`🏥 Health check completed: ${health.status}`);
    return health;

  } catch (error) {
    health.status = 'unhealthy';
    health.errors.push(`Health check failed: ${error.message}`);
    console.error('❌ Health check failed:', error);
    return health;
  }
}