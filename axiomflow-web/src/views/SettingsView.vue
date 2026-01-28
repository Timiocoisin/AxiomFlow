<template>
  <section class="settings">
    <div class="settings-container">
      <div class="settings-header">
        <h2 class="settings-title">账户设置</h2>
        <p class="settings-subtitle">管理您的账户信息和安全设置</p>
      </div>
      
      <!-- 账号信息 + 安全设置：合成一个大卡片 -->
      <div class="settings-section glass-card settings-section-combined">
        <!-- 账号信息子区域 -->
            <div class="settings-subsection">
          <div class="subsection-header">
            <div class="subsection-icon account-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div>
              <h3 class="settings-section-title">账号信息</h3>
              <p class="settings-section-desc">管理您的基本资料和邮箱信息</p>
            </div>
          </div>

          <div class="settings-grid">
            <div class="setting-card email-card">
              <div class="card-icon-wrapper">
                <div class="setting-icon email-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <polyline points="22,6 12,13 2,6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
              </div>
              <div class="setting-card-header">
                <span class="setting-label">邮箱地址</span>
                <span v-if="userStore.user?.email_verified" class="email-verified-badge">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  已验证
                </span>
                <span v-else class="email-unverified-badge">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                    <path d="M12 8v4M12 16h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  未验证
                </span>
              </div>
              <div class="setting-card-content">
                <div class="email-display">
                  <span class="email-text">{{ userStore.user?.email }}</span>
                </div>
                <p
                  v-if="!userStore.user?.email_verified"
                  class="email-status-description email-status-description-unverified"
                >
                  邮箱未验证，将限制部分安全操作，建议尽快完成验证。
                </p>
                <button
                  v-if="!userStore.user?.email_verified"
                  class="settings-action-btn"
                  @click="handleResendVerification"
                  :disabled="resendingVerification"
                >
                  <span v-if="resendingVerification" class="loading-spinner-small"></span>
                  <span>{{ resendingVerification ? "发送中..." : "发送验证邮件" }}</span>
                </button>
              </div>
            </div>

            <div class="setting-card user-card">
              <div class="card-icon-wrapper">
                <div class="user-avatar-wrapper" @click="openAvatarModal">
                  <div class="user-avatar" v-if="userStore.user?.avatar">
                    <img :src="userStore.user.avatar" :alt="userStore.user?.name || '用户头像'" />
                  </div>
                  <div class="user-avatar-placeholder" v-else>
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <button
                    type="button"
                    class="avatar-edit-icon"
                    aria-label="编辑头像"
                  >
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 20h9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L10 16l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                </div>
              </div>
              <div class="setting-card-header">
                <span class="setting-label">用户名</span>
              </div>
              <div class="setting-card-content">
                <div class="name-display name-editable">
                  <template v-if="editingName">
                    <input
                      v-model="nameInput"
                      class="name-input"
                      type="text"
                      maxlength="50"
                      placeholder="请输入昵称"
                      @keyup.enter="saveName"
                      @keyup.esc="cancelEditName"
                    />
                    <div class="name-edit-actions">
                      <button
                        type="button"
                        class="name-save-btn"
                        @click="saveName"
                        :disabled="savingName"
                      >
                        <span v-if="savingName" class="loading-spinner-small"></span>
                        <span>{{ savingName ? "保存中..." : "保存" }}</span>
                      </button>
                      <button
                        type="button"
                        class="name-cancel-btn"
                        @click="cancelEditName"
                        :disabled="savingName"
                      >
                        取消
                      </button>
                    </div>
                  </template>
                  <template v-else>
                    <button
                      type="button"
                      class="name-text-button"
                      @click="startEditName"
                    >
                      <span class="name-text">{{ userStore.user?.name || "未设置" }}</span>
                      <span class="name-edit-icon">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M12 20h9" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                          <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L10 16l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                      </span>
                    </button>
                  </template>
                </div>
              </div>
            </div>

            <div class="setting-card provider-card">
              <div class="card-icon-wrapper">
                <div class="setting-icon provider-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
              </div>
              <div class="setting-card-header">
                <span class="setting-label">登录方式</span>
              </div>
              <div class="setting-card-content">
                <div class="provider-badge" :class="`provider-${currentLoginMethod}`">
                  {{ currentLoginMethodText }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 分隔线 -->
        <div class="settings-subsection-divider"></div>

        <!-- 安全设置子区域 -->
        <div class="settings-subsection">
          <!-- 顶部邮箱未验证提醒条 -->
          <div
            v-if="!isEmailVerified"
            class="security-warning-banner"
          >
            <div class="security-warning-dot"></div>
            <div class="security-warning-text">
              <div class="security-warning-title">邮箱尚未验证</div>
              <div class="security-warning-desc">
                为了保障账户安全，请先完成邮箱验证，部分安全操作在验证前将被限制。
              </div>
            </div>
            <button
              type="button"
              class="security-warning-action"
              @click="handleResendVerification"
              :disabled="resendingVerification"
            >
              {{ resendingVerification ? "发送中..." : "重新发送验证邮件" }}
            </button>
          </div>

          <div class="subsection-header">
            <div class="subsection-icon security-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div>
              <h3 class="settings-section-title">安全设置</h3>
              <p class="settings-section-desc">
                通过密码、登录记录和会话管理保护您的账户安全
              </p>
            </div>
          </div>

          <div class="settings-grid">
            <!-- 修改密码 -->
            <div class="setting-card security-card password-card">
              <div class="card-icon-wrapper">
                <div class="setting-icon password-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </div>
              </div>
              <div class="setting-card-header">
                <span class="setting-label">修改密码</span>
              </div>
              <div class="setting-card-content">
                <button
                  class="settings-action-btn"
                  @click="showChangePasswordModal = true"
                  :disabled="!canChangePassword || !isEmailVerified"
                >
                  修改密码
                </button>
                <p v-if="!canChangePassword" class="settings-hint">
                  当前账户暂不支持直接修改密码，请先通过“忘记密码”设置登录密码。
                </p>
                <p v-else-if="!isEmailVerified" class="settings-hint">
                  当前邮箱未验证，部分安全操作将受限，建议尽快完成验证。
                </p>
              </div>
            </div>

            <!-- 登录历史 -->
            <div class="setting-card security-card history-card">
              <div class="card-icon-wrapper">
                <div class="setting-icon history-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" />
                    <polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </div>
              </div>
              <div class="setting-card-header">
                <span class="setting-label">登录历史</span>
              </div>
              <div class="setting-card-content">
                <button
                  class="settings-action-btn"
                  @click="showLoginHistoryModal = true"
                  :disabled="!isEmailVerified"
                >
                  查看登录历史
                </button>
              </div>
            </div>

            <!-- 活跃会话 -->
            <div class="setting-card security-card session-card">
              <div class="card-icon-wrapper">
                <div class="setting-icon session-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                    <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
                  </svg>
                </div>
              </div>
              <div class="setting-card-header">
                <div class="setting-card-header-main">
                  <span class="setting-label">活跃会话</span>
                  <span
                    v-if="sessions.length > 0"
                    class="security-status-badge security-status-badge-warning"
                  >
                    <span class="security-status-dot"></span>
                    {{ sessions.length }} 个活跃会话
                  </span>
                </div>
                <p
                  v-if="sessions.length > 0"
                  class="setting-card-subtext"
                >
                  建议定期检查并关闭不认识的设备登录。
                </p>
              </div>
              <div class="setting-card-content">
                <button
                  class="settings-action-btn"
                  @click="showSessionsModal = true"
                  :disabled="!isEmailVerified"
                >
                  管理会话
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- 修改密码模态框 -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showChangePasswordModal"
          class="modal-overlay"
          @click.self="showChangePasswordModal = false"
          role="dialog"
          aria-labelledby="change-password-title"
          aria-modal="true"
        >
          <div class="modal-content glass-card">
            <div class="modal-header">
              <h2 id="change-password-title">修改密码</h2>
              <button
                class="modal-close"
                @click="showChangePasswordModal = false"
                aria-label="关闭"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label" for="current-password">当前密码</label>
                <div class="password-input-wrapper">
                  <input
                    id="current-password"
                    v-model="changePasswordData.currentPassword"
                    :type="showCurrentPassword ? 'text' : 'password'"
                    class="form-input"
                    placeholder="请输入当前密码"
                    autocomplete="current-password"
                    aria-required="true"
                    @keyup.enter="handleChangePassword"
                  />
                  <button
                    type="button"
                    class="password-toggle"
                    @click="showCurrentPassword = !showCurrentPassword"
                    tabindex="-1"
                  >
                    <svg v-if="showCurrentPassword" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M1 12S5 4 12 4S23 12 23 12S19 20 12 20S1 12 1 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20C7 20 2.73 16.39 1 12C2.73 7.61 7 4 12 4C13.5 4 14.9 4.35 16.12 4.95L17.94 3.13M17.94 17.94L3.13 3.13M17.94 17.94L20.87 20.87M3.13 3.13L1 1M20.87 20.87L23 23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                </div>
              </div>
              <div class="form-group">
                <label class="form-label" for="new-password">新密码</label>
                <div class="password-input-wrapper">
                  <input
                    id="new-password"
                    v-model="changePasswordData.newPassword"
                    :type="showNewPassword ? 'text' : 'password'"
                    class="form-input"
                    placeholder="请输入新密码（至少8位）"
                    autocomplete="new-password"
                    aria-required="true"
                    minlength="8"
                    @keyup.enter="handleChangePassword"
                  />
                  <button
                    type="button"
                    class="password-toggle"
                    @click="showNewPassword = !showNewPassword"
                    tabindex="-1"
                  >
                    <svg v-if="showNewPassword" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M1 12S5 4 12 4S23 12 23 12S19 20 12 20S1 12 1 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20C7 20 2.73 16.39 1 12C2.73 7.61 7 4 12 4C13.5 4 14.9 4.35 16.12 4.95L17.94 3.13M17.94 17.94L3.13 3.13M17.94 17.94L20.87 20.87M3.13 3.13L1 1M20.87 20.87L23 23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                </div>
              </div>
              <div class="form-group">
                <label class="form-label" for="confirm-new-password">确认新密码</label>
                <div class="password-input-wrapper">
                  <input
                    id="confirm-new-password"
                    v-model="changePasswordData.confirmPassword"
                    :type="showConfirmPassword ? 'text' : 'password'"
                    class="form-input"
                    placeholder="请再次输入新密码"
                    autocomplete="new-password"
                    aria-required="true"
                    @keyup.enter="handleChangePassword"
                  />
                  <button
                    type="button"
                    class="password-toggle"
                    @click="showConfirmPassword = !showConfirmPassword"
                    tabindex="-1"
                  >
                    <svg v-if="showConfirmPassword" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M1 12S5 4 12 4S23 12 23 12S19 20 12 20S1 12 1 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20C7 20 2.73 16.39 1 12C2.73 7.61 7 4 12 4C13.5 4 14.9 4.35 16.12 4.95L17.94 3.13M17.94 17.94L3.13 3.13M17.94 17.94L20.87 20.87M3.13 3.13L1 1M20.87 20.87L23 23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                </div>
              </div>
              <div v-if="changePasswordError" class="field-error">{{ changePasswordError }}</div>
              <button
                class="auth-button"
                @click="handleChangePassword"
                :disabled="changingPassword || !changePasswordData.currentPassword || !changePasswordData.newPassword || !changePasswordData.confirmPassword"
                style="width: 100%; margin-top: 20px;"
              >
                <span v-if="changingPassword" class="loading-spinner"></span>
                <span>{{ changingPassword ? "修改中..." : "修改密码" }}</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 登录历史模态框 -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showLoginHistoryModal"
          class="modal-overlay"
          @click.self="showLoginHistoryModal = false"
          role="dialog"
          aria-labelledby="login-history-title"
          aria-modal="true"
          @keyup.esc.stop.prevent="showLoginHistoryModal = false"
          tabindex="-1"
        >
          <div class="modal-content glass-card modal-content-large">
            <div class="modal-header">
              <h2 id="login-history-title">登录历史</h2>
              <button
                class="modal-close"
                @click="showLoginHistoryModal = false"
                aria-label="关闭"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div v-if="loadingLoginHistory" class="loading-state">
                <div class="loading-spinner"></div>
                <p>加载中...</p>
              </div>
              <div v-else-if="loginHistory.length === 0" class="empty-state">
                <div class="empty-state-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
                <p>当前没有登录记录，一切正常。</p>
              </div>
              <div v-else>
                <div class="history-list">
                  <div
                    v-for="item in paginatedLoginHistory"
                    :key="item.id"
                    class="history-item"
                    :class="{ 'history-item-success': item.success, 'history-item-failed': !item.success }"
                  >
                  <div class="history-item-icon">
                    <svg v-if="item.success" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      <path d="M12 8v4M12 16h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <div class="history-item-content">
                    <div class="history-item-header">
                      <span class="history-item-status">{{ item.success ? "登录成功" : "登录失败" }}</span>
                      <span class="history-item-time">{{ formatTime(item.created_at) }}</span>
                    </div>
                    <!-- 设备 + IP 优先的一行摘要 -->
                    <div class="history-item-primary-meta">
                      <span class="history-item-device">
                        {{ item.device_type || "未知设备" }}
                      </span>
                      <span class="history-item-separator">•</span>
                      <span class="history-item-ip">
                        {{ item.ip || "IP 未知" }}
                      </span>
                    </div>
                    <!-- 其它信息折行为次级 -->
                    <div class="history-item-details">
                      <div class="history-item-detail history-item-detail-secondary">
                        <span class="detail-label">登录方式：</span>
                        <span class="detail-value">{{ formatLoginMethod(item.login_method) }}</span>
                      </div>
                      <div class="history-item-detail history-item-detail-secondary">
                        <span class="detail-label">浏览器：</span>
                        <span class="detail-value">{{ item.browser || "未知" }}</span>
                      </div>
                      <div class="history-item-detail history-item-detail-secondary">
                        <span class="detail-label">操作系统：</span>
                        <span class="detail-value">{{ item.os || "未知" }}</span>
                      </div>
                      <div
                        v-if="item.reason && !item.success"
                        class="history-item-detail history-item-detail-secondary"
                      >
                        <span class="detail-label">失败原因：</span>
                        <span class="detail-value error-text">{{ formatFailureReason(item.reason) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                </div>
                
                <!-- 分页控件 -->
                <div v-if="totalLoginHistoryPages > 1" class="pagination-container">
                  <div class="pagination-info">
                    <span>共 {{ loginHistory.length }} 条记录</span>
                    <span>第 {{ currentLoginHistoryPage }} / {{ totalLoginHistoryPages }} 页</span>
                  </div>
                  <div class="pagination-controls">
                    <button
                      class="pagination-btn"
                      :class="{ 'pagination-btn-disabled': currentLoginHistoryPage === 1 }"
                      @click="goToLoginHistoryPage(currentLoginHistoryPage - 1)"
                      :disabled="currentLoginHistoryPage === 1"
                    >
                      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </button>
                    <div class="pagination-pages">
                      <button
                        v-for="page in visibleLoginHistoryPages"
                        :key="page"
                        class="pagination-page-btn"
                        :class="{ 
                          'pagination-page-btn-active': page === currentLoginHistoryPage,
                          'pagination-page-btn-ellipsis': page === -1
                        }"
                        @click="goToLoginHistoryPage(page)"
                        :disabled="page === -1"
                      >
                        {{ page === -1 ? '...' : page }}
                      </button>
                    </div>
                    <button
                      class="pagination-btn"
                      :class="{ 'pagination-btn-disabled': currentLoginHistoryPage === totalLoginHistoryPages }"
                      @click="goToLoginHistoryPage(currentLoginHistoryPage + 1)"
                      :disabled="currentLoginHistoryPage === totalLoginHistoryPages"
                    >
                      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 活跃会话模态框 -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showSessionsModal"
          class="modal-overlay"
          @click.self="showSessionsModal = false"
          role="dialog"
          aria-labelledby="sessions-title"
          aria-modal="true"
          @keyup.esc.stop.prevent="showSessionsModal = false"
          tabindex="-1"
        >
          <div class="modal-content glass-card modal-content-large">
            <div class="modal-header">
              <h2 id="sessions-title">活跃会话</h2>
              <button
                class="modal-close"
                @click="showSessionsModal = false"
                aria-label="关闭"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div v-if="loadingSessions" class="loading-state">
                <div class="loading-spinner"></div>
                <p>加载中...</p>
              </div>
              <div v-else-if="sessions.length === 0" class="empty-state">
                <div class="empty-state-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
                <p>当前没有其他活跃会话，一切正常。</p>
              </div>
              <div v-else>
                <div class="sessions-list">
                  <div
                    v-for="session in orderedPaginatedSessions"
                    :key="session.token"
                    class="session-item"
                    :class="{ 'session-item-current': session.is_current }"
                  >
                    <div class="session-item-icon">
                      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
                        <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                      </svg>
                    </div>
                    <div class="session-item-content">
                      <div class="session-item-header">
                        <span class="session-item-token">Token: {{ session.token }}</span>
                        <span v-if="session.is_current" class="session-item-badge">当前会话</span>
                      </div>
                      <div class="session-item-details">
                        <div class="session-item-detail">
                          <span class="detail-label">IP地址：</span>
                          <span class="detail-value">{{ session.ip || "未知" }}</span>
                        </div>
                        <div class="session-item-detail">
                          <span class="detail-label">设备：</span>
                          <span class="detail-value">{{ parseUserAgent(session.user_agent) }}</span>
                        </div>
                        <div class="session-item-detail">
                          <span class="detail-label">创建时间：</span>
                          <span class="detail-value">{{ formatTime(session.created_at) }}</span>
                        </div>
                        <div v-if="session.last_used_at" class="session-item-detail">
                          <span class="detail-label">最后使用：</span>
                          <span class="detail-value">{{ formatTime(session.last_used_at) }}</span>
                        </div>
                      </div>
                    </div>
                    <div class="session-item-actions">
                      <button
                        v-if="!session.is_current"
                        class="session-revoke-btn"
                        @click="handleRevokeSession(session.session_id || session.token)"
                        :disabled="revokingSession === (session.session_id || session.token)"
                      >
                        <span v-if="revokingSession === (session.session_id || session.token)" class="loading-spinner-small"></span>
                        <span>{{ revokingSession === (session.session_id || session.token) ? "撤销中..." : "撤销" }}</span>
                      </button>
                    </div>
                  </div>
                </div>

                <!-- 分页控件：样式与登录历史保持一致 -->
                <div v-if="totalSessionsPages > 1" class="pagination-container">
                  <div class="pagination-info">
                    <span>共 {{ sessions.length }} 个会话</span>
                    <span>第 {{ currentSessionsPage }} / {{ totalSessionsPages }} 页</span>
                  </div>
                  <div class="pagination-controls">
                    <button
                      class="pagination-btn"
                      :class="{ 'pagination-btn-disabled': currentSessionsPage === 1 }"
                      @click="goToSessionsPage(currentSessionsPage - 1)"
                      :disabled="currentSessionsPage === 1"
                    >
                      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </button>
                    <div class="pagination-pages">
                      <button
                        v-for="page in visibleSessionsPages"
                        :key="page"
                        class="pagination-page-btn"
                        :class="{
                          'pagination-page-btn-active': page === currentSessionsPage,
                          'pagination-page-btn-ellipsis': page === -1
                        }"
                        @click="goToSessionsPage(page)"
                        :disabled="page === -1"
                      >
                        {{ page === -1 ? '...' : page }}
                      </button>
                    </div>
                    <button
                      class="pagination-btn"
                      :class="{ 'pagination-btn-disabled': currentSessionsPage === totalSessionsPages }"
                      @click="goToSessionsPage(currentSessionsPage + 1)"
                      :disabled="currentSessionsPage === totalSessionsPages"
                    >
                      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </button>
                  </div>
                </div>

                <div class="sessions-actions">
                  <button
                    class="auth-button auth-button-danger-outlined"
                    @click="handleRevokeAllSessions"
                    :disabled="revokingAllSessions"
                  >
                    <span v-if="revokingAllSessions" class="loading-spinner"></span>
                    <span>{{ revokingAllSessions ? "撤销中..." : "撤销所有会话" }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 头像上传 / 裁剪模态框 -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showAvatarModal"
          class="modal-overlay"
          @click.self="showAvatarModal = false"
          role="dialog"
          aria-modal="true"
          aria-labelledby="avatar-modal-title"
          @keyup.esc.stop.prevent="showAvatarModal = false"
          tabindex="-1"
        >
          <div class="modal-content glass-card modal-content-avatar">
            <div class="modal-header">
              <h2 id="avatar-modal-title">编辑头像</h2>
              <button
                class="modal-close"
                @click="showAvatarModal = false"
                aria-label="关闭"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
            <div class="modal-body avatar-modal-body">
              <div class="avatar-editor-grid">
                <div class="avatar-preview-panel">
                  <div class="avatar-preview-wrapper">
                    <div class="avatar-preview-mask">
                      <div class="avatar-preview-circle">
                        <img
                          v-if="avatarPreviewUrl || userStore.user?.avatar"
                          :src="avatarPreviewUrl || userStore.user?.avatar"
                          alt="头像预览"
                          :style="{ transform: `scale(${avatarZoom})` }"
                        />
                        <div v-else class="avatar-preview-placeholder">
                          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                          </svg>
                        </div>
                      </div>
                    </div>
                  </div>
                  <p class="avatar-helper-text">
                    头像将以居中区域裁剪为正方形，适配圆形展示。
                  </p>
                </div>
                <div class="avatar-control-panel">
                  <div class="form-group">
                    <label class="form-label">选择图片</label>
                    <label class="avatar-upload-btn">
                      <input
                        type="file"
                        accept="image/*"
                        @change="handleAvatarFileChange"
                      />
                      <span>上传图片</span>
                    </label>
                    <p class="avatar-upload-hint">推荐使用清晰的正方形图片，支持 JPG / PNG，最大 2MB。</p>
                  </div>
                  <div class="form-group">
                    <label class="form-label">缩放</label>
                    <div class="avatar-zoom-row">
                      <span class="avatar-zoom-label">缩小</span>
                      <input
                        type="range"
                        min="1"
                        max="2"
                        step="0.05"
                        v-model.number="avatarZoom"
                        class="avatar-zoom-slider"
                      />
                      <span class="avatar-zoom-percentage">
                        {{ Math.round(avatarZoom * 100) }}%
                      </span>
                      <span class="avatar-zoom-label">放大</span>
                    </div>
                  </div>
                  <div class="avatar-actions">
                    <button
                      class="auth-button"
                      type="button"
                      @click="handleSaveAvatar"
                      :disabled="avatarUploading"
                    >
                      <span v-if="avatarUploading" class="loading-spinner"></span>
                      <span>{{ avatarUploading ? "保存中..." : "保存头像" }}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </section>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";
import {
  changePassword,
  getLoginHistory,
  getSessions,
  revokeSession,
  revokeAllSessions,
  sendEmailVerification,
  uploadAvatar,
  updateProfile,
  type LoginHistoryItem,
  type SessionInfo,
} from "@/lib/api";

const router = useRouter();
const userStore = useUserStore();

const showChangePasswordModal = ref(false);
const showLoginHistoryModal = ref(false);
const showSessionsModal = ref(false);
const show2FAModal = ref(false); // 已废弃功能占位，保持为 false，不再使用
const showSocialBindingModal = ref(false); // 已废弃
const showBreachCheckModal = ref(false); // 已废弃

const changePasswordData = ref({
  currentPassword: "",
  newPassword: "",
  confirmPassword: "",
});
const showCurrentPassword = ref(false);
const showNewPassword = ref(false);
const showConfirmPassword = ref(false);
const changingPassword = ref(false);
const changePasswordError = ref("");

const loginHistory = ref<LoginHistoryItem[]>([]);
const loadingLoginHistory = ref(false);
const currentLoginHistoryPage = ref(1);
const loginHistoryPageSize = 3; // 每页显示3条记录

const currentLoginMethod = ref<"email" | "google" | "github">("email");

const sessions = ref<SessionInfo[]>([]);
const loadingSessions = ref(false);
const currentSessionsPage = ref(1);
const sessionsPageSize = 3; // 每页3条，与登录历史保持一致
const revokingSession = ref<string | null>(null);
const revokingAllSessions = ref(false);

const resendingVerification = ref(false);

const modalBodyLockCount = ref(0);

const lockBodyScroll = () => {
  if (typeof document === "undefined") return;
  if (modalBodyLockCount.value === 0) {
    document.body.dataset.prevOverflow = document.body.style.overflow || "";
    document.body.style.overflow = "hidden";
  }
  modalBodyLockCount.value += 1;
};

const unlockBodyScroll = () => {
  if (typeof document === "undefined") return;
  if (modalBodyLockCount.value <= 0) return;
  modalBodyLockCount.value -= 1;
  if (modalBodyLockCount.value === 0) {
    const prev = document.body.dataset.prevOverflow;
    if (prev !== undefined) {
      document.body.style.overflow = prev;
      delete document.body.dataset.prevOverflow;
    } else {
      document.body.style.overflow = "";
    }
  }
};

// 头像上传 / 裁剪
const showAvatarModal = ref(false);
const avatarPreviewUrl = ref<string | null>(null);
const avatarImage = ref<HTMLImageElement | null>(null);
const avatarZoom = ref(1.1);
const avatarUploading = ref(false);

// 头像引导提示：仅首次显示一次
const showAvatarHint = ref(false);

// 用户名内联编辑
const editingName = ref(false);
const nameInput = ref("");
const savingName = ref(false);

// 以下安全扩展功能（2FA / 社交绑定 / 密码泄露检测）已下线，仅保留占位变量避免报错
const twoFAStatus = ref(null);
const twoFASetup = ref(null);
const twoFACode = ref("");
const twoFABackupCodes = ref<string[]>([]);
const loading2FA = ref(false);

const socialBindings = ref<any[]>([]);
const loadingSocialBindings = ref(false);

const breachCheckPassword = ref("");
const breachCheckResult = ref<any | null>(null);
const checkingBreach = ref(false);

const currentLoginMethodText = computed(() => {
  return formatLoginMethod(currentLoginMethod.value);
});

const canChangePassword = computed(() => {
  // provider 不代表“当前登录方式”，也不应作为权限依据；
  // 是否能改密码取决于账户是否设置过密码（OAuth-only 用户需要先走“忘记密码”设置密码）
  return !!userStore.user?.has_password;
});

const isEmailVerified = computed(() => {
  return !!userStore.user?.email_verified;
});

const showToast = (type: "success" | "error" | "warning" | "info", title: string, message?: string) => {
  const event = new CustomEvent("show-toast", {
    detail: { type, title, message },
  });
  window.dispatchEvent(event);
};

const initAvatarHint = () => {
  try {
    const seen = typeof window !== "undefined" ? window.localStorage.getItem("settings_avatar_hint_seen") : "1";
    showAvatarHint.value = !seen;
  } catch {
    showAvatarHint.value = true;
  }
};

// 计算分页后的活跃会话列表
const totalSessionsPages = computed(() => {
  return sessions.value.length === 0 ? 1 : Math.ceil(sessions.value.length / sessionsPageSize);
});

const paginatedSessions = computed(() => {
  const start = (currentSessionsPage.value - 1) * sessionsPageSize;
  const end = start + sessionsPageSize;
  return sessions.value.slice(start, end);
});

// 当前会话优先排序：当前会话在前，其余保持时间顺序
const orderedPaginatedSessions = computed(() => {
  const list = [...paginatedSessions.value];
  return list.sort((a, b) => {
    if (a.is_current && !b.is_current) return -1;
    if (!a.is_current && b.is_current) return 1;
    return 0;
  });
});

const visibleSessionsPages = computed(() => {
  const total = totalSessionsPages.value;
  const current = currentSessionsPage.value;
  const pages: number[] = [];

  if (total <= 5) {
    for (let i = 1; i <= total; i++) {
      pages.push(i);
    }
    return pages;
  }

  pages.push(1);
  if (current > 3) {
    pages.push(-1);
  }

  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);
  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  if (current < total - 2) {
    pages.push(-1);
  }
  pages.push(total);

  return pages;
});

const goToSessionsPage = (page: number) => {
  if (page < 1 || page > totalSessionsPages.value || page === -1) return;
  currentSessionsPage.value = page;
};

const formatTime = (timeStr: string) => {
  if (!timeStr) return "未知";
  try {
    const date = new Date(timeStr);
    return date.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return timeStr;
  }
};

const parseUserAgent = (userAgent: string) => {
  if (!userAgent) return "未知设备";
  // 简单的User-Agent解析（用于会话管理，登录历史使用后端解析的数据）
  if (userAgent.includes("Chrome")) return "Chrome 浏览器";
  if (userAgent.includes("Firefox")) return "Firefox 浏览器";
  if (userAgent.includes("Safari") && !userAgent.includes("Chrome")) return "Safari 浏览器";
  if (userAgent.includes("Edge")) return "Edge 浏览器";
  if (userAgent.includes("Mobile")) return "移动设备";
  return "未知设备";
};

const formatLoginMethod = (method: string) => {
  const methodMap: Record<string, string> = {
    email: "邮箱登录",
    google: "Google 登录",
    github: "GitHub 登录",
  };
  return methodMap[method] || method || "未知";
};

const openAvatarModal = () => {
  avatarZoom.value = 1.1;
  avatarPreviewUrl.value = userStore.user?.avatar || null;
  avatarImage.value = null;
  showAvatarModal.value = true;
  lockBodyScroll();
  // 标记用户已经知道头像可点击编辑
  try {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("settings_avatar_hint_seen", "1");
    }
  } catch {
    // ignore
  }
  showAvatarHint.value = false;
};

const handleAvatarFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (!target.files || !target.files[0]) return;
  const file = target.files[0];

  if (!file.type.startsWith("image/")) {
    showToast("error", "格式不支持", "请上传 JPG 或 PNG 图片");
    return;
  }
  if (file.size > 2 * 1024 * 1024) {
    showToast("error", "图片过大", "头像图片大小不能超过 2MB");
    return;
  }

  const reader = new FileReader();
  reader.onload = () => {
    const result = reader.result as string;
    avatarPreviewUrl.value = result;
    const img = new Image();
    img.onload = () => {
      avatarImage.value = img;
      avatarZoom.value = 1.1;
    };
    img.src = result;
  };
  reader.readAsDataURL(file);
};

const startEditName = () => {
  editingName.value = true;
  nameInput.value = userStore.user?.name || "";
};

const cancelEditName = () => {
  editingName.value = false;
  nameInput.value = userStore.user?.name || "";
};

const saveName = async () => {
  const value = nameInput.value.trim();
  if (!value) {
    showToast("error", "保存失败", "昵称不能为空");
    return;
  }
  if (value.length > 50) {
    showToast("error", "保存失败", "昵称长度不能超过 50 个字符");
    return;
  }

  savingName.value = true;
  try {
    const res = await updateProfile({ name: value });
    if (userStore.user) {
      const updatedUser = { ...userStore.user, name: res.name };
      userStore.user = updatedUser as any;
      const storage = localStorage.getItem("auth_token") ? localStorage : sessionStorage;
      storage.setItem("user", JSON.stringify(updatedUser));
    }
    showToast("success", "已保存", res.message || "昵称已更新");
    editingName.value = false;
  } catch (err: any) {
    showToast("error", "保存失败", err.message || "保存昵称失败，请稍后重试");
  } finally {
    savingName.value = false;
  }
};

