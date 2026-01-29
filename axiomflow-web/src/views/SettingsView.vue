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
                  class="settings-action-btn ripple"
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
                <button
                  type="button"
                  class="user-avatar-wrapper"
                  @click="(e) => openAvatarModalFromTrigger(e)"
                  ref="avatarTriggerRef"
                  aria-label="编辑头像"
                >
                  <div class="user-avatar" v-if="userStore.user?.avatar">
                    <img :src="userStore.user.avatar" :alt="userStore.user?.name || '用户头像'" />
                  </div>
                  <div class="user-avatar-placeholder" v-else>
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <span class="avatar-edit-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 20h9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L10 16l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </span>
                </button>
              </div>
              <div class="setting-card-header">
                <span class="setting-label">用户名</span>
              </div>
              <div class="setting-card-content">
                <div class="name-display name-editable">
                  <Transition name="fade-slide" mode="out-in">
                    <div :key="editingName ? 'edit' : 'view'" class="name-edit-pane">
                      <template v-if="editingName">
                        <input
                          ref="nameInputRef"
                          v-model="nameInput"
                          class="name-input"
                          :class="{ 'input-error': !!nameError, 'input-valid': nameTouched && !nameError && nameInput.trim().length > 0 }"
                          type="text"
                          maxlength="50"
                          placeholder="请输入昵称"
                          @keyup.enter="saveName"
                          @keyup.esc="cancelEditName"
                          @input="validateNameLive"
                          @blur="onNameBlur"
                          :aria-invalid="nameError ? 'true' : 'false'"
                          :aria-describedby="nameError ? 'name-error' : undefined"
                        />
                        <Transition name="field-pop">
                          <div v-if="nameError" id="name-error" class="field-error" role="alert">{{ nameError }}</div>
                        </Transition>
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
                          ref="nameTriggerRef"
                          aria-label="编辑昵称"
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
                  </Transition>
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
            class="app-alert app-alert--warning"
            role="status"
            aria-live="polite"
          >
            <div class="app-alert-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="22,6 12,13 2,6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="app-alert-content">
              <p class="app-alert-title">邮箱尚未验证</p>
              <p class="app-alert-message">
                为了保障账户安全，请先完成邮箱验证，部分安全操作在验证前将被限制。
              </p>
              <div class="app-alert-actions">
                <span
                  class="restricted-help sec-tooltip-trigger"
                  tabindex="0"
                  role="button"
                  aria-label="为何受限？"
                  aria-describedby="security-warning-tooltip"
                >
                  为什么？
                  <span id="security-warning-tooltip" class="restricted-tooltip sec-tooltip" role="tooltip">
                    {{ emailRestrictionMessage }}
                  </span>
                </span>
                <button
                  type="button"
                  class="settings-action-btn"
                  @click="handleResendVerification"
                  :disabled="resendingVerification"
                >
                  <span v-if="resendingVerification" class="loading-spinner-small"></span>
                  {{ resendingVerification ? "发送中..." : "重新发送验证邮件" }}
                </button>
              </div>
            </div>
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
                <div class="restricted-action">
                  <button
                    class="settings-action-btn ripple"
                    @click="(e) => openChangePasswordModalFromTrigger(e)"
                    :disabled="!canChangePassword || !isEmailVerified"
                    ref="changePasswordTriggerRef"
                    :aria-describedby="(!isEmailVerified && canChangePassword) ? 'email-restrict-tip-password' : undefined"
                  >
                    修改密码
                  </button>
                  <span
                    v-if="!isEmailVerified && canChangePassword"
                    class="restricted-help sec-tooltip-trigger"
                    tabindex="0"
                    role="button"
                    aria-label="为什么修改密码被限制？"
                    aria-describedby="email-restrict-tip-password"
                  >
                    为什么？
                    <span id="email-restrict-tip-password" class="restricted-tooltip sec-tooltip" role="tooltip">
                      {{ emailRestrictionMessage }}
                    </span>
                  </span>
                </div>
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
                <div class="restricted-action">
                  <button
                    class="settings-action-btn ripple"
                    @click="(e) => openLoginHistoryModalFromTrigger(e)"
                    :disabled="!isEmailVerified"
                    ref="loginHistoryTriggerRef"
                    :aria-describedby="!isEmailVerified ? 'email-restrict-tip-history' : undefined"
                  >
                    查看登录历史
                  </button>
                  <span
                    v-if="!isEmailVerified"
                    class="restricted-help sec-tooltip-trigger"
                    tabindex="0"
                    role="button"
                    aria-label="为什么登录历史查看被限制？"
                    aria-describedby="email-restrict-tip-history"
                  >
                    为什么？
                    <span id="email-restrict-tip-history" class="restricted-tooltip sec-tooltip" role="tooltip">
                      {{ emailRestrictionMessage }}
                    </span>
                  </span>
                </div>
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
                    class="security-status-badge"
                    :class="sessionBadgeVariant === 'warning' ? 'security-status-badge-warning' : 'security-status-badge-neutral'"
                  >
                    <span
                      class="security-status-dot"
                      :class="sessionBadgeVariant === 'warning' ? 'security-status-dot-warning' : 'security-status-dot-neutral'"
                    ></span>
                    {{ sessionBadgeLabel }}
                  </span>
                </div>
              </div>
              <div class="setting-card-content">
                <div class="restricted-action">
                  <button
                    class="settings-action-btn ripple"
                    @click="(e) => openSessionsModalFromTrigger(e)"
                    :disabled="!isEmailVerified"
                    ref="sessionsTriggerRef"
                    :aria-describedby="!isEmailVerified ? 'email-restrict-tip-sessions' : undefined"
                  >
                    管理会话
                  </button>
                  <span
                    v-if="!isEmailVerified"
                    class="restricted-help sec-tooltip-trigger"
                    tabindex="0"
                    role="button"
                    aria-label="为什么会话管理被限制？"
                    aria-describedby="email-restrict-tip-sessions"
                  >
                    为什么？
                    <span id="email-restrict-tip-sessions" class="restricted-tooltip sec-tooltip" role="tooltip">
                      {{ emailRestrictionMessage }}
                    </span>
                  </span>
                </div>
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
          @keyup.esc.stop.prevent="showChangePasswordModal = false"
          tabindex="-1"
        >
          <div class="modal-content glass-card modal-content--sm">
            <div class="modal-header">
              <div class="modal-header-text">
                <h2 id="change-password-title" ref="changePasswordTitleRef" tabindex="-1">修改密码</h2>
                <p class="modal-subtitle">定期更新密码，提升账户安全。</p>
              </div>
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
                    ref="currentPasswordInputRef"
                    id="current-password"
                    v-model="changePasswordData.currentPassword"
                    :type="showCurrentPassword ? 'text' : 'password'"
                    class="form-input"
                    :class="{
                      'input-error': changePasswordTouched.current && !!changePasswordFieldError.current,
                      'input-valid': changePasswordTouched.current && !changePasswordFieldError.current && !!changePasswordData.currentPassword
                    }"
                    placeholder="请输入当前密码"
                    autocomplete="current-password"
                    aria-required="true"
                    @keyup.enter="handleChangePassword"
                    @input="validateChangePasswordLive"
                    @blur="() => (changePasswordTouched.current = true, validateChangePasswordLive())"
                  />
                  <button
                    type="button"
                    class="password-toggle"
                    @click="showCurrentPassword = !showCurrentPassword"
                    aria-label="切换当前密码可见性"
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
                    :class="{
                      'input-error': changePasswordTouched.new && !!changePasswordFieldError.new,
                      'input-valid': changePasswordTouched.new && !changePasswordFieldError.new && !!changePasswordData.newPassword
                    }"
                    placeholder="请输入新密码（至少8位）"
                    autocomplete="new-password"
                    aria-required="true"
                    minlength="8"
                    @keyup.enter="handleChangePassword"
                    @input="validateChangePasswordLive"
                    @blur="() => (changePasswordTouched.new = true, validateChangePasswordLive())"
                  />
                  <button
                    type="button"
                    class="password-toggle"
                    @click="showNewPassword = !showNewPassword"
                    aria-label="切换新密码可见性"
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
                    :class="{
                      'input-error': changePasswordTouched.confirm && !!changePasswordFieldError.confirm,
                      'input-valid': changePasswordTouched.confirm && !changePasswordFieldError.confirm && !!changePasswordData.confirmPassword
                    }"
                    placeholder="请再次输入新密码"
                    autocomplete="new-password"
                    aria-required="true"
                    @keyup.enter="handleChangePassword"
                    @input="validateChangePasswordLive"
                    @blur="() => (changePasswordTouched.confirm = true, validateChangePasswordLive())"
                  />
                  <button
                    type="button"
                    class="password-toggle"
                    @click="showConfirmPassword = !showConfirmPassword"
                    aria-label="切换确认密码可见性"
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
              <Transition name="field-pop">
                <div v-if="changePasswordError" class="field-error" role="alert">{{ changePasswordError }}</div>
              </Transition>
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
          <div class="modal-content glass-card modal-content--lg">
            <div class="modal-header">
              <div class="modal-header-text">
                <h2 id="login-history-title" ref="loginHistoryTitleRef" tabindex="-1">登录历史</h2>
                <p class="modal-subtitle">查看最近的登录记录，发现异常可及时处理。</p>
              </div>
              <div class="modal-header-right">
                <span class="modal-updated-at" aria-live="polite">{{ loginHistoryUpdatedLabel }}</span>
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
            </div>
            <div class="modal-body">
              <p class="modal-tip-pill sec-pill sec-pill--warning sec-pill--one-line">
                支持筛选与搜索，建议定期回顾异常登录。
              </p>
              <div class="modal-toolbar">
                <div class="modal-toolbar-left">
                  <div class="filter-pills" role="tablist" aria-label="登录历史筛选">
                    <button
                      class="filter-pill"
                      :class="{ 'filter-pill-active': loginHistoryFilter === 'all' }"
                      type="button"
                      @click="loginHistoryFilter = 'all'"
                    >
                      全部
                    </button>
                    <button
                      class="filter-pill"
                      :class="{ 'filter-pill-active': loginHistoryFilter === 'failed' }"
                      type="button"
                      @click="loginHistoryFilter = 'failed'"
                    >
                      仅失败
                    </button>
                    <button
                      class="filter-pill"
                      :class="{ 'filter-pill-active': loginHistoryFilter === '7d' }"
                      type="button"
                      @click="loginHistoryFilter = '7d'"
                    >
                      近 7 天
                    </button>
                  </div>
                </div>
                <div class="modal-toolbar-right">
                  <div class="search-input">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                      <circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="2"/>
                      <path d="M20 20l-3.5-3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    <input
                      v-model="loginHistorySearch"
                      type="text"
                      placeholder="搜索设备 / IP"
                      aria-label="搜索设备或IP"
                    />
                    <button
                      v-if="loginHistorySearch"
                      class="search-clear"
                      type="button"
                      @click="loginHistorySearch = ''"
                      aria-label="清空搜索"
                    >
                      ×
                    </button>
                  </div>
                  <button
                    class="modal-refresh-btn"
                    type="button"
                    @click="loadLoginHistory({ force: true, isRefresh: true })"
                    :disabled="loadingLoginHistory || refreshingLoginHistory"
                    aria-label="刷新登录历史"
                    title="刷新"
                  >
                    <svg 
                      viewBox="0 0 24 24" 
                      fill="none" 
                      xmlns="http://www.w3.org/2000/svg"
                      :class="{ 'refresh-icon-spinning': refreshingLoginHistory }"
                    >
                      <path d="M21 12a9 9 0 1 1-2.64-6.36" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                      <path d="M21 3v6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                </div>
              </div>

              <div v-if="loadingLoginHistory && !refreshingLoginHistory" class="skeleton-list">
                <div v-for="n in 3" :key="n" class="skeleton-card">
                  <div class="skeleton-icon"></div>
                  <div class="skeleton-lines">
                    <div class="skeleton-line skeleton-line--lg"></div>
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line skeleton-line--sm"></div>
                  </div>
                </div>
              </div>

              <div
                v-else-if="loginHistoryErrorType === 'permission'"
                class="app-alert app-alert--warning"
                role="status"
                aria-live="polite"
              >
                <div class="app-alert-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 9v4M12 17h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
                  </svg>
                </div>
                <div class="app-alert-content">
                  <p class="app-alert-title">操作受限</p>
                  <p class="app-alert-message">{{ loginHistoryErrorMessage }}</p>
                  <div class="app-alert-actions">
                    <button class="auth-button" type="button" @click="loadLoginHistory({ force: true })">
                      重试
                    </button>
                  </div>
                </div>
              </div>

              <div
                v-else-if="loginHistoryErrorType === 'network'"
                class="app-alert app-alert--error"
                role="alert"
                aria-live="assertive"
              >
                <div class="app-alert-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                    <path d="M8 12h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </div>
                <div class="app-alert-content">
                  <p class="app-alert-title">加载失败</p>
                  <p class="app-alert-message">{{ loginHistoryErrorMessage }}</p>
                  <div class="app-alert-actions">
                    <button class="auth-button" type="button" @click="loadLoginHistory({ force: true })">
                      重试
                    </button>
                  </div>
                </div>
              </div>

              <div v-else-if="filteredLoginHistory.length === 0" class="empty-state">
                <div class="empty-state-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
                <p class="empty-state-title">
                  {{ loginHistory.length === 0 ? "当前没有登录记录，一切正常。" : "没有匹配的记录" }}
                </p>
                <p class="empty-state-subtitle">
                  {{ loginHistory.length === 0 ? "如发现陌生登录，可前往“活跃会话”撤销相关设备。" : "可尝试调整筛选条件或搜索关键词。" }}
                </p>
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
                      <div class="history-item-header-right">
                        <span class="history-item-time">{{ formatTime(item.created_at) }}</span>
                        <button
                          class="accordion-toggle"
                          type="button"
                          :aria-expanded="expandedLoginHistoryDetailsKey === item.id ? 'true' : 'false'"
                          :aria-controls="`login-history-details-${item.id}`"
                          @click="toggleLoginHistoryDetails(item.id)"
                        >
                          {{ expandedLoginHistoryDetailsKey === item.id ? "收起详情" : "展开详情" }}
                        </button>
                      </div>
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
                    <Transition
                      name="collapse"
                      @enter="collapseEnter"
                      @after-enter="collapseAfterEnter"
                      @leave="collapseLeave"
                    >
                      <div
                        v-if="expandedLoginHistoryDetailsKey === item.id"
                        class="history-item-details"
                        :id="`login-history-details-${item.id}`"
                      >
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
                    </Transition>
                  </div>
                </div>
                </div>
                
                <!-- 分页控件 -->
                <div v-if="totalLoginHistoryPages > 1" class="pagination-container">
                  <div class="pagination-info">
                    <span>共 {{ filteredLoginHistory.length }} 条记录</span>
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
          <div class="modal-content glass-card modal-content--lg">
            <div class="modal-header">
              <div class="modal-header-text">
                <h2 id="sessions-title" ref="sessionsTitleRef" tabindex="-1">活跃会话</h2>
                <p class="modal-subtitle">管理已登录设备，撤销不认识的会话。</p>
              </div>
              <div class="modal-header-right">
                <span class="modal-updated-at" aria-live="polite">{{ sessionsUpdatedLabel }}</span>
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
            </div>
            <div class="modal-body">
              <p class="modal-tip-pill sec-pill sec-pill--warning sec-pill--one-line">
                建议定期检查并关闭不认识的设备登录。
              </p>
              <div class="modal-toolbar">
                <div class="modal-toolbar-left">
                  <div class="filter-pills" role="tablist" aria-label="活跃会话筛选">
                    <button
                      class="filter-pill"
                      :class="{ 'filter-pill-active': sessionsFilter === 'all' }"
                      type="button"
                      @click="sessionsFilter = 'all'"
                    >
                      全部
                    </button>
                    <button
                      class="filter-pill"
                      :class="{ 'filter-pill-active': sessionsFilter === 'abnormal' }"
                      type="button"
                      @click="sessionsFilter = 'abnormal'"
                    >
                      仅其他设备
                    </button>
                    <button
                      class="filter-pill"
                      :class="{ 'filter-pill-active': sessionsFilter === '7d' }"
                      type="button"
                      @click="sessionsFilter = '7d'"
                    >
                      近 7 天活跃
                    </button>
                  </div>
                </div>
                <div class="modal-toolbar-right">
                  <div class="search-input">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                      <circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="2"/>
                      <path d="M20 20l-3.5-3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    <input
                      v-model="sessionsSearch"
                      type="text"
                      placeholder="搜索设备 / IP"
                      aria-label="搜索设备或IP"
                    />
                    <button
                      v-if="sessionsSearch"
                      class="search-clear"
                      type="button"
                      @click="sessionsSearch = ''"
                      aria-label="清空搜索"
                    >
                      ×
                    </button>
                  </div>
                  <button
                    class="modal-refresh-btn"
                    type="button"
                    @click="loadSessions({ force: true, isRefresh: true })"
                    :disabled="loadingSessions || refreshingSessions"
                    aria-label="刷新会话列表"
                    title="刷新"
                  >
                    <svg 
                      viewBox="0 0 24 24" 
                      fill="none" 
                      xmlns="http://www.w3.org/2000/svg"
                      :class="{ 'refresh-icon-spinning': refreshingSessions }"
                    >
                      <path d="M21 12a9 9 0 1 1-2.64-6.36" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                      <path d="M21 3v6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                </div>
              </div>

              <div v-if="loadingSessions && !refreshingSessions" class="skeleton-list">
                <div v-for="n in 3" :key="n" class="skeleton-card">
                  <div class="skeleton-icon"></div>
                  <div class="skeleton-lines">
                    <div class="skeleton-line skeleton-line--lg"></div>
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line skeleton-line--sm"></div>
                  </div>
                </div>
              </div>

              <div
                v-else-if="sessionsErrorType === 'permission'"
                class="app-alert app-alert--warning"
                role="status"
                aria-live="polite"
              >
                <div class="app-alert-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 9v4M12 17h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
                  </svg>
                </div>
                <div class="app-alert-content">
                  <p class="app-alert-title">操作受限</p>
                  <p class="app-alert-message">{{ sessionsErrorMessage }}</p>
                  <div class="app-alert-actions">
                    <button class="auth-button" type="button" @click="loadSessions({ force: true })">
                      重试
                    </button>
                  </div>
                </div>
              </div>

              <div
                v-else-if="sessionsErrorType === 'network'"
                class="app-alert app-alert--error"
                role="alert"
                aria-live="assertive"
              >
                <div class="app-alert-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                    <path d="M8 12h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </div>
                <div class="app-alert-content">
                  <p class="app-alert-title">加载失败</p>
                  <p class="app-alert-message">{{ sessionsErrorMessage }}</p>
                  <div class="app-alert-actions">
                    <button class="auth-button" type="button" @click="loadSessions({ force: true })">
                      重试
                    </button>
                  </div>
                </div>
              </div>

              <div v-else-if="filteredSessions.length === 0" class="empty-state">
                <div class="empty-state-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
                <p class="empty-state-title">没有匹配的会话</p>
                <p class="empty-state-subtitle">可尝试调整筛选条件或搜索关键词。</p>
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
                        <div class="session-item-token-row">
                          <span class="session-item-token-label">Token</span>
                          <Transition name="fade-slide" mode="out-in">
                            <span
                              :key="expandedSessionTokens.has(session.session_id || session.token) ? 'full' : 'short'"
                              class="session-item-token-mono"
                            >
                              {{ expandedSessionTokens.has(session.session_id || session.token) ? (session.token || "未知") : shortToken(session.token) }}
                            </span>
                          </Transition>
                          <button
                            class="session-copy-btn"
                            type="button"
                            :disabled="!session.token"
                            @click="copyText(session.token)"
                            aria-label="复制 Token"
                            title="复制"
                          >
                            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                              <rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" stroke-width="2"/>
                              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            </svg>
                          </button>
                          <button
                            class="session-expand-btn"
                            type="button"
                            :disabled="!session.token || (session.token || '').length <= 16"
                            @click="toggleSessionToken(session.session_id || session.token)"
                            aria-label="展开或收起 Token"
                            title="展开/收起"
                          >
                            {{ expandedSessionTokens.has(session.session_id || session.token) ? "收起" : "展开" }}
                          </button>
                        </div>
                        <button
                          class="accordion-toggle"
                          type="button"
                          :aria-expanded="expandedSessionDetailsKey === (session.session_id || session.token) ? 'true' : 'false'"
                          :aria-controls="`session-details-${session.session_id || session.token}`"
                          @click="toggleSessionDetails(session.session_id || session.token)"
                        >
                          {{ expandedSessionDetailsKey === (session.session_id || session.token) ? "收起详情" : "展开详情" }}
                        </button>
                        <span v-if="session.is_current" class="session-item-badge">当前会话</span>
                      </div>
                      <Transition
                        name="collapse"
                        @enter="collapseEnter"
                        @after-enter="collapseAfterEnter"
                        @leave="collapseLeave"
                      >
                        <div
                          v-if="expandedSessionDetailsKey === (session.session_id || session.token)"
                          class="session-item-details"
                          :id="`session-details-${session.session_id || session.token}`"
                        >
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
                            <span class="detail-value">
                              {{ formatRelativeTime(session.last_used_at) }}
                              <span class="detail-subtle">（{{ formatTime(session.last_used_at) }}）</span>
                            </span>
                          </div>
                        </div>
                      </Transition>
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
                    <span>共 {{ filteredSessions.length }} 个会话</span>
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
                    <span>
                      {{
                        revokingAllSessions
                          ? "撤销中..."
                          : (Date.now() < revokeAllConfirmUntil ? "确认撤销（2秒内）" : "撤销所有会话")
                      }}
                    </span>
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
          <div class="modal-content glass-card modal-content--md">
            <div class="modal-header">
              <div class="modal-header-text">
                <h2 id="avatar-modal-title" ref="avatarModalTitleRef" tabindex="-1">编辑头像</h2>
                <p class="modal-subtitle">上传并调整头像，推荐清晰的正方形图片。</p>
              </div>
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
                          :style="getAvatarTransformStyle()"
                          @pointerdown.prevent="handleAvatarPointerDown"
                          @pointermove.prevent="handleAvatarPointerMove"
                          @pointerup.prevent="endAvatarDragging"
                          @pointercancel.prevent="endAvatarDragging"
                          @pointerleave.prevent="endAvatarDragging"
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
                  <div class="avatar-dual-preview">
                    <div class="avatar-mini-preview">
                      <div class="avatar-mini-label">圆形</div>
                      <div class="avatar-mini avatar-mini--circle">
                        <img
                          v-if="avatarPreviewUrl || userStore.user?.avatar"
                          :src="avatarPreviewUrl || userStore.user?.avatar"
                          alt="圆形预览"
                          :style="getAvatarTransformStyle()"
                        />
                      </div>
                    </div>
                    <div class="avatar-mini-preview">
                      <div class="avatar-mini-label">方形</div>
                      <div class="avatar-mini avatar-mini--square">
                        <img
                          v-if="avatarPreviewUrl || userStore.user?.avatar"
                          :src="avatarPreviewUrl || userStore.user?.avatar"
                          alt="方形预览"
                          :style="getAvatarTransformStyle()"
                        />
                      </div>
                    </div>
                  </div>
                </div>
                <div class="avatar-control-panel">
                  <div class="form-group">
                    <label class="form-label">选择图片</label>
                    <label class="avatar-upload-btn">
                      <input
                        type="file"
                        accept="image/*"
                        @change="handleAvatarFileChange"
                        :aria-invalid="avatarError ? 'true' : 'false'"
                        :aria-describedby="avatarError ? 'avatar-error' : undefined"
                      />
                      <span>上传图片</span>
                    </label>
                    <div v-if="avatarError" id="avatar-error" class="field-error">{{ avatarError }}</div>
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
                  <div class="form-group">
                    <label class="form-label">调整</label>
                    <div class="avatar-transform-row">
                      <button class="avatar-tool-btn" type="button" @click="rotateAvatar90" :disabled="!avatarImage">
                        旋转 90°
                      </button>
                      <button class="avatar-tool-btn avatar-tool-btn--ghost" type="button" @click="resetAvatarTransform" :disabled="!avatarImage">
                        重置
                      </button>
                    </div>
                    <p class="avatar-upload-hint">可拖拽预览区移动位置，修正手机照片方向或构图。</p>
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
import { ref, computed, onMounted, watch, nextTick } from "vue";
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

