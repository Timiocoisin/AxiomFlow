import { defineStore } from "pinia";
import { ref, computed } from "vue";

export interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
  provider?: "email" | "google" | "github";
  has_password?: boolean;
  email_verified?: boolean;
  email_verified_at?: string | null;
}

export const useUserStore = defineStore("user", () => {
  const user = ref<User | null>(null);
  // 优先从localStorage读取，如果没有则从sessionStorage读取
  const token = ref<string | null>(
    localStorage.getItem("auth_token") || sessionStorage.getItem("auth_token")
  );
  const refreshToken = ref<string | null>(
    localStorage.getItem("refresh_token") || sessionStorage.getItem("refresh_token")
  );

  const isLoggedIn = computed(() => !!user.value && !!token.value);

  const login = (userData: User, authToken: string, refreshTokenValue?: string, rememberMe: boolean = true) => {
    user.value = userData;
    token.value = authToken;
    if (refreshTokenValue) {
      refreshToken.value = refreshTokenValue;
    }
    
    if (rememberMe) {
      // 使用localStorage（持久化）
      localStorage.setItem("auth_token", authToken);
      localStorage.setItem("user", JSON.stringify(userData));
      if (refreshTokenValue) {
        localStorage.setItem("refresh_token", refreshTokenValue);
      }
      // 清除sessionStorage中的旧数据
      sessionStorage.removeItem("auth_token");
      sessionStorage.removeItem("user");
      sessionStorage.removeItem("refresh_token");
    } else {
      // 使用sessionStorage（会话级）
      sessionStorage.setItem("auth_token", authToken);
      sessionStorage.setItem("user", JSON.stringify(userData));
      if (refreshTokenValue) {
        sessionStorage.setItem("refresh_token", refreshTokenValue);
      }
      // 清除localStorage中的旧数据
      localStorage.removeItem("auth_token");
      localStorage.removeItem("user");
      localStorage.removeItem("refresh_token");
    }
  };

  const updateTokens = (newToken: string, newRefreshToken: string) => {
    token.value = newToken;
    refreshToken.value = newRefreshToken;
    const storage = localStorage.getItem("auth_token") ? localStorage : sessionStorage;
    storage.setItem("auth_token", newToken);
    storage.setItem("refresh_token", newRefreshToken);
  };

  const logout = () => {
    user.value = null;
    token.value = null;
    refreshToken.value = null;
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user");
    localStorage.removeItem("refresh_token");
    sessionStorage.removeItem("auth_token");
    sessionStorage.removeItem("user");
    sessionStorage.removeItem("refresh_token");
  };

  const loadUserFromStorage = () => {
    // 优先从localStorage读取，如果没有则从sessionStorage读取
    const storedUser = localStorage.getItem("user") || sessionStorage.getItem("user");
    // 如果 token 不存在但 user 还在（历史遗留/异常状态），直接清理，避免 UI 误判
    if (storedUser && !token.value) {
      localStorage.removeItem("user");
      sessionStorage.removeItem("user");
      user.value = null;
      return;
    }

    if (storedUser && token.value) {
      try {
        user.value = JSON.parse(storedUser);
      } catch (e) {
        console.error("Failed to parse user from storage", e);
        logout();
      }
    }
  };

  // 初始化时从存储加载用户
  if (token.value) {
    loadUserFromStorage();
  }

  return {
    user,
    token,
    refreshToken,
    isLoggedIn,
    login,
    updateTokens,
    logout,
    loadUserFromStorage,
  };
});