const handleSaveAvatar = async () => {
  if (!avatarPreviewUrl.value) {
    showToast("error", "未选择图片", "请先选择一张头像图片");
    return;
  }

  // 如果用户还没选新图，沿用当前头像，无需请求
  if (!avatarImage.value) {
    showAvatarModal.value = false;
    unlockBodyScroll();
    return;
  }

  const img = avatarImage.value;
  const size = 512;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    showToast("error", "错误", "浏览器不支持头像裁剪");
    return;
  }

  // 居中裁剪：以图片中心为基准放大/缩小后绘制到正方形画布
  ctx.save();
  ctx.fillStyle = "#f3f4f6";
  ctx.fillRect(0, 0, size, size);
  ctx.translate(size / 2, size / 2);
  const scale = avatarZoom.value;
  ctx.scale(scale, scale);
  ctx.drawImage(img, -img.width / 2, -img.height / 2);
  ctx.restore();

  avatarUploading.value = true;
  try {
    const blob: Blob = await new Promise((resolve, reject) => {
      canvas.toBlob((b) => {
        if (!b) {
          reject(new Error("生成头像失败"));
        } else {
          resolve(b);
        }
      }, "image/png", 0.92);
    });

    const file = new File([blob], "avatar.png", { type: "image/png" });
    const result = await uploadAvatar(file);

    if (userStore.user) {
      const updatedUser = {
        ...userStore.user,
        avatar: result.avatar,
      };
      userStore.user = updatedUser as any;
      const storage = localStorage.getItem("auth_token") ? localStorage : sessionStorage;
      storage.setItem("user", JSON.stringify(updatedUser));
    }

    showToast("success", "头像已更新", result.message || "头像已更新");
    showAvatarModal.value = false;
  } catch (err: any) {
    showToast("error", "上传失败", err.message || "上传头像失败，请稍后重试");
  } finally {
    avatarUploading.value = false;
    showAvatarModal.value = false;
    unlockBodyScroll();
  }
};

