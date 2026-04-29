/**
 * Auth Module — 用户认证系统
 * 邮箱注册/登录 + Apple Sign-In + JWT 管理 + 订阅状态
 */
import { aiChatSetAuth } from './ai-chat.js';
import { t, getLang } from './i18n.js';

// ============================================================================
// 配置
// ============================================================================
const API_BASE = '';  // 同域部署，留空；Capacitor 打包时改为服务器地址
const TOKEN_KEY = 'jyotish_auth_token';
const USER_KEY = 'jyotish_auth_user';

// ============================================================================
// 状态
// ============================================================================
let _token = null;
let _user = null;
let _modalEl = null;
let _onAuthChange = null;  // 外部回调

// ============================================================================
// Token / 用户持久化
// ============================================================================
function loadSavedAuth() {
  try {
    _token = localStorage.getItem(TOKEN_KEY);
    const raw = localStorage.getItem(USER_KEY);
    _user = raw ? JSON.parse(raw) : null;
  } catch { _token = null; _user = null; }
}

function saveAuth(token, user) {
  _token = token;
  _user = user;
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
  // 同步给 ai-chat
  aiChatSetAuth(token, user);
  // 通知外部
  if (_onAuthChange) _onAuthChange(user);
  // 更新 UI
  updateHeaderUI();
}

// ============================================================================
// 公共 API
// ============================================================================
export function getToken() { return _token; }
export function getUser() { return _user; }
export function isLoggedIn() { return !!_token && !!_user; }

export function getApiBase() {
  // Capacitor 环境用服务器地址
  if (window.Capacitor?.isNativePlatform?.()) {
    return localStorage.getItem('jyotish_api_base') || 'https://your-server.com';
  }
  return API_BASE;
}

export function onAuthChange(cb) { _onAuthChange = cb; }

// ============================================================================
// 初始化
// ============================================================================
export function initAuth() {
  loadSavedAuth();
  createModal();
  updateHeaderUI();

  // 绑定 header 按钮
  document.addEventListener('click', e => {
    const btn = e.target.closest('[data-auth-action]');
    if (!btn) return;
    const action = btn.dataset.authAction;
    if (action === 'open-login') openModal('login');
    else if (action === 'open-register') openModal('register');
    else if (action === 'logout') doLogout();
    else if (action === 'open-profile') openModal('profile');
  });

  // 如果有 token，验证一下
  if (_token) {
    fetchUser().catch(() => {
      // token 过期，清除
      saveAuth(null, null);
    });
  }

  // 同步给 ai-chat
  aiChatSetAuth(_token, _user);
}

// ============================================================================
// Header UI 更新
// ============================================================================
function updateHeaderUI() {
  const containers = document.querySelectorAll('[data-auth-header]');
  containers.forEach(el => {
    if (_user) {
      const initial = (_user.email || 'U')[0].toUpperCase();
      const sub = _user.subscription || {};
      const planLabel = sub.plan === 'premium' ? '∞' : `${sub.todayUsage ?? 0}/3`;
      el.innerHTML = `
        <div class="auth-user-info">
          <button class="auth-avatar" data-auth-action="open-profile" title="${_user.email || ''}">${initial}</button>
          <span class="auth-usage-badge" data-auth-action="open-profile">${planLabel}</span>
        </div>
        <button class="auth-logout" data-auth-action="logout" title="${t('auth.logout')}">${t('auth.logout')}</button>
      `;
    } else {
      el.innerHTML = `
        <button class="auth-login-btn" data-auth-action="open-login">${t('auth.login')}</button>
      `;
    }
  });
}

// ============================================================================
// 模态框
// ============================================================================
function createModal() {
  _modalEl = document.createElement('div');
  _modalEl.className = 'auth-modal-overlay';
  _modalEl.id = 'auth-modal';
  _modalEl.innerHTML = `
    <div class="auth-modal">
      <button class="auth-modal-close" id="auth-modal-close">&times;</button>
      <div class="auth-modal-body" id="auth-modal-body"></div>
    </div>
  `;
  document.body.appendChild(_modalEl);

  _modalEl.querySelector('#auth-modal-close').addEventListener('click', closeModal);
  _modalEl.addEventListener('click', e => {
    if (e.target === _modalEl) closeModal();
  });
}