const changePasswordErrorTarget = computed<"none" | "current" | "new" | "confirm">(() => {
  const msg = (changePasswordError.value || "").trim();
  if (!msg) return "none";
  if (msg.includes("当前密码")) return "current";
  if (msg.includes("不一致") || msg.includes("确认")) return "confirm";
  if (msg.includes("新密码")) return "new";
  return "none";
});

const loginHistory = ref<LoginHistoryItem[]>([]);
const loadingLoginHistory = ref(false);
const refreshingLoginHistory = ref(false);
const currentLoginHistoryPage = ref(1);
const loginHistoryPageSize = 3; // 每页显示3条记录

const currentLoginMethod = ref<"email" | "google" | "github">(userStore.user?.provider || "email");

const sessions = ref<SessionInfo[]>([]);
const loadingSessions = ref(false);
const refreshingSessions = ref(false);
const currentSessionsPage = ref(1);
const sessionsPageSize = 3; // 每页3条，与登录历史保持一致
const revokingSession = ref<string | null>(null);
const revokingAllSessions = ref(false);
const revokeAllConfirmUntil = ref<number>(0);

const loginHistoryErrorType = ref<"none" | "permission" | "network">("none");
const loginHistoryErrorMessage = ref("");
const sessionsErrorType = ref<"none" | "permission" | "network">("none");
const sessionsErrorMessage = ref("");