const formatFailureReason = (reason: string) => {
  const reasonMap: Record<string, string> = {
    captcha_invalid_or_expired: "验证码无效或已过期",
    account_temporarily_locked: "账户已暂时锁定",
    user_not_found: "用户不存在",
    invalid_password: "密码错误",
    rate_limit_exceeded: "请求过于频繁",
  };
  return reasonMap[reason] || reason || "未知原因";
};

const handleChangePassword = async () => {
  changePasswordError.value = "";

  if (!isEmailVerified.value) {
    changePasswordError.value = "邮箱未验证：请先完成邮箱验证后再修改密码";
    showToast("warning", "操作被限制", changePasswordError.value);
    return;
  }
  
  if (!changePasswordData.value.currentPassword) {
    changePasswordError.value = "请输入当前密码";
    return;
  }
  
  if (!changePasswordData.value.newPassword) {
    changePasswordError.value = "请输入新密码";
    return;
  }
  
  if (changePasswordData.value.newPassword.length < 8) {
    changePasswordError.value = "新密码至少需要8个字符";
    return;
  }
  
  if (changePasswordData.value.newPassword !== changePasswordData.value.confirmPassword) {
    changePasswordError.value = "两次输入的密码不一致";
    return;
  }
  
  changingPassword.value = true;
  try {
    const result = await changePassword({
      current_password: changePasswordData.value.currentPassword,
      new_password: changePasswordData.value.newPassword,
    });
    showToast("success", "修改成功", result.message);
    showChangePasswordModal.value = false;
    changePasswordData.value = {
      currentPassword: "",
      newPassword: "",
      confirmPassword: "",
    };
    // 密码修改后会清除所有会话，需要重新登录
    setTimeout(() => {
      showToast("info", "请重新登录", "密码已修改，所有设备已登出，请重新登录");
      userStore.logout();
      router.push("/auth");
    }, 2000);
  } catch (err: any) {
    changePasswordError.value = err.message || "修改失败，请稍后重试";
    showToast("error", "修改失败", err.message);
  } finally {
    changingPassword.value = false;
  }
};