function openModal(view = 'login') {
  if (!_modalEl) return;
  const body = _modalEl.querySelector('#auth-modal-body');
  if (view === 'login') renderLoginView(body);
  else if (view === 'register') renderRegisterView(body);
  else if (view === 'profile') renderProfileView(body);
  else if (view === 'forgot') renderForgotView(body);
  _modalEl.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  if (!_modalEl) return;
  _modalEl.classList.remove('open');
  document.body.style.overflow = '';
}

// ============================================================================
// Login 视图
// ============================================================================
function renderLoginView(container) {
  container.innerHTML = `
    <div class="auth-view">
      <div class="auth-view-header">
        <span class="auth-view-icon">☉</span>
        <h3>${t('auth.login.title')}</h3>
        <p>${t('auth.login.desc')}</p>
      </div>
      <form id="auth-login-form" class="auth-form">
        <div class="form-group">
          <label>${t('auth.email')}</label>
          <input type="email" id="auth-login-email" placeholder="your@email.com" required autocomplete="email">
        </div>
        <div class="form-group">
          <label>${t('auth.password')}</label>
          <input type="password" id="auth-login-password" placeholder="${t('auth.pw.ph')}" required autocomplete="current-password">
        </div>
        <div class="auth-error hidden" id="auth-login-error"></div>
        <button type="submit" class="btn-primary auth-submit" id="auth-login-btn">
          <span class="btn-text">${t('auth.login.btn')}</span>
          <span class="btn-loading hidden"><span class="spinner"></span> ${t('auth.logging.in')}</span>
        </button>
      </form>
      <div class="auth-divider"><span>${t('auth.or')}</span></div>
      <button class="auth-apple-btn" id="auth-apple-login">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/></svg>
        ${t('auth.apple.login')}
      </button>
      <div class="auth-footer">
        ${t('auth.no.account')}<button class="auth-link" data-auth-action="open-register">${t('auth.register.link')}</button>
      </div>
    </div>
  `;
  bindLoginForm(container);
  bindAppleLogin(container);
  bindAuthLinks(container);
}

function bindLoginForm(container) {
  const form = container.querySelector('#auth-login-form');
  const errEl = container.querySelector('#auth-login-error');
  const btnText = container.querySelector('#auth-login-btn .btn-text');
  const btnLoading = container.querySelector('#auth-login-btn .btn-loading');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = container.querySelector('#auth-login-email').value.trim();
    const password = container.querySelector('#auth-login-password').value;
    if (!email || !password) return;

    btnText.classList.add('hidden');
    btnLoading.classList.remove('hidden');
    errEl.classList.add('hidden');

    try {
      const res = await apiPost('/api/auth/login', { email, password });
      saveAuth(res.token, res.user);
      closeModal();
    } catch (err) {
      errEl.textContent = err.message || t('auth.login.failed');
      errEl.classList.remove('hidden');
    } finally {
      btnText.classList.remove('hidden');
      btnLoading.classList.add('hidden');
    }
  });
}

// ============================================================================
// Register 视图
// ============================================================================
function renderRegisterView(container) {
  container.innerHTML = `
    <div class="auth-view">
      <div class="auth-view-header">
        <span class="auth-view-icon">☉</span>
        <h3>${t('auth.register.title')}</h3>
        <p>${t('auth.register.desc')}</p>
      </div>
      <form id="auth-register-form" class="auth-form">
        <div class="form-group">
          <label>${t('auth.email')}</label>
          <input type="email" id="auth-register-email" placeholder="your@email.com" required autocomplete="email">
        </div>
        <div class="form-group">
          <label>${t('auth.password')}</label>
          <input type="password" id="auth-register-password" placeholder="${t('auth.pw.min.ph')}" required minlength="6" autocomplete="new-password">
        </div>
        <div class="form-group">
          <label>${t('auth.pw2')}</label>
          <input type="password" id="auth-register-password2" placeholder="${t('auth.pw2.ph')}" required minlength="6" autocomplete="new-password">
        </div>
        <div class="auth-error hidden" id="auth-register-error"></div>
        <button type="submit" class="btn-primary auth-submit" id="auth-register-btn">
          <span class="btn-text">${t('auth.register.btn')}</span>
          <span class="btn-loading hidden"><span class="spinner"></span> ${t('auth.registering')}</span>
        </button>
      </form>
      <div class="auth-divider"><span>${t('auth.or')}</span></div>
      <button class="auth-apple-btn" id="auth-apple-register">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/></svg>
        ${t('auth.apple.login')}
      </button>
      <div class="auth-footer">
        ${t('auth.has.account')}<button class="auth-link" data-auth-action="open-login">${t('auth.login.link')}</button>
      </div>
    </div>
  `;
  bindRegisterForm(container);
  bindAppleLogin(container);
  bindAuthLinks(container);
}

