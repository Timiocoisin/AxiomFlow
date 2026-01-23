import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import { router } from "./router";

import "./styles.css";

const app = createApp(App);

// 全局错误兜底：避免页面“白屏”但控制台才有报错的情况
app.config.errorHandler = (err, instance, info) => {
  // eslint-disable-next-line no-console
  console.error("[VueError]", info, err);
  try {
    const message = err instanceof Error ? err.message : String(err);
    const event = new CustomEvent("show-toast", {
      detail: { type: "error", title: "前端运行错误", message },
    });
    window.dispatchEvent(event);
  } catch {
    // ignore
  }
};

app.use(createPinia());
app.use(router);

app.mount("#app");