const loadLoginHistory = async () => {
  loadingLoginHistory.value = true;
  currentLoginHistoryPage.value = 1; // 重置到第一页
  try {
    loginHistory.value = await getLoginHistory(50); // 获取更多记录用于分页
    // 用最近一次成功登录的审计记录作为“当前登录方式”展示来源
    const latestSuccess = loginHistory.value.find((x) => x && x.success);
    if (latestSuccess && (latestSuccess.login_method === "email" || latestSuccess.login_method === "google" || latestSuccess.login_method === "github")) {
      currentLoginMethod.value = latestSuccess.login_method;
    } else {
      currentLoginMethod.value = "email";
    }
  } catch (err: any) {
    showToast("error", "加载失败", err.message);
  } finally {
    loadingLoginHistory.value = false;
  }
};

// 计算分页后的登录历史
const paginatedLoginHistory = computed(() => {
  const start = (currentLoginHistoryPage.value - 1) * loginHistoryPageSize;
  const end = start + loginHistoryPageSize;
  return loginHistory.value.slice(start, end);
});

// 计算总页数
const totalLoginHistoryPages = computed(() => {
  return Math.ceil(loginHistory.value.length / loginHistoryPageSize);
});

// 计算可见的页码
const visibleLoginHistoryPages = computed(() => {
  const total = totalLoginHistoryPages.value;
  const current = currentLoginHistoryPage.value;
  const pages: number[] = [];
  
  if (total <= 7) {
    // 如果总页数少于等于7，显示所有页码
    for (let i = 1; i <= total; i++) {
      pages.push(i);
    }
  } else {
    // 否则显示当前页附近的页码
    if (current <= 4) {
      for (let i = 1; i <= 5; i++) {
        pages.push(i);
      }
      pages.push(-1); // 省略号
      pages.push(total);
    } else if (current >= total - 3) {
      pages.push(1);
      pages.push(-1); // 省略号
      for (let i = total - 4; i <= total; i++) {
        pages.push(i);
      }
    } else {
      pages.push(1);
      pages.push(-1); // 省略号
      for (let i = current - 1; i <= current + 1; i++) {
        pages.push(i);
      }
      pages.push(-1); // 省略号
      pages.push(total);
    }
  }
  
  return pages;
});

// 跳转到指定页
const goToLoginHistoryPage = (page: number) => {
  if (page < 1 || page > totalLoginHistoryPages.value || page === -1) {
    return;
  }
  currentLoginHistoryPage.value = page;
  // 滚动到顶部
  const modalBody = document.querySelector('.modal-body');
  if (modalBody) {
    modalBody.scrollTop = 0;
  }
};

const loadSessions = async () => {
  loadingSessions.value = true;
  try {
    sessions.value = await getSessions();
    currentSessionsPage.value = 1;
  } catch (err: any) {
    showToast("error", "加载失败", err.message);
  } finally {
    loadingSessions.value = false;
  }
};

const handleRevokeSession = async (sessionIdOrTokenPrefix: string) => {
  revokingSession.value = sessionIdOrTokenPrefix;
  try {
    await revokeSession(sessionIdOrTokenPrefix);
    showToast("success", "撤销成功", "会话已撤销");
    await loadSessions();
  } catch (err: any) {
    showToast("error", "撤销失败", err.message);
  } finally {
    revokingSession.value = null;
  }
};

const handleRevokeAllSessions = async () => {
  if (!confirm("确定要撤销所有会话吗？这将登出所有设备，包括当前设备。")) {
    return;
  }
  
  revokingAllSessions.value = true;
  try {
    await revokeAllSessions();
    showToast("success", "撤销成功", "所有会话已撤销");
    showSessionsModal.value = false;
    // 撤销所有会话后需要重新登录
    setTimeout(() => {
      userStore.logout();
      router.push("/auth");
    }, 2000);
  } catch (err: any) {
    showToast("error", "撤销失败", err.message);
  } finally {
    revokingAllSessions.value = false;
  }
};

const handleResendVerification = async () => {
  if (!userStore.user?.email) {
    showToast("error", "错误", "无法获取邮箱地址");
    return;
  }
  
  resendingVerification.value = true;
  try {
    const result = await sendEmailVerification({ email: userStore.user.email });
    showToast("success", "发送成功", result.message);
    if (result.verification_url) {
      showToast("info", "开发环境提示", `验证链接：${result.verification_url}`);
    }
  } catch (err: any) {
    showToast("error", "发送失败", err.message);
  } finally {
    resendingVerification.value = false;
  }
};

// 监听模态框打开，加载数据
watch(showLoginHistoryModal, (visible) => {
  if (visible) {
    lockBodyScroll();
    loadLoginHistory();
  } else {
    unlockBodyScroll();
  }
});

watch(showSessionsModal, (visible) => {
  if (visible) {
    lockBodyScroll();
    loadSessions();
  } else {
    unlockBodyScroll();
  }
});

// 2FA / 社交绑定 / 密码泄露检测相关函数已移除，仅保留登录历史等通用安全信息

onMounted(() => {
  // 初始化时拉取一次登录历史（轻量：用于正确展示“登录方式”卡片）
  loadLoginHistory();
  initAvatarHint();
});
</script>

<style scoped>
.settings {
  width: 100%;
  padding: 0;
  margin: 0;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0e7ff 50%, #f3e8ff 100%);
  display: block;
  min-height: 100%;
}

.settings-container {
  width: 100%;
  padding: 60px 48px;
  display: flex;
  flex-direction: column;
  gap: 40px;
  max-width: 100%;
  box-sizing: border-box;
}

.settings-header {
  text-align: center;
  margin-bottom: 8px;
}