const loginHistoryFilter = ref<"all" | "failed" | "7d">("all");
const loginHistorySearch = ref("");
const sessionsFilter = ref<"all" | "abnormal" | "7d">("all");
const sessionsSearch = ref("");

const CACHE_MS = 60_000;
const lastLoginHistoryFetchedAt = ref<number>(0);
const lastSessionsFetchedAt = ref<number>(0);
const lastLoginHistoryUpdatedAt = ref<number>(0);
const lastSessionsUpdatedAt = ref<number>(0);

const formatRelativeFromTs = (ts: number) => {
  if (!ts) return "未更新";
  return formatRelativeTime(new Date(ts).toISOString());
};

const loginHistoryUpdatedLabel = computed(() => `最近更新：${formatRelativeFromTs(lastLoginHistoryUpdatedAt.value)}`);
const sessionsUpdatedLabel = computed(() => `最近更新：${formatRelativeFromTs(lastSessionsUpdatedAt.value)}`);

const resendingVerification = ref(false);

const modalBodyLockCount = ref(0);

// 为避免任何布局跳动，这里不再锁定滚动容器，仅保留计数接口以兼容调用方
const lockBodyScroll = () => {
  modalBodyLockCount.value += 1;
};

const unlockBodyScroll = () => {
  if (modalBodyLockCount.value <= 0) return;
  modalBodyLockCount.value -= 1;
};

