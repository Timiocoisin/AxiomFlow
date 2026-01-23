import { defineStore } from "pinia";
import { ref, computed } from "vue";

export interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
  provider?: "email" | "google" | "github";
  email_verified?: boolean;
}

export const useUserStore = defineStore("user", () => {
  const user = ref<User | null>(null);
  // 优先从localStorage读取，如果没有则从sessionStorage读取
  const token = ref<string | null>(
    localStorage.getItem("auth_token") || sessionStorage.getItem("auth_token")
  );

  const isLoggedIn = computed(() => !!user.value && !!token.value);

  const login = (userData: User, authToken: string, rememberMe: boolean = true) => {
    user.value = userData;
    token.value = authToken;
    
    if (rememberMe) {
      // 使用localStorage（持久化）
      localStorage.setItem("auth_token", authToken);
      localStorage.setItem("user", JSON.stringify(userData));
      // 清除sessionStorage中的旧数据
      sessionStorage.removeItem("auth_token");
      sessionStorage.removeItem("user");
    } else {
      // 使用sessionStorage（会话级）
      sessionStorage.setItem("auth_token", authToken);
      sessionStorage.setItem("user", JSON.stringify(userData));
      // 清除localStorage中的旧数据
      localStorage.removeItem("auth_token");
      localStorage.removeItem("user");
    }
  };

  const logout = () => {
    user.value = null;
    token.value = null;
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user");
    sessionStorage.removeItem("auth_token");
    sessionStorage.removeItem("user");
  };

  const setEmailVerified = (verified: boolean) => {
    if (!user.value) return;
    user.value = {
      ...user.value,
      email_verified: verified,
    };
    const serialized = JSON.stringify(user.value);
    if (localStorage.getItem("auth_token")) {
      localStorage.setItem("user", serialized);
    } else if (sessionStorage.getItem("auth_token")) {
      sessionStorage.setItem("user", serialized);
    }
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
    isLoggedIn,
    login,
    logout,
    loadUserFromStorage,
    setEmailVerified,
  };
});