.settings-title {
  font-size: 48px;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 12px 0;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.settings-subtitle {
  font-size: 18px;
  color: #64748b;
  margin: 0;
  font-weight: 400;
}

.settings-section {
  padding: 48px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  width: 100%;
  transition: all 0.3s ease;
}

.settings-section-combined {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.settings-subsection {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-subsection + .settings-subsection {
  border-top: 1px solid rgba(226, 232, 240, 0.7);
  padding-top: 28px;
}

.subsection-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 8px;
}

.subsection-header .settings-section-title {
  font-size: 22px;
  text-align: left;
}

.subsection-header .settings-section-desc {
  text-align: left;
  font-size: 14px;
}

.subsection-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  flex-shrink: 0;
}

.settings-section:hover {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 40px;
  padding-bottom: 32px;
  border-bottom: 2px solid #f1f5f9;
  text-align: center;
}

.section-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  flex-shrink: 0;
}

/* 统一图标尺寸与线条风格 */
.subsection-icon svg,
.section-icon svg,
.setting-icon svg,
.email-verified-badge svg,
.email-unverified-badge svg,
.user-avatar-placeholder svg,
.avatar-edit-icon svg,
.name-edit-icon svg,
.modal-close svg,
.avatar-preview-placeholder svg,
.password-toggle svg,
.empty-state-icon svg,
.history-item-icon svg,
.session-item-icon svg,
.pagination-btn svg,
.status-badge svg,
.breach-result-icon svg {
  width: 20px;
  height: 20px;
  stroke-width: 2;
}

.account-icon {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  color: #6366f1;
}

.security-icon {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #ef4444;
}

.settings-section-title {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 6px 0;
  letter-spacing: -0.01em;
  text-align: center;
}

.settings-section-desc {
  font-size: 15px;
  color: #64748b;
  margin: 0;
  font-weight: 400;
  text-align: center;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 32px;
}

.setting-card {
  padding: 40px 32px;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  border-radius: 20px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 220px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
}

.setting-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.setting-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
  border-color: #cbd5e1;
}

.setting-card:hover::before {
  opacity: 1;
}

.security-card {
  background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
}

.security-card::before {
  background: linear-gradient(90deg, #ef4444 0%, #dc2626 50%, #b91c1c 100%);
}

.card-icon-wrapper {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.setting-card-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  margin-bottom: 16px;
  text-align: center;
}

.setting-card-header-main {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
}

.setting-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
  flex-shrink: 0;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transition: all 0.3s ease;
  border: 4px solid #ffffff;
}

.setting-card:hover .setting-icon {
  transform: scale(1.05);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
}

.setting-icon svg {
  width: 40px;
  height: 40px;
}

.email-icon {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #3b82f6;
}

.user-icon {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  color: #6366f1;
}

.provider-icon {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #f59e0b;
}

.password-icon {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #ef4444;
}

.history-icon {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  color: #10b981;
}

.security-warning-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  margin-bottom: 20px;
  border-radius: 14px;
  background: linear-gradient(120deg, rgba(254, 243, 199, 0.9), rgba(253, 230, 138, 0.9));
  box-shadow: 0 10px 30px rgba(251, 191, 36, 0.3);
  border: 1px solid rgba(245, 158, 11, 0.35);
}

.security-warning-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #f97316;
  box-shadow: 0 0 0 4px rgba(248, 171, 75, 0.4);
  flex-shrink: 0;
}

.security-warning-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.security-warning-title {
  font-size: 14px;
  font-weight: 700;
  color: #92400e;
}

.security-warning-desc {
  font-size: 13px;
  color: #78350f;
  opacity: 0.9;
}

.security-warning-action {
  border: none;
  outline: none;
  border-radius: 999px;
  padding: 8px 14px;
  background: linear-gradient(135deg, #f97316, #ea580c);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 8px 18px rgba(234, 88, 12, 0.45);
  transition: all 0.2s ease;
  white-space: nowrap;
}

.security-warning-action:disabled {
  opacity: 0.7;
  cursor: default;
  box-shadow: none;
}

.security-warning-action:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(234, 88, 12, 0.6);
}

.security-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.security-status-badge-warning {
  background: rgba(254, 226, 226, 0.9);
  color: #b91c1c;
  box-shadow: 0 4px 14px rgba(248, 113, 113, 0.4);
}

.security-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #ef4444;
  box-shadow: 0 0 0 4px rgba(248, 113, 113, 0.3);
}

.setting-card-subtext {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

.session-icon {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  color: #6366f1;
}

.twofa-icon {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #3b82f6;
}

.social-icon {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #f59e0b;
}

.breach-icon {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #ef4444;
}

.setting-label {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.01em;
}

.email-verified-badge,
.email-unverified-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.email-verified-badge {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  color: #065f46;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
}

.email-verified-badge svg {
  width: 16px;
  height: 16px;
}

.email-unverified-badge {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #92400e;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.2);
}

.email-unverified-badge svg {
  width: 16px;
  height: 16px;
}

.setting-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  flex: 1;
  width: 100%;
}