// A11y: 记录触发元素，关闭时还原焦点
const lastTriggerEl = ref<HTMLElement | null>(null);
const setLastTrigger = (e?: Event) => {
  const target = (e?.currentTarget || e?.target) as HTMLElement | null;
  if (target && typeof target.focus === "function") lastTriggerEl.value = target;
};
const restoreFocus = async () => {
  await nextTick();
  if (lastTriggerEl.value) {
    try {
      lastTriggerEl.value.focus();
    } catch {
      // ignore
    }
  }
};

const changePasswordTriggerRef = ref<HTMLElement | null>(null);
const loginHistoryTriggerRef = ref<HTMLElement | null>(null);
const sessionsTriggerRef = ref<HTMLElement | null>(null);
const avatarTriggerRef = ref<HTMLElement | null>(null);
const nameTriggerRef = ref<HTMLElement | null>(null);

const changePasswordTitleRef = ref<HTMLElement | null>(null);
const loginHistoryTitleRef = ref<HTMLElement | null>(null);
const sessionsTitleRef = ref<HTMLElement | null>(null);
const avatarModalTitleRef = ref<HTMLElement | null>(null);

const currentPasswordInputRef = ref<HTMLInputElement | null>(null);
const nameInputRef = ref<HTMLInputElement | null>(null);

const focusEl = async (el: HTMLElement | { focus?: (opts?: FocusOptions) => void } | null | undefined) => {
  await nextTick();
  try {
    // 优先使用 preventScroll，避免触发自动滚动导致布局轻微抖动
    if (el && "focus" in el) {
      (el as any).focus?.({ preventScroll: true });
    }
  } catch {
    // ignore
  }
};

// 头像上传 / 裁剪
const showAvatarModal = ref(false);
const avatarPreviewUrl = ref<string | null>(null);
const avatarImage = ref<HTMLImageElement | null>(null);
const avatarZoom = ref(1.1);
const avatarUploading = ref(false);
const avatarError = ref("");
const avatarRotate = ref<0 | 90 | 180 | 270>(0);
const avatarOffsetX = ref(0);
const avatarOffsetY = ref(0);
const avatarDragging = ref(false);
const avatarDragStartX = ref(0);
const avatarDragStartY = ref(0);
const avatarDragStartOffsetX = ref(0);
const avatarDragStartOffsetY = ref(0);

const clamp = (v: number, min: number, max: number) => Math.max(min, Math.min(max, v));

const AVATAR_PREVIEW_SIZE = 200; // 主预览裁剪窗口（圆形）直径，px

const getAvatarMaxOffsets = () => {
  const img = avatarImage.value;
  if (!img) return { maxX: 0, maxY: 0 };

  // 先让图片在预览窗口“至少覆盖”（cover），再叠加用户缩放
  const baseScale = Math.max(AVATAR_PREVIEW_SIZE / img.width, AVATAR_PREVIEW_SIZE / img.height);
  const scale = baseScale * avatarZoom.value;
  const w = img.width * scale;
  const h = img.height * scale;

  // 旋转后矩形的轴对齐包围盒尺寸
  const rad = (avatarRotate.value * Math.PI) / 180;
  const cos = Math.cos(rad);
  const sin = Math.sin(rad);
  const bw = Math.abs(w * cos) + Math.abs(h * sin);
  const bh = Math.abs(w * sin) + Math.abs(h * cos);

  // 为避免留白，中心点可移动范围为 (bbox - window) / 2
  const maxX = Math.max(0, (bw - AVATAR_PREVIEW_SIZE) / 2);
  const maxY = Math.max(0, (bh - AVATAR_PREVIEW_SIZE) / 2);
  return { maxX, maxY };
};

const clampAvatarOffsets = () => {
  const { maxX, maxY } = getAvatarMaxOffsets();
  avatarOffsetX.value = clamp(avatarOffsetX.value, -maxX, maxX);
  avatarOffsetY.value = clamp(avatarOffsetY.value, -maxY, maxY);
};

const getAvatarTransformStyle = () => {
  return {
    transform: `translate(${avatarOffsetX.value}px, ${avatarOffsetY.value}px) rotate(${avatarRotate.value}deg) scale(${avatarZoom.value})`,
    cursor: avatarImage.value ? (avatarDragging.value ? "grabbing" : "grab") : "default",
  } as Record<string, string>;
};

const rotateAvatar90 = () => {
  avatarRotate.value = ((avatarRotate.value + 90) % 360) as 0 | 90 | 180 | 270;
  clampAvatarOffsets();
};

const resetAvatarTransform = () => {
  avatarZoom.value = 1.1;
  avatarRotate.value = 0;
  avatarOffsetX.value = 0;
  avatarOffsetY.value = 0;
};

const handleAvatarPointerDown = (e: PointerEvent) => {
  if (!avatarImage.value) return;
  avatarDragging.value = true;
  avatarDragStartX.value = e.clientX;
  avatarDragStartY.value = e.clientY;
  avatarDragStartOffsetX.value = avatarOffsetX.value;
  avatarDragStartOffsetY.value = avatarOffsetY.value;
  try {
    (e.currentTarget as HTMLElement | null)?.setPointerCapture?.(e.pointerId);
  } catch {
    // ignore
  }
};

const handleAvatarPointerMove = (e: PointerEvent) => {
  if (!avatarDragging.value) return;
  const dx = e.clientX - avatarDragStartX.value;
  const dy = e.clientY - avatarDragStartY.value;
  const { maxX, maxY } = getAvatarMaxOffsets();
  avatarOffsetX.value = clamp(avatarDragStartOffsetX.value + dx, -maxX, maxX);
  avatarOffsetY.value = clamp(avatarDragStartOffsetY.value + dy, -maxY, maxY);
};

const endAvatarDragging = (e?: PointerEvent) => {
  if (!avatarDragging.value) return;
  avatarDragging.value = false;
  if (e) {
    try {
      (e.currentTarget as HTMLElement | null)?.releasePointerCapture?.(e.pointerId);
    } catch {
      // ignore
    }
  }
};

// 缩放/旋转变化时也要自动约束位移，避免出现边缘留白
watch([avatarZoom, avatarRotate, avatarImage], () => {
  clampAvatarOffsets();
});

watch([loginHistoryFilter, loginHistorySearch], () => {
  currentLoginHistoryPage.value = 1;
});

watch([sessionsFilter, sessionsSearch], () => {
  currentSessionsPage.value = 1;
});

// 头像引导提示：仅首次显示一次
const showAvatarHint = ref(false);

// 用户名内联编辑
const editingName = ref(false);
const nameInput = ref("");
const savingName = ref(false);
const nameError = ref("");
const nameTouched = ref(false);