function bindRegisterForm(container) {
  const form = container.querySelector('#auth-register-form');
  const errEl = container.querySelector('#auth-register-error');
  const btnText = container.querySelector('#auth-register-btn .btn-text');
  const btnLoading = container.querySelector('#auth-register-btn .btn-loading');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = container.querySelector('#auth-register-email').value.trim();
    const password = container.querySelector('#auth-register-password').value;
    const password2 = container.querySelector('#auth-register-password2').value;

    if (password !== password2) {
      errEl.textContent = t('auth.pw.mismatch');
      errEl.classList.remove('hidden');
      return;
    }
    if (password.length < 6) {
      errEl.textContent = t('auth.pw.short');
      errEl.classList.remove('hidden');
      return;
    }

    btnText.classList.add('hidden');
    btnLoading.classList.remove('hidden');
    errEl.classList.add('hidden');

    try {
      const res = await apiPost('/api/auth/register', { email, password });
      saveAuth(res.token, res.user);
      closeModal();
    } catch (err) {
      errEl.textContent = err.message || t('auth.register.failed');
      errEl.classList.remove('hidden');
    } finally {
      btnText.classList.remove('hidden');
      btnLoading.classList.add('hidden');
    }
  });
}

// ============================================================================
// Apple Sign-In
// ============================================================================
function bindAppleLogin(container) {
  container.querySelectorAll('[id^="auth-apple-"]').forEach(btn => {
    btn.addEventListener('click', async () => {
      try {
        // Capacitor 原生环境
        if (window.Capacitor?.Plugins?.SignInWithApple) {
          const result = await window.Capacitor.Plugins.SignInWithApple.authorize({
            clientId: localStorage.getItem('jyotish_apple_bundle_id') || 'com.jyotish.app',
            redirectURI: window.location.origin,
            scopes: 'email name',
          });
          await handleAppleToken(result.identityToken || result.idToken);
        } else {
          // Web 环境 - 使用 Apple JS SDK
          if (!window.AppleID) {
            alert(t('auth.apple.device'));
            return;
          }
          // Web 方式由 Apple JS SDK 处理
          const data = await window.AppleID.auth.signIn();
          await handleAppleToken(data.authorization.id_token);
        }
      } catch (err) {
        console.error('[Auth] Apple Sign-In error:', err);
        if (err.message !== 'popup_closed_by_user') {
          alert(t('auth.apple.failed') + (err.message || t('auth.error.unknown')));
        }
      }
    });
  });
}

async function handleAppleToken(idToken) {
  try {
    const res = await apiPost('/api/auth/apple', { idToken });
    saveAuth(res.token, res.user);
    closeModal();
  } catch (err) {
    alert(t('auth.apple.failed') + (err.message || t('auth.error.unknown')));
  }
}