.email-display,
.name-display {
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-card .setting-card-content {
  display: flex;
  justify-content: center;
}

.user-card .name-display {
  width: auto;
  margin: 0 auto;
}

.email-text,
.name-text {
  font-size: 16px;
  color: #334155;
  font-weight: 600;
  word-break: break-all;
  text-align: center;
}

.email-status-description {
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 13px;
  line-height: 1.5;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
  border: 1px solid transparent;
}

.email-status-description-verified {
  background: linear-gradient(120deg, #ecfdf5, #d1fae5);
  color: #047857;
  border-color: rgba(16, 185, 129, 0.4);
}

.email-status-description-unverified {
  background: linear-gradient(120deg, #fffbeb, #fef3c7);
  color: #92400e;
  border-color: rgba(251, 191, 36, 0.6);
}

/* 用户名卡片特殊样式 */
.avatar-inline-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #9ca3af;
  text-align: center;
  letter-spacing: 0.02em;
}

.user-avatar-wrapper {
  position: relative;
  cursor: pointer;
}

.user-avatar,
.user-avatar-placeholder {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.2);
  transition: all 0.3s ease;
  border: 4px solid #ffffff;
}

.setting-card:hover .user-avatar,
.setting-card:hover .user-avatar-placeholder {
  transform: scale(1.05);
  box-shadow: 0 12px 32px rgba(99, 102, 241, 0.3);
}

.user-avatar {
  overflow: hidden;
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-avatar-placeholder {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  color: #6366f1;
}

.user-avatar-placeholder svg {
  width: 40px;
  height: 40px;
}

.avatar-edit-icon {
  position: absolute;
  right: -2px;
  bottom: -2px;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  border: none;
  background: radial-gradient(circle at 0 0, #e0f2fe 0%, #6366f1 45%, #8b5cf6 100%);
  color: #f9fafb;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 10px 25px rgba(15, 23, 42, 0.38),
    0 0 0 1px rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}

.avatar-edit-icon svg {
  width: 16px;
  height: 16px;
}

.avatar-edit-icon:hover {
  transform: translateY(-1px) scale(1.02);
  box-shadow:
    0 14px 30px rgba(15, 23, 42, 0.45),
    0 0 0 1px rgba(191, 219, 254, 0.9);
}

.name-editable {
  flex-direction: column;
  gap: 10px;
}

.name-text-button {
  border: none;
  background: none;
  padding: 0;
  cursor: pointer;
  display: inline-block;
  position: relative;
}

.name-text-button .name-text {
  position: relative;
}

.name-text-button .name-text::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: -2px;
  height: 1px;
  background: linear-gradient(90deg, rgba(148, 163, 184, 0.4), transparent);
  opacity: 0;
  transition: opacity 0.15s ease;
}

.name-text-button:hover .name-text::after {
  opacity: 1;
}

.name-edit-icon {
  position: absolute;
  right: 18px;
  top: 50%;
  transform: translateY(-50%);
  width: 22px;
  height: 22px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eef2ff;
  color: #4f46e5;
}

.name-edit-icon svg {
  width: 14px;
  height: 14px;
}

.name-input {
  min-width: 200px;
  padding: 10px 16px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  font-size: 15px;
  box-shadow:
    0 10px 40px rgba(15, 23, 42, 0.12),
    0 0 0 1px rgba(255, 255, 255, 0.9) inset;
  outline: none;
  text-align: center;
  background: radial-gradient(circle at 0 0, rgba(248, 250, 252, 0.95), rgba(226, 232, 240, 0.95));
  color: #111827;
}

.name-input:focus {
  border-color: rgba(129, 140, 248, 0.9);
  box-shadow:
    0 12px 45px rgba(79, 70, 229, 0.23),
    0 0 0 1px rgba(191, 219, 254, 0.9);
}

.name-edit-actions {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 4px;
}

.name-save-btn,
.name-cancel-btn {
  border-radius: 999px;
  padding: 4px 14px;
  font-size: 12px;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.name-save-btn {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 60%, #ec4899 115%);
  color: #ffffff;
  box-shadow:
    0 8px 24px rgba(79, 70, 229, 0.45),
    0 0 0 1px rgba(255, 255, 255, 0.6);
}

.name-cancel-btn {
  background: rgba(249, 250, 251, 0.9);
  color: #4b5563;
  box-shadow:
    0 4px 16px rgba(15, 23, 42, 0.08),
    0 0 0 1px rgba(226, 232, 240, 0.9);
}

.name-text {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.01em;
  padding: 12px 40px 12px 24px; /* 右侧为铅笔留出空间 */
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  min-width: 180px;
  display: inline-block;
}

.email-text {
  font-size: 16px;
  font-weight: 600;
  color: #334155;
  padding: 12px 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  display: inline-block;
  max-width: 100%;
  word-break: break-all;
}

.provider-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 28px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  min-width: 140px;
  border: 2px solid transparent;
}

.setting-card:hover .provider-badge {
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

.provider-badge.provider-email {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  color: #4338ca;
}

.provider-badge.provider-google {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #991b1b;
}

.provider-badge.provider-github {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  color: #ffffff;
}

.settings-action-btn {
  padding: 12px 28px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  min-width: 160px;
}

.settings-action-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.5);
}

.settings-action-btn:active:not(:disabled) {
  transform: translateY(0);
}

.settings-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.settings-action-btn-secondary {
  background: linear-gradient(135deg, #f8fafc 0%, #e5e7eb 100%);
  color: #111827;
  box-shadow: 0 2px 8px rgba(148, 163, 184, 0.35);
  border: 1px solid rgba(148, 163, 184, 0.6);
  min-width: 0;
  padding-inline: 20px;
}

.settings-action-btn-secondary:hover:not(:disabled) {
  box-shadow: 0 4px 14px rgba(148, 163, 184, 0.55);
}

.settings-action-btn:hover:not(:disabled),
.auth-button:hover:not(:disabled),
.auth-button-danger-outlined:hover:not(:disabled),
.email-verification-btn:hover:not(:disabled),
.security-guide-primary:hover:not(:disabled),
.security-guide-secondary:hover:not(:disabled),
.dashboard-refresh-icon-btn:hover:not(:disabled) {
  filter: brightness(1.02);
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.14);
}

.settings-hint {
  font-size: 13px;
  color: #64748b;
  margin: 0;
  text-align: center;
  line-height: 1.6;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-content-large {
  max-width: 800px;
}

.modal-content-avatar {
  max-width: 760px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.modal-close svg {
  width: 20px;
  height: 20px;
}

.modal-body {
  padding: 32px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.avatar-modal-body {
  padding: 28px 32px 32px;
}

.avatar-editor-grid {
  display: grid;
  grid-template-columns: minmax(260px, 320px) minmax(260px, 1fr);
  gap: 32px;
  align-items: stretch;
}

.avatar-preview-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.avatar-preview-wrapper {
  width: 260px;
  height: 260px;
  border-radius: 24px;
  background: radial-gradient(circle at 0 0, #e0f2fe 0%, transparent 40%), radial-gradient(circle at 100% 100%, #e9d5ff 0%, transparent 40%), linear-gradient(135deg, #f8fafc 0%, #e5e7eb 100%);
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8), 0 10px 30px rgba(15, 23, 42, 0.18);
}

.avatar-preview-mask {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-preview-circle {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  overflow: hidden;
  position: relative;
  background: radial-gradient(circle at 30% 0%, #e0f2fe 0%, #c7d2fe 40%, #a5b4fc 100%);
  border: 4px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 12px 35px rgba(15, 23, 42, 0.35);
}

.avatar-preview-circle img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform-origin: center center;
  transition: transform 0.15s ease-out;
}

.avatar-preview-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(15, 23, 42, 0.7);
}

.avatar-preview-placeholder svg {
  width: 72px;
  height: 72px;
}

.avatar-helper-text {
  font-size: 13px;
  color: #64748b;
  text-align: center;
  margin: 0;
}

.avatar-control-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.avatar-upload-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 18px;
  border-radius: 999px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(99, 102, 241, 0.45);
  transition: all 0.2s ease;
  border: none;
  position: relative;
  overflow: hidden;
}

.avatar-upload-btn input[type="file"] {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.avatar-upload-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 28px rgba(99, 102, 241, 0.6);
}

.avatar-upload-btn:active {
  transform: translateY(0);
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
}

.avatar-upload-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #94a3b8;
}

.avatar-zoom-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar-zoom-label {
  font-size: 12px;
  color: #94a3b8;
}

.avatar-zoom-percentage {
  min-width: 48px;
  text-align: center;
  font-size: 12px;
  font-weight: 500;
  color: #0f172a;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.04);
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08);
}

.avatar-zoom-slider {
  flex: 1;
  appearance: none;
  height: 6px;
  border-radius: 999px;
  background: linear-gradient(90deg, #e5e7eb 0%, #6366f1 50%, #8b5cf6 100%);
  outline: none;
}

.avatar-zoom-slider::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #ffffff;
  border: 2px solid #6366f1;
  box-shadow: 0 0 0 4px rgba(129, 140, 248, 0.35);
  cursor: pointer;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.avatar-zoom-slider::-webkit-slider-thumb:hover {
  box-shadow: 0 0 0 6px rgba(129, 140, 248, 0.45);
  transform: scale(1.03);
}

.avatar-zoom-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #ffffff;
  border: 2px solid #6366f1;
  box-shadow: 0 0 0 4px rgba(129, 140, 248, 0.35);
  cursor: pointer;
}

.avatar-actions {
  margin-top: 4px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #475569;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 15px;
  transition: all 0.2s ease;
  background: #ffffff;
}

.form-input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.password-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.password-toggle {
  position: absolute;
  right: 12px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  border-radius: 4px;
}

.password-toggle:hover {
  color: #1e293b;
  background: #f1f5f9;
}

.password-toggle svg {
  width: 18px;
  height: 18px;
}

.field-error {
  color: #ef4444;
  font-size: 14px;
  margin-top: 8px;
}

.auth-button {
  width: 100%;
  padding: 14px 28px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.auth-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3);
}

.auth-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-button-danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.auth-button-danger:hover:not(:disabled) {
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.3);
}

/* 会话：撤销所有会话按钮，默认次要色，hover 时变成实体红色 */
.auth-button-danger-outlined {
  background: transparent;
  color: #dc2626;
  border-color: rgba(248, 113, 113, 0.7);
  box-shadow: none;
}

.auth-button-danger-outlined:hover:not(:disabled) {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  box-shadow: 0 8px 18px rgba(248, 113, 113, 0.35);
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-spinner-small {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 16px;
}

.loading-state .loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #6366f1;
}

.loading-state p {
  color: #64748b;
  font-size: 15px;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #64748b;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.empty-state-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  color: #94a3b8;
  margin-bottom: 8px;
}

.empty-state-icon svg {
  width: 32px;
  height: 32px;
}

.empty-state p {
  font-size: 15px;
  font-weight: 500;
  color: #64748b;
  margin: 0;
}

.history-list,
.sessions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 4px;
  margin: -4px;
  /* 移除固定高度，让内容自适应 */
  min-height: 0;
}

.history-item,
.session-item {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 16px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.history-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, #e2e8f0 0%, #cbd5e1 100%);
  transition: width 0.3s ease;
}

.history-item:hover,
.session-item:hover {
  background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
  border-color: rgba(203, 213, 225, 0.6);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08), 0 2px 6px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.history-item-success {
  border-left-color: transparent;
}

.history-item-success::before {
  background: linear-gradient(180deg, #10b981 0%, #059669 100%);
  width: 4px;
}

.history-item-failed {
  border-left-color: transparent;
}

.history-item-failed::before {
  background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%);
  width: 4px;
}

.session-item-current {
  border-left: 4px solid #6366f1;
  background: #eef2ff;
}

.history-item-icon,
.session-item-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 12px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.8);
  transition: all 0.3s ease;
}