const validateNameLive = () => {
  if (!editingName.value) return;
  if (!nameTouched.value) return;
  const value = nameInput.value.trim();
  if (!value) {
    nameError.value = "昵称不能为空";
    return;
  }
  if (value.length > 50) {
    nameError.value = "昵称长度不能超过 50 个字符";
    return;
  }
  nameError.value = "";
};

const onNameBlur = () => {
  nameTouched.value = true;
  validateNameLive();
};

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

// 首屏避免额外请求：优先用用户信息中的 provider 推断登录方式；
// 打开“登录历史”弹窗时再加载完整审计记录并纠正展示。
watch(
  () => userStore.user?.provider,
  (provider) => {
    if (provider === "email" || provider === "google" || provider === "github") {
      currentLoginMethod.value = provider;
    } else {
      currentLoginMethod.value = "email";
    }
  },
  { immediate: true }
);

const sessionBadgeVariant = computed<"neutral" | "warning">(() => {
  if (!sessions.value || sessions.value.length === 0) return "neutral";
  if (sessions.value.length >= 2) return "warning";
  // length === 1
  const only = sessions.value[0] as any;
  return only?.is_current ? "neutral" : "warning";
});

const sessionBadgeLabel = computed(() => {
  const count = sessions.value?.length || 0;
  if (count <= 0) return "";
  if (count === 1 && sessionBadgeVariant.value === "neutral") return "仅当前设备";
  return `${count} 个活跃会话`;
});

const canChangePassword = computed(() => {
  // provider 不代表“当前登录方式”，也不应作为权限依据；
  // 是否能改密码取决于账户是否设置过密码（OAuth-only 用户需要先走“忘记密码”设置密码）
  return !!userStore.user?.has_password;
});

const isEmailVerified = computed(() => {
  return !!userStore.user?.email_verified;
});

const emailRestrictionMessage = "当前邮箱未验证，部分安全操作将受限，建议尽快完成验证。";

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