// ============================================================================
// Profile 视图
// ============================================================================
function renderProfileView(container) {
  if (!_user) { closeModal(); return; }
  const sub = _user.subscription || {};
  const isPremium = sub.plan === 'premium';
  const usage = sub.todayUsage ?? 0;
  const limit = sub.limit ?? 3;

  container.innerHTML = `
    <div class="auth-view">
      <div class="auth-view-header">
        <div class="auth-profile-avatar">${(_user.email || 'U')[0].toUpperCase()}</div>
        <h3>${_user.email || t('auth.profile')}</h3>
        <p class="auth-plan-label ${isPremium ? 'premium' : 'free'}">
          ${isPremium ? t('auth.premium.plan') : t('auth.free.plan').replace('{0}', usage).replace('{1}', limit)}
        </p>
      </div>
      ${!isPremium ? `
        <div class="auth-upgrade-card">
          <h4>${t('auth.upgrade.title')}</h4>
          <ul class="auth-upgrade-features">
            <li>${t('auth.upgrade.1')}</li>
            <li>${t('auth.upgrade.2')}</li>
            <li>${t('auth.upgrade.3')}</li>
            <li>${t('auth.upgrade.4')}</li>
          </ul>
          <button class="btn-primary auth-upgrade-btn" id="auth-upgrade-btn">${t('auth.upgrade.btn')}</button>
        </div>
      ` : ''}
      <div class="auth-profile-actions">
        <button class="auth-profile-btn" data-auth-action="logout">${t('auth.logout')}</button>
      </div>
    </div>
  `;

  // 升级按钮
  const upgradeBtn = container.querySelector('#auth-upgrade-btn');
  if (upgradeBtn) {
    upgradeBtn.addEventListener('click', () => {
      // 触发 IAP（由 subscription.js 处理）
      const event = new CustomEvent('jyotish:subscribe');
      document.dispatchEvent(event);
    });
  }

  bindAuthLinks(container);
}

// ============================================================================
// Forgot Password 视图（占位）
// ============================================================================
function renderForgotView(container) {
  container.innerHTML = `
    <div class="auth-view">
      <div class="auth-view-header">
        <span class="auth-view-icon">☉</span>
        <h3>${t('auth.reset.title')}</h3>
        <p>${t('auth.reset.desc')}</p>
      </div>
      <form id="auth-forgot-form" class="auth-form">
        <div class="form-group">
          <label>${t('auth.email')}</label>
          <input type="email" id="auth-forgot-email" placeholder="your@email.com" required>
        </div>
        <div class="auth-error hidden" id="auth-forgot-error"></div>
        <button type="submit" class="btn-primary auth-submit">
          <span class="btn-text">${t('auth.reset.btn')}</span>
        </button>
      </form>
      <div class="auth-footer">
        <button class="auth-link" data-auth-action="open-login">${t('auth.back.login')}</button>
      </div>
    </div>
  `;
  bindAuthLinks(container);
}

// ============================================================================
// 视图间跳转链接
// ============================================================================
function bindAuthLinks(container) {
  container.querySelectorAll('[data-auth-action]').forEach(el => {
    // 避免重复绑定
    if (el._authBound) return;
    el._authBound = true;
    el.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const action = el.dataset.authAction;
      if (action === 'open-login') openModal('login');
      else if (action === 'open-register') openModal('register');
      else if (action === 'logout') { doLogout(); closeModal(); }
      else if (action === 'open-profile') openModal('profile');
    });
  });
}

// ============================================================================
// Logout
// ============================================================================
function doLogout() {
  saveAuth(null, null);
  closeModal();
}

// ============================================================================
// API 调用
// ============================================================================
async function apiPost(path, body) {
  const base = getApiBase();
  const headers = { 'Content-Type': 'application/json' };
  if (_token) headers['Authorization'] = `Bearer ${_token}`;

  const resp = await fetch(`${base}${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  const data = await resp.json();
  if (!resp.ok) {
    throw new Error(data.error || data.message || t('auth.request.failed') + ` (${resp.status})`);
  }
  return data;
}

async function fetchUser() {
  const base = getApiBase();
  const resp = await fetch(`${base}/api/auth/me`, {
    headers: { 'Authorization': `Bearer ${_token}` },
  });
  if (!resp.ok) throw new Error(t('auth.token.expired'));
  const data = await resp.json();
  // 更新本地用户数据
  _user = data.user || data;
  localStorage.setItem(USER_KEY, JSON.stringify(_user));
  updateHeaderUI();
  aiChatSetAuth(_token, _user);
  return _user;
}

// 暴露 apiPost 给其他模块使用
export { apiPost, fetchUser };
