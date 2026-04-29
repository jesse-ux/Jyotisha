/**
 * Subscription Module — 订阅管理
 * Apple IAP 订阅 + 订阅状态 + 升级提示
 */
import { getToken, getUser, getApiBase, fetchUser, isLoggedIn, apiPost } from './auth.js';
import { t } from './i18n.js';

// ============================================================================
// 配置
// ============================================================================
const PRODUCT_ID = 'com.jyotish.app.premium.monthly';  // Apple IAP 产品 ID
const API_BASE_FUNC = getApiBase;

// ============================================================================
// 状态
// ============================================================================
let _isCapacitor = false;
let _purchasesPlugin = null;

// ============================================================================
// 初始化
// ============================================================================
export function initSubscription() {
  // 检测 Capacitor 环境
  _isCapacitor = !!(window.Capacitor?.isNativePlatform?.());
  
  if (_isCapacitor) {
    setupCapacitorIAP();
  }

  // 监听订阅事件（由 auth profile 升级按钮触发）
  document.addEventListener('jyotish:subscribe', handleSubscribe);
}

// ============================================================================
// Capacitor IAP 设置
// ============================================================================
async function setupCapacitorIAP() {
  try {
    // 尝试使用 RevenueCat
    const Purchases = window.Capacitor?.Plugins?.Purchases;
    if (Purchases) {
      _purchasesPlugin = Purchases;
      // RevenueCat 初始化需要 API Key（从后端获取或硬编码）
      const apiKey = localStorage.getItem('jyotish_revenuecat_key');
      if (apiKey) {
        await Purchases.configure({ apiKey, appUserID: getUser()?.id });
        console.log('[Subscription] RevenueCat configured');
      }
    }
  } catch (err) {
    console.warn('[Subscription] IAP setup failed:', err);
  }
}

// ============================================================================
// 订阅流程
// ============================================================================
async function handleSubscribe() {
  if (!isLoggedIn()) {
    // 未登录，先提示登录
    const event = new CustomEvent('jyotish:auth-required');
    document.dispatchEvent(event);
    return;
  }

  if (_isCapacitor && _purchasesPlugin) {
    await purchaseNative();
  } else {
    // Web 环境 — 显示订阅说明
    showSubscriptionInfo();
  }
}

// ============================================================================
// Apple IAP 购买
// ============================================================================
async function purchaseNative() {
  try {
    if (!_purchasesPlugin) {
      alert(t('sub.iap.unavail'));
      return;
    }

    // 获取可用产品
    const offerings = await _purchasesPlugin.getOfferings();
    const product = offerings?.current?.availablePackages?.[0]?.product;
    
    if (!product) {
      alert(t('sub.no.product'));
      return;
    }

    // 发起购买
    const purchaseResult = await _purchasesPlugin.purchasePackage({
      aPackage: offerings.current.availablePackages[0],
    });

    // 验证收据
    if (purchaseResult?.customerInfo?.activeSubscriptions?.length > 0) {
      await verifyReceipt(purchaseResult);
      // 刷新用户信息
      await fetchUser();
      alert(t('sub.success'));
    }
  } catch (err) {
    if (err.userCancelled) return;
    console.error('[Subscription] Purchase failed:', err);
    alert(t('sub.failed') + (err.message || ''));
  }
}

// ============================================================================
// 收据验证
// ============================================================================
async function verifyReceipt(purchaseResult) {
  const receiptData = purchaseResult?.purchaseToken || purchaseResult?.receipt;
  if (!receiptData) return;

  try {
    await apiPost('/api/subscription/verify', {
      receiptData: typeof receiptData === 'string' ? receiptData : JSON.stringify(receiptData),
      productId: PRODUCT_ID,
    });
  } catch (err) {
    console.error('[Subscription] Receipt verification failed:', err);
    // 即使验证失败，RevenueCat 已经记录了购买
  }
}

// ============================================================================
// 恢复购买
// ============================================================================
export async function restorePurchases() {
  if (!_purchasesPlugin) {
    alert(t('sub.restore.only'));
    return;
  }

  try {
    const result = await _purchasesPlugin.restorePurchases();
    if (result?.customerInfo?.activeSubscriptions?.length > 0) {
      // 恢复成功，验证并更新状态
      await fetchUser();
      alert(t('sub.restore.ok'));
    } else {
      alert(t('sub.restore.none'));
    }
  } catch (err) {
    console.error('[Subscription] Restore failed:', err);
    alert(t('sub.restore.fail') + (err.message || ''));
  }
}

// ============================================================================
// Web 环境 — 订阅说明弹窗
// ============================================================================
function showSubscriptionInfo() {
  // 创建临时弹窗
  const overlay = document.createElement('div');
  overlay.className = 'auth-modal-overlay open';
  overlay.style.cssText = 'opacity:1;visibility:visible;';
  overlay.innerHTML = `
    <div class="auth-modal">
      <button class="auth-modal-close" id="sub-info-close">&times;</button>
      <div class="auth-view">
        <div class="auth-view-header">
          <span class="auth-view-icon" style="font-size:42px">☉</span>
          <h3>${t('auth.upgrade.title')}</h3>
        </div>
        <div class="sub-comparison">
          <div class="sub-plan free">
            <h4>${t('sub.free.name')}</h4>
            <div class="sub-price">${t('sub.free.price')}</div>
            <ul>
              <li>${t('sub.f1')}</li>
              <li>${t('sub.f2')}</li>
              <li>${t('sub.f3')}</li>
              <li>${t('sub.f4')}</li>
            </ul>
          </div>
          <div class="sub-plan premium">
            <div class="sub-badge">${t('sub.recommended')}</div>
            <h4>${t('sub.premium.name')}</h4>
            <div class="sub-price">${t('sub.premium.price')}</div>
            <ul>
              <li>${t('sub.f1')}</li>
              <li>${t('sub.f2')}</li>
              <li>${t('sub.f5')}</li>
              <li>${t('sub.f6')}</li>
              <li>${t('sub.f7')}</li>
            </ul>
          </div>
        </div>
        <div class="sub-note">
          <p>${t('sub.note')}</p>
          <p>${t('sub.contact')}</p>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
  overlay.querySelector('#sub-info-close').addEventListener('click', () => {
    overlay.remove();
  });
  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.remove();
  });
}

// ============================================================================
// 订阅状态查询
// ============================================================================
export function isPremium() {
  const user = getUser();
  return user?.subscription?.plan === 'premium';
}

export function getUsageInfo() {
  const user = getUser();
  const sub = user?.subscription || {};
  return {
    todayUsage: sub.todayUsage ?? 0,
    limit: sub.limit ?? 3,
    plan: sub.plan ?? 'free',
    isPremium: sub.plan === 'premium',
  };
}

// ============================================================================
// AI 对话前的订阅检查
// ============================================================================
export function checkCanChat() {
  if (!isLoggedIn()) {
    return { canChat: false, reason: 'login_required', message: t('sub.check.login') };
  }
  const usage = getUsageInfo();
  if (usage.isPremium) {
    return { canChat: true };
  }
  if (usage.todayUsage >= usage.limit) {
    return {
      canChat: false,
      reason: 'limit_reached',
      message: t('sub.check.limit') + ` (${usage.todayUsage}/${usage.limit})`,
    };
  }
  return {
    canChat: true,
    remaining: usage.limit - usage.todayUsage,
  };
}
