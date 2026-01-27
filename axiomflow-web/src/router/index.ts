import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import LandingView from "@/views/LandingView.vue";
import DashboardView from "@/views/DashboardView.vue";
import ProjectWorkbenchView from "@/views/ProjectWorkbenchView.vue";
import SettingsView from "@/views/SettingsView.vue";
import BatchProgressView from "@/views/BatchProgressView.vue";
import AuthView from "@/views/AuthView.vue";

const routes: RouteRecordRaw[] = [
  { path: "/", name: "landing", component: LandingView },
  { path: "/auth", name: "auth", component: AuthView },
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


