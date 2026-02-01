import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import LandingView from "@/views/LandingView.vue";
import DashboardView from "@/views/DashboardView.vue";
import ProjectWorkbenchView from "@/views/ProjectWorkbenchView.vue";
import SettingsView from "@/views/SettingsView.vue";
import BatchProgressView from "@/views/BatchProgressView.vue";
import AuthView from "@/views/AuthView.vue";
import VerifyEmailView from "@/views/VerifyEmailView.vue";
import { updatePageMeta, getPageMeta } from "@/utils/meta";

const routes: RouteRecordRaw[] = [
  { path: "/", name: "landing", component: LandingView },
  { path: "/auth", name: "auth", component: AuthView },
  { path: "/auth/verify-email", name: "verify-email", component: VerifyEmailView },
  { path: "/app", name: "dashboard", component: DashboardView },
  { path: "/batch/:id", name: "batch", component: BatchProgressView, props: true },
  {
    path: "/project/:id",
    name: "project",
    component: ProjectWorkbenchView,
  },
  { path: "/settings", name: "settings", component: SettingsView },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 路由切换时聚焦主内容和更新元标签（可访问性改进）
router.afterEach((to, from) => {
  // 更新页面元标签
  const meta = getPageMeta(to.name as string, to.params);
  updatePageMeta(meta.title, meta.description);
  
  // 延迟执行以确保DOM已更新
  setTimeout(() => {
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
      mainContent.focus();
      // 滚动到顶部（如果不在首页）
      if (to.path !== '/') {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }
  }, 100);
});