const filteredSessions = computed(() => {
  const q = sessionsSearch.value.trim().toLowerCase();
  const now = Date.now();
  return sessions.value.filter((s) => {
    if (!s) return false;
    if (sessionsFilter.value === "abnormal" && s.is_current) return false;
    if (sessionsFilter.value === "7d") {
      const t = new Date((s.last_used_at as any) || s.created_at || "").getTime();
      if (!Number.isFinite(t) || now - t > 7 * 24 * 3600 * 1000) return false;
    }
    if (q) {
      const hay = `${s.ip || ""} ${s.user_agent || ""} ${parseUserAgent(s.user_agent || "")}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
});

// 计算分页后的活跃会话列表
const totalSessionsPages = computed(() => {
  return filteredSessions.value.length === 0 ? 1 : Math.ceil(filteredSessions.value.length / sessionsPageSize);
});

const paginatedSessions = computed(() => {
  const start = (currentSessionsPage.value - 1) * sessionsPageSize;
  const end = start + sessionsPageSize;
  return filteredSessions.value.slice(start, end);
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

const formatRelativeTime = (timeStr: string) => {
  if (!timeStr) return "未知";
  const t = new Date(timeStr).getTime();
  if (!Number.isFinite(t)) return timeStr;
  const diff = Date.now() - t;
  if (diff < 0) return "刚刚";
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return "刚刚";
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} 分钟前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} 小时前`;
  const day = Math.floor(hr / 24);
  if (day < 7) return `${day} 天前`;
  // 超过一周回落到绝对时间，避免“32天前”不直观
  return formatTime(timeStr);
};

const shortToken = (token?: string) => {
  const t = (token || "").trim();
  if (!t) return "未知";
  if (t.length <= 16) return t;
  return `${t.slice(0, 6)}…${t.slice(-6)}`;
};

const copyText = async (text: string) => {
  const v = (text || "").trim();
  if (!v) return;
  try {
    await navigator.clipboard.writeText(v);
    showToast("success", "已复制", "已复制到剪贴板");
  } catch {
    try {
      const ta = document.createElement("textarea");
      ta.value = v;
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      showToast("success", "已复制", "已复制到剪贴板");
    } catch {
      showToast("error", "复制失败", "请手动复制");
    }
  }
};

const expandedSessionTokens = ref(new Set<string>());
const toggleSessionToken = (key: string) => {
  if (!key) return;
  const s = expandedSessionTokens.value;
  if (s.has(key)) s.delete(key);
  else s.add(key);
  // 触发响应式更新：Set 本身不是深度追踪，替换引用更稳妥
  expandedSessionTokens.value = new Set(s);
};

// Accordion: details expand/collapse (height animation)
// Accordion mode: only one item expanded at a time (per list)
const expandedSessionDetailsKey = ref<string | null>(null);
const toggleSessionDetails = (key: string) => {
  if (!key) return;
  expandedSessionDetailsKey.value = expandedSessionDetailsKey.value === key ? null : key;
};

const expandedLoginHistoryDetailsKey = ref<string | null>(null);
const toggleLoginHistoryDetails = (key: string) => {
  if (!key) return;
  expandedLoginHistoryDetailsKey.value = expandedLoginHistoryDetailsKey.value === key ? null : key;
};

const collapseEnter = (el: Element) => {
  const node = el as HTMLElement;
  node.style.height = "0px";
  node.style.overflow = "hidden";
  node.style.willChange = "height";
  // force reflow
  // eslint-disable-next-line @typescript-eslint/no-unused-expressions
  node.offsetHeight;
  node.style.height = `${node.scrollHeight}px`;
};

const collapseAfterEnter = (el: Element) => {
  const node = el as HTMLElement;
  node.style.height = "auto";
  node.style.overflow = "";
  node.style.willChange = "";
};

const collapseLeave = (el: Element) => {
  const node = el as HTMLElement;
  node.style.height = `${node.scrollHeight}px`;
  node.style.overflow = "hidden";
  node.style.willChange = "height";
  // force reflow
  // eslint-disable-next-line @typescript-eslint/no-unused-expressions
  node.offsetHeight;
  node.style.height = "0px";
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
  resetAvatarTransform();
  avatarError.value = "";
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

const openAvatarModalFromTrigger = (e: Event) => {
  setLastTrigger(e);
  openAvatarModal();
};

const handleAvatarFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (!target.files || !target.files[0]) return;
  const file = target.files[0];

  avatarError.value = "";
  // 选择新图时重置变换，更符合用户预期
  resetAvatarTransform();
  if (!file.type.startsWith("image/")) {
    avatarError.value = "格式不支持：请上传 JPG 或 PNG 图片";
    return;
  }
  if (file.size > 2 * 1024 * 1024) {
    avatarError.value = "图片过大：头像图片大小不能超过 2MB";
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
      clampAvatarOffsets();
    };
    img.src = result;
  };
  reader.readAsDataURL(file);
};

const startEditName = () => {
  setLastTrigger({ currentTarget: nameTriggerRef.value } as any);
  nameError.value = "";
  nameTouched.value = false;
  editingName.value = true;
  nameInput.value = userStore.user?.name || "";
  focusEl(nameInputRef.value);
};

const cancelEditName = () => {
  editingName.value = false;
  nameError.value = "";
  nameTouched.value = false;
  nameInput.value = userStore.user?.name || "";
  restoreFocus();
};

const saveName = async () => {
  nameError.value = "";
  const value = nameInput.value.trim();
  if (!value) {
    nameError.value = "昵称不能为空";
    return;
  }
  if (value.length > 50) {
    nameError.value = "昵称长度不能超过 50 个字符";
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
    restoreFocus();
  } catch (err: any) {
    showToast("error", "保存失败", err.message || "保存昵称失败，请稍后重试");
    // 可重试的服务端错误也给输入区域一个可见提示（更不打扰）
    nameError.value = err?.message || "保存失败，请稍后重试";
  } finally {
    savingName.value = false;
  }
};

const handleSaveAvatar = async () => {
  avatarError.value = "";
  if (!avatarPreviewUrl.value) {
    avatarError.value = "请先选择一张头像图片";
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
  // 让图片至少覆盖整个输出画布（再叠加用户缩放），避免出现边缘留白
  const baseScale = Math.max(size / img.width, size / img.height);
  const scale = baseScale * avatarZoom.value;
  // 将预览中的平移（基于 200px 圆形区域）映射到 512 输出画布
  const offsetScale = size / 200;
  const tx = size / 2 + avatarOffsetX.value * offsetScale;
  const ty = size / 2 + avatarOffsetY.value * offsetScale;
  ctx.translate(tx, ty);
  ctx.rotate((avatarRotate.value * Math.PI) / 180);
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
    const msg = err?.message || "上传头像失败，请稍后重试";
    // 用户可修复的错误（格式/大小/空文件等）优先内联提示，不弹 toast
    if (
      msg.includes("JPG") ||
      msg.includes("PNG") ||
      msg.includes("2MB") ||
      msg.includes("为空") ||
      msg.includes("格式")
    ) {
      avatarError.value = msg;
    } else {
      avatarError.value = msg;
      showToast("error", "上传失败", msg);
    }
  } finally {
    avatarUploading.value = false;
    showAvatarModal.value = false;
    unlockBodyScroll();
  }
};

const openChangePasswordModalFromTrigger = (e: Event) => {
  setLastTrigger(e);
  showChangePasswordModal.value = true;
};

const openLoginHistoryModalFromTrigger = (e: Event) => {
  setLastTrigger(e);
  showLoginHistoryModal.value = true;
};

const openSessionsModalFromTrigger = (e: Event) => {
  setLastTrigger(e);
  showSessionsModal.value = true;
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
    // 权限/受限：保留黄 toast
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
    const msg = err?.message || "修改失败，请稍后重试";
    // 可修复错误优先 inline，避免打扰
    changePasswordError.value = msg;
    // 严重失败才红 toast（这里用关键词做一个保守判断）
    if (msg.includes("500") || msg.includes("timeout") || msg.includes("网络") || msg.includes("服务")) {
      showToast("error", "修改失败", msg);
    }
  } finally {
    changingPassword.value = false;
  }
};

// Change password: real-time validation (touched-based)
const changePasswordTouched = ref({ current: false, new: false, confirm: false });
const changePasswordFieldError = computed(() => {
  const current = changePasswordData.value.currentPassword || "";
  const next = changePasswordData.value.newPassword || "";
  const confirm = changePasswordData.value.confirmPassword || "";

  return {
    current: !current ? "请输入当前密码" : "",
    new: !next ? "请输入新密码" : next.length < 8 ? "新密码至少需要8个字符" : "",
    confirm: !confirm ? "请再次输入新密码" : next && confirm && next !== confirm ? "两次输入的密码不一致" : "",
  };
});

const validateChangePasswordLive = () => {
  // When any field is touched, keep the inline error message aligned with the first visible issue.
  if (!changePasswordTouched.value.current && !changePasswordTouched.value.new && !changePasswordTouched.value.confirm) return;

  // If user already submitted and got a server-side/permission error, don't fight it.
  const existing = (changePasswordError.value || "").trim();
  if (existing && (existing.includes("邮箱未验证") || existing.includes("500") || existing.includes("timeout") || existing.includes("网络") || existing.includes("服务"))) {
    return;
  }

  const errs = changePasswordFieldError.value;
  if (changePasswordTouched.value.current && errs.current) {
    changePasswordError.value = errs.current;
    return;
  }
  if (changePasswordTouched.value.new && errs.new) {
    changePasswordError.value = errs.new;
    return;
  }
  if (changePasswordTouched.value.confirm && errs.confirm) {
    changePasswordError.value = errs.confirm;
    return;
  }

  // Clear only if it's one of our client-side validation messages
  if (
    existing === "请输入当前密码" ||
    existing === "请输入新密码" ||
    existing === "新密码至少需要8个字符" ||
    existing === "两次输入的密码不一致" ||
    existing === "请输入确认密码" ||
    existing === "请再次输入新密码"
  ) {
    changePasswordError.value = "";
  }
};

const isPermissionError = (msg: string) => {
  const m = (msg || "").toLowerCase();
  return m.includes("401") || m.includes("403") || m.includes("unauthorized") || m.includes("forbidden") || m.includes("not authenticated");
};

const loadLoginHistory = async (opts?: { force?: boolean; silent?: boolean; isRefresh?: boolean }) => {
  const force = !!opts?.force;
  const silent = !!opts?.silent;
  const isRefresh = !!opts?.isRefresh;
  loginHistoryErrorType.value = "none";
  loginHistoryErrorMessage.value = "";

  if (!force && loginHistory.value.length > 0 && Date.now() - lastLoginHistoryFetchedAt.value < CACHE_MS) {
    return;
  }
  
  // 区分初始加载和刷新
  if (isRefresh && loginHistory.value.length > 0) {
    refreshingLoginHistory.value = true;
  } else {
    loadingLoginHistory.value = true;
  }
  
  const refreshStartedAt = Date.now();
  const MIN_REFRESH_MS = 450;

  currentLoginHistoryPage.value = 1; // 重置到第一页
  try {
    loginHistory.value = await getLoginHistory(50); // 获取更多记录用于分页
    lastLoginHistoryFetchedAt.value = Date.now();
    lastLoginHistoryUpdatedAt.value = Date.now();
    // 用最近一次成功登录的审计记录作为"当前登录方式"展示来源
    const latestSuccess = loginHistory.value.find((x) => x && x.success);
    if (latestSuccess && (latestSuccess.login_method === "email" || latestSuccess.login_method === "google" || latestSuccess.login_method === "github")) {
      currentLoginMethod.value = latestSuccess.login_method;
    } else {
      currentLoginMethod.value = "email";
    }
  } catch (err: any) {
    const msg = err?.message || "加载失败，请稍后重试";
    if (isPermissionError(msg)) {
      loginHistoryErrorType.value = "permission";
      loginHistoryErrorMessage.value = "当前操作受限：请先完成邮箱验证或重新登录后再试。";
      if (!silent) showToast("warning", "操作被限制", loginHistoryErrorMessage.value);
    } else {
      loginHistoryErrorType.value = "network";
      loginHistoryErrorMessage.value = msg;
      if (!silent) showToast("error", "加载失败", msg);
    }
  } finally {
    // 让“无感刷新”的旋转有可感知的存在感（避免请求太快肉眼看不到）
    if (isRefresh) {
      const elapsed = Date.now() - refreshStartedAt;
      if (elapsed < MIN_REFRESH_MS) {
        await new Promise((r) => setTimeout(r, MIN_REFRESH_MS - elapsed));
      }
    }
    loadingLoginHistory.value = false;
    refreshingLoginHistory.value = false;
  }
};

// 计算分页后的登录历史
const filteredLoginHistory = computed(() => {
  const q = loginHistorySearch.value.trim().toLowerCase();
  const now = Date.now();
  return loginHistory.value.filter((item) => {
    if (!item) return false;
    if (loginHistoryFilter.value === "failed" && item.success) return false;
    if (loginHistoryFilter.value === "7d") {
      const t = new Date(item.created_at || "").getTime();
      if (!Number.isFinite(t) || now - t > 7 * 24 * 3600 * 1000) return false;
    }
    if (q) {
      const hay = `${item.device_type || ""} ${item.ip || ""} ${item.browser || ""} ${item.os || ""}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
});

const paginatedLoginHistory = computed(() => {
  const start = (currentLoginHistoryPage.value - 1) * loginHistoryPageSize;
  const end = start + loginHistoryPageSize;
  return filteredLoginHistory.value.slice(start, end);
});

// 计算总页数
const totalLoginHistoryPages = computed(() => {
  return Math.ceil(filteredLoginHistory.value.length / loginHistoryPageSize);
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

const loadSessions = async (opts?: { force?: boolean; silent?: boolean; isRefresh?: boolean }) => {
  const force = !!opts?.force;
  const silent = !!opts?.silent;
  const isRefresh = !!opts?.isRefresh;
  sessionsErrorType.value = "none";
  sessionsErrorMessage.value = "";

  if (!force && sessions.value.length > 0 && Date.now() - lastSessionsFetchedAt.value < CACHE_MS) {
    return;
  }
  
  // 区分初始加载和刷新
  if (isRefresh && sessions.value.length > 0) {
    refreshingSessions.value = true;
  } else {
    loadingSessions.value = true;
  }
  
  const refreshStartedAt = Date.now();
  const MIN_REFRESH_MS = 450;

  try {
    sessions.value = await getSessions();
    lastSessionsFetchedAt.value = Date.now();
    lastSessionsUpdatedAt.value = Date.now();
    currentSessionsPage.value = 1;
  } catch (err: any) {
    const msg = err?.message || "加载失败，请稍后重试";
    if (isPermissionError(msg)) {
      sessionsErrorType.value = "permission";
      sessionsErrorMessage.value = "当前操作受限：请先完成邮箱验证或重新登录后再试。";
      if (!silent) showToast("warning", "操作被限制", sessionsErrorMessage.value);
    } else {
      sessionsErrorType.value = "network";
      sessionsErrorMessage.value = msg;
      if (!silent) showToast("error", "加载失败", msg);
    }
  } finally {
    if (isRefresh) {
      const elapsed = Date.now() - refreshStartedAt;
      if (elapsed < MIN_REFRESH_MS) {
        await new Promise((r) => setTimeout(r, MIN_REFRESH_MS - elapsed));
      }
    }
    loadingSessions.value = false;
    refreshingSessions.value = false;
  }
};

const handleRevokeSession = async (sessionIdOrTokenPrefix: string) => {
  revokingSession.value = sessionIdOrTokenPrefix;
  try {
    await revokeSession(sessionIdOrTokenPrefix);
    showToast("success", "撤销成功", "会话已撤销");
    await loadSessions({ force: true, silent: true, isRefresh: true });
  } catch (err: any) {
    const msg = err?.message || "撤销失败，请稍后重试";
    if (isPermissionError(msg)) {
      showToast("warning", "操作被限制", "当前操作受限，请先完成邮箱验证或重新登录后再试。");
    } else {
      showToast("error", "撤销失败", msg);
    }
  } finally {
    revokingSession.value = null;
  }
};

const handleRevokeAllSessions = async () => {
  // 二段式轻确认：2 秒内再次点击才执行
  if (Date.now() >= revokeAllConfirmUntil.value) {
    revokeAllConfirmUntil.value = Date.now() + 2000;
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
    const msg = err?.message || "撤销失败，请稍后重试";
    if (isPermissionError(msg)) {
      showToast("warning", "操作被限制", "当前操作受限，请先完成邮箱验证或重新登录后再试。");
    } else {
      showToast("error", "撤销失败", msg);
    }
  } finally {
    revokingAllSessions.value = false;
    revokeAllConfirmUntil.value = 0;
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
watch(showLoginHistoryModal, async (visible) => {
  if (visible) {
    lockBodyScroll();
    await focusEl(loginHistoryTitleRef.value);
    // 60s 内重复打开不重复请求；手动刷新可强制拉取
    loadLoginHistory({ silent: true });
  } else {
    unlockBodyScroll();
    restoreFocus();
  }
});

watch(showSessionsModal, async (visible) => {
  if (visible) {
    lockBodyScroll();
    await focusEl(sessionsTitleRef.value);
    loadSessions({ silent: true });
  } else {
    unlockBodyScroll();
    restoreFocus();
  }
});

watch(showChangePasswordModal, async (visible) => {
  if (visible) {
    lockBodyScroll();
    await focusEl(currentPasswordInputRef.value || changePasswordTitleRef.value);
  } else {
    unlockBodyScroll();
    restoreFocus();
  }
});

watch(showAvatarModal, async (visible) => {
  if (visible) {
    // openAvatarModal() 已经做了 lockBodyScroll
    await focusEl(avatarModalTitleRef.value);
  } else {
    unlockBodyScroll();
    restoreFocus();
  }
});

// 2FA / 社交绑定 / 密码泄露检测相关函数已移除，仅保留登录历史等通用安全信息

onMounted(() => {
  // 初始化时拉取一次会话列表（轻量：用于正确展示“活跃会话”徽章/提示）
  loadSessions({ silent: true });
  initAvatarHint();
});
</script>

<style scoped>
@import "@/styles/securitySection.tokens.css";

.settings {
  width: 100%;
  padding: 0;
  margin: 0;
  background: var(--gradient-settings-bg, linear-gradient(135deg, #f0f9ff 0%, #e0e7ff 50%, #f3e8ff 100%));
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
  color: var(--app-text, #1e293b);
  margin: 0 0 12px 0;
  letter-spacing: -0.03em;
  background: var(--gradient-primary, linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.settings-subtitle {
  font-size: 18px;
  color: var(--app-muted, #64748b);
  margin: 0;
  font-weight: 400;
}

.settings-section {
  padding: 48px;
  border-radius: 28px;
  background: var(--app-surface, rgba(255, 255, 255, 0.95));
  backdrop-filter: blur(20px);
  box-shadow: var(--shadow-md, 0 8px 32px rgba(0, 0, 0, 0.08));
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

/* security-warning-* replaced by global .app-alert */

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
  background: var(--sec-badge-warning-bg, rgba(254, 226, 226, 0.9));
  color: var(--sec-badge-warning-text, #b91c1c);
  box-shadow: var(--sec-badge-warning-shadow, 0 4px 14px rgba(248, 113, 113, 0.4));
}

.security-status-badge-neutral {
  background: var(--sec-badge-neutral-bg, rgba(219, 234, 254, 0.9));
  color: var(--sec-badge-neutral-text, #1d4ed8);
  box-shadow: var(--sec-badge-neutral-shadow, 0 4px 14px rgba(59, 130, 246, 0.28));
}

.security-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
}

.security-status-dot-warning {
  background: var(--sec-dot-warning-bg, #ef4444);
  box-shadow: var(--sec-dot-warning-shadow, 0 0 0 4px rgba(248, 113, 113, 0.3));
}

.security-status-dot-neutral {
  background: var(--sec-dot-neutral-bg, #3b82f6);
  box-shadow: var(--sec-dot-neutral-shadow, 0 0 0 4px rgba(59, 130, 246, 0.22));
}

/* security-warning-* replaced by global .app-alert */

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
  border: none;
  padding: 0;
  background: transparent;
  text-align: inherit;
}

.settings :is(
  button,
  [role="button"],
  a,
  input,
  select,
  textarea
):focus-visible {
  outline: 3px solid rgba(99, 102, 241, 0.45);
  outline-offset: 2px;
}

.settings :is(button, [role="button"]):focus-visible {
  border-radius: 12px;
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
  background: radial-gradient(circle at 0 0, #e0f2fe 0%, #6366f1 45%, #8b5cf6 100%);
  color: #f9fafb;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 10px 25px rgba(15, 23, 42, 0.38),
    0 0 0 1px rgba(255, 255, 255, 0.7);
  pointer-events: none; /* 避免嵌套可点击元素：点击落到外层头像按钮 */
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

.name-edit-pane {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.name-input.input-error {
  border-color: rgba(239, 68, 68, 0.85);
  box-shadow:
    0 14px 45px rgba(239, 68, 68, 0.12),
    0 0 0 3px rgba(239, 68, 68, 0.14),
    0 0 0 1px rgba(255, 255, 255, 0.9) inset;
  animation: shake-x 0.26s ease-in-out;
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

/* Transitions: lightweight, used for expand/collapse-like swaps */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.field-pop-enter-active,
.field-pop-leave-active {
  transition: opacity 0.16s ease, transform 0.16s ease;
}
.field-pop-enter-from,
.field-pop-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@keyframes shake-x {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  50% { transform: translateX(4px); }
  75% { transform: translateX(-3px); }
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
  max-width: 560px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-content--sm {
  max-width: 560px;
}

.modal-content--md {
  max-width: 720px;
}

.modal-content--lg {
  max-width: 860px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 28px;
  border-bottom: 1px solid #e2e8f0;
  gap: 16px;
}

.modal-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.modal-header-text {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.modal-header-right {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.modal-updated-at {
  font-size: 12px;
  font-weight: 700;
  color: var(--sec-muted, #64748b);
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(226, 232, 240, 0.9);
  padding: 6px 10px;
  border-radius: var(--sec-radius-pill, 999px);
  white-space: nowrap;
}

.modal-subtitle {
  font-size: 13px;
  color: #64748b;
  margin: 0;
  line-height: 1.4;
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
  padding: 24px 28px 28px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.avatar-modal-body {
  padding: 24px 28px 28px;
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

.avatar-preview-circle::before {
  content: "";
  position: absolute;
  inset: 0;
  /* 细腻的裁剪网格线 */
  background-image:
    linear-gradient(to right, rgba(15, 23, 42, 0.08) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(15, 23, 42, 0.08) 1px, transparent 1px);
  background-size: 18px 18px;
  opacity: 0.55;
  mix-blend-mode: soft-light;
  pointer-events: none;
}

.avatar-preview-circle::after {
  content: "";
  position: absolute;
  inset: 10%;
  /* 中心辅助线（十字线）+ 内圈裁剪框 */
  background:
    linear-gradient(to right, rgba(255, 255, 255, 0.65) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255, 255, 255, 0.65) 1px, transparent 1px);
  background-repeat: no-repeat;
  background-position: 50% 0, 0 50%;
  background-size: 1px 100%, 100% 1px;
  border-radius: 50%;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.7);
  opacity: 0.85;
  pointer-events: none;
}

.avatar-preview-circle img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform-origin: center center;
  transition: transform 0.15s ease-out;
  user-select: none;
  -webkit-user-drag: none;
}

.avatar-dual-preview {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  width: 100%;
  max-width: 260px;
}

.avatar-mini-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.avatar-mini-label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.avatar-mini {
  width: 104px;
  height: 104px;
  overflow: hidden;
  background: #eef2ff;
  border: 2px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.18);
  position: relative;
}

.avatar-mini::before {
  content: "";
  position: absolute;
  inset: 10%;
  background-image:
    linear-gradient(to right, rgba(15, 23, 42, 0.08) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(15, 23, 42, 0.08) 1px, transparent 1px);
  background-size: 14px 14px;
  opacity: 0.6;
  mix-blend-mode: soft-light;
  pointer-events: none;
}

.avatar-mini--circle {
  border-radius: 50%;
}

.avatar-mini--square {
  border-radius: 16px;
}

.avatar-mini img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform-origin: center center;
  transition: transform 0.15s ease-out;
  user-select: none;
  -webkit-user-drag: none;
}

.avatar-transform-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.avatar-tool-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 14px;
  border-radius: 999px;
  border: 1px solid rgba(99, 102, 241, 0.35);
  background: rgba(99, 102, 241, 0.08);
  color: #3730a3;
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.avatar-tool-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(99, 102, 241, 0.2);
  background: rgba(99, 102, 241, 0.12);
}

.avatar-tool-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.avatar-tool-btn--ghost {
  border-color: rgba(148, 163, 184, 0.6);
  background: rgba(148, 163, 184, 0.12);
  color: #334155;
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

/* spin keyframes are defined globally in src/styles.css */

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

.empty-state-title {
  font-size: 15px;
  font-weight: 600;
  color: #475569;
  margin: 0;
}

.empty-state-subtitle {
  font-size: 13px;
  font-weight: 400;
  color: #94a3b8;
  margin: 0;
  line-height: 1.4;
  max-width: 520px;
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

.history-item-header-right {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.accordion-toggle {
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: rgba(255, 255, 255, 0.7);
  color: rgba(51, 65, 85, 0.9);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  white-space: nowrap;
}

.accordion-toggle:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(99, 102, 241, 0.35);
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.10);
}

.accordion-toggle:active:not(:disabled) {
  transform: translateY(0);
}

.accordion-toggle:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.collapse-enter-active,
.collapse-leave-active {
  transition: height 0.22s cubic-bezier(0.4, 0, 0.2, 1);
}

.history-item-status,
.session-item-token {
  font-weight: 600;
  color: #0f172a;
  font-size: 15px;
  letter-spacing: -0.01em;
}

.detail-subtle {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 500;
}

.session-item-token-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.session-item-token-label {
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  background: rgba(148, 163, 184, 0.14);
  border: 1px solid rgba(148, 163, 184, 0.25);
  padding: 4px 8px;
  border-radius: 999px;
  flex-shrink: 0;
}

.session-item-token-mono {
  font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
  font-size: 13px;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.session-copy-btn,
.session-expand-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 30px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid rgba(203, 213, 225, 0.8);
  background: rgba(255, 255, 255, 0.7);
  color: #334155;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.session-copy-btn svg {
  width: 16px;
  height: 16px;
}

.session-copy-btn:hover:not(:disabled),
.session-expand-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.12);
  border-color: rgba(99, 102, 241, 0.35);
}

.session-copy-btn:disabled,
.session-expand-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.subtle-pill {
  /* legacy alias; styles are provided by sec-pill classes */
}

.modal-tip-pill {
  margin: 0 0 16px 0;
  display: inline-block;
}

.modal-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin: 0 0 16px 0;
  flex-wrap: wrap;
}

.filter-pills {
  display: inline-flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-pill {
  height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid rgba(203, 213, 225, 0.9);
  background: rgba(255, 255, 255, 0.7);
  color: #334155;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-pill:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.10);
}

.filter-pill-active {
  border-color: rgba(99, 102, 241, 0.35);
  background: rgba(99, 102, 241, 0.12);
  color: #3730a3;
}

.modal-toolbar-right {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  justify-content: flex-end;
  min-width: 260px;
}

.search-input {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(203, 213, 225, 0.9);
  flex: 1;
  max-width: 360px;
}

.search-input svg {
  width: 16px;
  height: 16px;
  color: #64748b;
  flex-shrink: 0;
}

.search-input input {
  border: none;
  outline: none;
  background: transparent;
  width: 100%;
  font-size: 13px;
  color: #0f172a;
}

.search-clear {
  width: 26px;
  height: 26px;
  border-radius: 999px;
  border: none;
  background: rgba(148, 163, 184, 0.18);
  color: #334155;
  cursor: pointer;
  font-weight: 800;
  line-height: 1;
}

.modal-refresh-btn {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  border: 1px solid rgba(203, 213, 225, 0.9);
  background: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  color: #334155;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.modal-refresh-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.10);
  border-color: rgba(99, 102, 241, 0.35);
}

.modal-refresh-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.modal-refresh-btn svg {
  width: 18px;
  height: 18px;
  transition: transform 0.3s ease;
  /* SVG 旋转在部分浏览器需要明确 box/origin，否则看起来“不转” */
  transform-box: fill-box;
  transform-origin: 50% 50%;
}

.refresh-icon-spinning {
  animation: refreshSpin 0.9s linear infinite;
}

@keyframes refreshSpin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 4px;
  margin: -4px;
}

.skeleton-card {
  display: flex;
  gap: 20px;
  padding: 20px;
  border-radius: 16px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.06);
}

.skeleton-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(90deg, rgba(226,232,240,0.9) 25%, rgba(241,245,249,0.9) 50%, rgba(226,232,240,0.9) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
  flex-shrink: 0;
}

.skeleton-lines {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 6px;
}

.skeleton-line {
  height: 12px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(226,232,240,0.9) 25%, rgba(241,245,249,0.9) 50%, rgba(226,232,240,0.9) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
  width: 70%;
}

.skeleton-line--lg {
  width: 48%;
  height: 14px;
}

.skeleton-line--sm {
  width: 34%;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.empty-state-warning .empty-state-icon {
  color: #f59e0b;
}

.empty-state-danger .empty-state-icon {
  color: #ef4444;
}

.restricted-action {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.restricted-help {
  /* tooltip trigger visuals are provided by .sec-tooltip-trigger */
}

.restricted-tooltip {
  /* tooltip visuals are provided by .sec-tooltip */
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

  .modal-toolbar-right {
    min-width: 0;
    width: 100%;
    justify-content: space-between;
  }

  .search-input {
    max-width: none;
  }

  .session-copy-btn,
  .session-expand-btn,
  .session-revoke-btn {
    height: 44px;
    padding: 0 14px;
  }

  .modal-header-right {
    gap: 10px;
  }

  .modal-updated-at {
    display: none;
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
@media (max-width: 1024px) {
  /* 不改变桌面端布局：仅在中小屏收紧间距/留白 */
  .settings-container {
    padding: 48px 32px;
    gap: 36px;
  }

  .settings-section {
    padding: 44px 36px;
    border-radius: 26px;
  }

  .settings-grid {
    gap: 28px;
  }
}

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

@media (max-width: 640px) {
  .settings-container {
    padding: 24px 14px;
    gap: 24px;
  }

  .settings-title {
    font-size: 32px;
  }

  .settings-subtitle {
    font-size: 15px;
  }

  .settings-section {
    padding: 22px 16px;
    border-radius: 20px;
  }

  .settings-grid {
    grid-template-columns: 1fr; /* 小屏强制单列 */
    gap: 16px;
  }

  .setting-card {
    padding: 22px 16px;
    min-height: auto;
  }

  /* 小屏：模态框全屏（不影响桌面端） */
  .modal-overlay {
    padding: 0;
    align-items: stretch;
    justify-content: stretch;
  }

  .modal-content {
    width: 100vw;
    height: 100vh;
    max-width: none;
    max-height: none;
    border-radius: 0;
    box-shadow: none;
  }

  .modal-header {
    padding: 16px 16px;
  }

  .modal-body,
  .avatar-modal-body {
    padding: 16px;
  }

  /* 头像编辑：小屏改为单列，避免左右两栏挤压 */
  .avatar-editor-grid {
    grid-template-columns: 1fr;
    gap: 18px;
  }

  .avatar-preview-wrapper {
    width: min(320px, 92vw);
    height: min(320px, 92vw);
  }
}

@media (max-width: 480px) {
  .settings-container {
    padding: 18px 12px;
    gap: 20px;
  }

  .settings-title {
    font-size: 28px;
  }

  .settings-subtitle {
    font-size: 14px;
  }

  .settings-section {
    padding: 18px 14px;
    border-radius: 18px;
  }

  .setting-card {
    padding: 18px 14px;
  }

  .modal-header h2 {
    font-size: 18px;
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
