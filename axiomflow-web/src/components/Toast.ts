export type ToastType = "success" | "error" | "warning" | "info";

/**
 * 全局 Toast 帮助函数
 * 依赖 Toast.vue 中在 window 上挂载的 showToast
 */
export function showToast(type: ToastType, title: string, message?: string) {
  const anyWindow = window as any;
  const impl = anyWindow.showToast;
  if (typeof impl === "function") {
    impl({
      type,
      title,
      message,
    });
  } else {
    // 在极早期还未挂载 Toast 组件时的兜底：直接用 alert
    if (type === "error") {
      // eslint-disable-next-line no-alert
      alert(`${title}${message ? "：\n" + message : ""}`);
    } else {
      // 静默失败避免打断流程
      // console.warn("showToast is not ready yet");
    }
  }
}