.history-item:hover .history-item-icon,
.session-item:hover .session-item-icon {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.history-item-success .history-item-icon {
  color: #10b981;
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
}

.history-item-failed .history-item-icon {
  color: #ef4444;
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
}

.session-item-icon {
  color: #6366f1;
}

.history-item-icon svg,
.session-item-icon svg {
  width: 24px;
  height: 24px;
}

.history-item-content,
.session-item-content {
  flex: 1;
  min-width: 0;
}

.history-item-header,
.session-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  gap: 12px;
}

.history-item-status,
.session-item-token {
  font-weight: 600;
  color: #0f172a;
  font-size: 15px;
  letter-spacing: -0.01em;
}

.session-item-token {
  font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
  font-size: 13px;
}

.history-item-time {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
  white-space: nowrap;
}

.history-item-primary-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  font-size: 13px;
  color: #0f172a;
}

.history-item-device {
  font-weight: 600;
}

.history-item-ip {
  font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
  font-size: 12px;
  color: #4b5563;
}

.history-item-separator {
  color: #9ca3af;
}

.session-item-badge {
  padding: 4px 8px;
  background: #6366f1;
  color: #ffffff;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.history-item-details,
.session-item-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 4px;
}

@media (max-width: 768px) {
  .history-item-details,
  .session-item-details {
    grid-template-columns: 1fr;
  }
  
  .history-item,
  .session-item {
    padding: 16px;
    gap: 16px;
  }
  
  .history-item-icon,
  .session-item-icon {
    width: 40px;
    height: 40px;
  }
  
  .pagination-controls {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .pagination-info {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
}

@media (max-width: 768px) {
  .avatar-editor-grid {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .avatar-preview-wrapper {
    width: 220px;
    height: 220px;
  }

  .avatar-preview-circle {
    width: 180px;
    height: 180px;
  }
}

.history-item-detail,
.session-item-detail {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px;
  background: rgba(248, 250, 252, 0.6);
  border-radius: 10px;
  border: 1px solid rgba(226, 232, 240, 0.5);
  transition: all 0.2s ease;
}

.history-item-detail-secondary {
  font-size: 12px;
  color: #6b7280;
}

.history-item-detail:hover,
.session-item-detail:hover {
  background: rgba(241, 245, 249, 0.8);
  border-color: rgba(203, 213, 225, 0.7);
}

.error-text {
  color: #dc2626;
  font-weight: 600;
}

.detail-label {
  color: #64748b;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.detail-value {
  color: #0f172a;
  font-weight: 500;
  font-size: 14px;
  word-break: break-word;
  line-height: 1.5;
}

.session-item-actions {
  flex-shrink: 0;
}

/* 分页控件样式 */
.pagination-container {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(226, 232, 240, 0.8);
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
}

.pagination-info {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(226, 232, 240, 0.8);
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 10px;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.pagination-btn:hover:not(.pagination-btn-disabled) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-color: rgba(203, 213, 225, 0.8);
  color: #0f172a;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.pagination-btn:active:not(.pagination-btn-disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.pagination-btn-disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: #f1f5f9;
}

.pagination-btn svg {
  width: 18px;
  height: 18px;
}

.pagination-pages {
  display: flex;
  gap: 4px;
  align-items: center;
}

.pagination-page-btn {
  min-width: 40px;
  height: 40px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(226, 232, 240, 0.8);
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 10px;
  color: #475569;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.pagination-page-btn:hover:not(.pagination-page-btn-disabled):not(.pagination-page-btn-ellipsis) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-color: rgba(203, 213, 225, 0.8);
  color: #0f172a;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.pagination-page-btn-active {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  border-color: #6366f1;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3), 0 1px 3px rgba(99, 102, 241, 0.2);
  font-weight: 600;
}

.pagination-page-btn-active:hover {
  background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
  border-color: #4f46e5;
  color: #ffffff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4), 0 2px 6px rgba(99, 102, 241, 0.3);
}

.pagination-page-btn-ellipsis {
  border: none;
  background: transparent;
  cursor: default;
  box-shadow: none;
  color: #94a3b8;
  min-width: auto;
  padding: 0 8px;
}

.pagination-page-btn-ellipsis:hover {
  background: transparent;
  transform: none;
  box-shadow: none;
}

.session-revoke-btn {
  padding: 6px 12px;
  background: #ef4444;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.session-revoke-btn:hover:not(:disabled) {
  background: #dc2626;
  transform: translateY(-1px);
}

.session-revoke-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sessions-actions {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e2e8f0;
}

/* 模态框动画 */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.9);
  opacity: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .settings-container {
    padding: 32px 20px;
    gap: 32px;
  }

  .settings-title {
    font-size: 36px;
  }

  .settings-subtitle {
    font-size: 16px;
  }

  .settings-section {
    padding: 32px 24px;
    border-radius: 24px;
  }

  .section-header {
    margin-bottom: 32px;
    padding-bottom: 24px;
  }

  .section-icon {
    width: 44px;
    height: 44px;
  }

  .section-icon svg {
    width: 22px;
    height: 22px;
  }

  .settings-section-title {
    font-size: 22px;
  }

  .settings-grid {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .setting-card {
    padding: 32px 24px;
    min-height: 200px;
  }

  .setting-icon {
    width: 56px;
    height: 56px;
  }

  .setting-icon svg {
    width: 28px;
    height: 28px;
  }

  .setting-icon {
    width: 64px;
    height: 64px;
  }

  .setting-icon svg {
    width: 32px;
    height: 32px;
  }

  .user-avatar,
  .user-avatar-placeholder {
    width: 64px;
    height: 64px;
  }

  .user-card .setting-card-content {
    flex-direction: column;
    align-items: center;
    gap: 16px;
  }

  .name-display.name-editable {
    width: 100%;
    justify-content: center;
  }

  .security-card .setting-card-content {
    flex-direction: column;
    align-items: stretch;
  }

  .security-card .settings-action-btn,
  .security-card .settings-action-btn-secondary,
  .security-card .auth-button-danger-outlined {
    width: 100%;
  }

  .user-avatar-placeholder svg {
    width: 32px;
    height: 32px;
  }

  .name-text,
  .email-text {
    font-size: 15px;
    min-width: 140px;
    padding: 10px 18px;
  }

  .provider-badge {
    font-size: 14px;
    padding: 12px 24px;
    min-width: 120px;
  }
}

@media (min-width: 1200px) {
  .settings-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* 2FA相关样式 */
.twofa-status-enabled {
  text-align: center;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: 12px;
  font-weight: 600;
  margin-bottom: 16px;
}

.status-badge.success {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  color: #065f46;
}

.status-badge svg {
  width: 20px;
  height: 20px;
}

.status-description {
  color: #64748b;
  line-height: 1.7;
  margin-bottom: 20px;
  text-align: center;
}

.qr-code-section {
  text-align: center;
}

.qr-code-placeholder {
  background: #f8fafc;
  border: 2px dashed #e2e8f0;
  border-radius: 12px;
  padding: 40px 20px;
  margin: 16px 0;
  word-break: break-all;
}

.backup-codes-display {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  margin-top: 16px;
}

.backup-codes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.backup-code-item {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  font-family: monospace;
  font-weight: 600;
  font-size: 14px;
  color: #1e293b;
}

/* 社交账号绑定相关样式 */
.bindings-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 20px;
}

.binding-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.binding-item:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.binding-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
}

.binding-provider-badge {
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  min-width: 80px;
  text-align: center;
}

.binding-provider-badge.provider-google {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #991b1b;
}

.binding-provider-badge.provider-github {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  color: #ffffff;
}

.binding-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.binding-detail {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.binding-detail .detail-label {
  color: #64748b;
  font-weight: 500;
}

.binding-detail .detail-value {
  color: #1e293b;
}

/* 密码泄露检测相关样式 */
.breach-result {
  margin-top: 24px;
  padding: 20px;
  border-radius: 12px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  background: #f0fdf4;
  border: 2px solid #86efac;
}

.breach-result-danger {
  background: #fef2f2;
  border-color: #fca5a5;
}

.breach-result-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #ffffff;
}

.breach-result-danger .breach-result-icon {
  color: #ef4444;
}

.breach-result:not(.breach-result-danger) .breach-result-icon {
  color: #10b981;
}

.breach-result-icon svg {
  width: 24px;
  height: 24px;
}

.breach-result-content {
  flex: 1;
}

.breach-result-message {
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.breach-result-danger .breach-result-message {
  color: #991b1b;
}

.breach-result-count {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.breach-result-danger .breach-result-count {
  color: #92400e;
}
</style>
