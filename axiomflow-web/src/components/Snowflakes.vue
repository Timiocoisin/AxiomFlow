<template>
  <div class="snowflakes-container">
    <div
      v-for="flake in snowflakes"
      :key="flake.id"
      class="snowflake"
      :style="{
        left: flake.left + '%',
        animationDelay: flake.delay + 's',
        animationDuration: flake.duration + 's',
        opacity: flake.opacity,
        '--scale': flake.scale,
      }"
    >
      <svg
        :width="flake.size"
        :height="flake.size"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M12 2V4M12 20V22M4 12H2M22 12H20M19.07 4.93L17.66 6.34M6.34 17.66L4.93 19.07M19.07 19.07L17.66 17.66M6.34 6.34L4.93 4.93M16 12C16 14.2091 14.2091 16 12 16C9.79086 16 8 14.2091 8 12C8 9.79086 9.79086 8 12 8C14.2091 8 16 9.79086 16 12Z"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";

interface Snowflake {
  id: number;
  left: number;
  delay: number;
  duration: number;
  opacity: number;
  scale: number;
  size: number;
}

const snowflakes = ref<Snowflake[]>([]);
const SNOWFLAKE_COUNT = 40; // 雪花数量，增加一些让效果更明显

const generateSnowflakes = () => {
  const flakes: Snowflake[] = [];
  for (let i = 0; i < SNOWFLAKE_COUNT; i++) {
    flakes.push({
      id: i,
      left: Math.random() * 100, // 0-100% 随机位置
      delay: Math.random() * 5, // 0-5秒延迟
      duration: 8 + Math.random() * 12, // 8-20秒下落时间
      opacity: 0.5 + Math.random() * 0.3, // 0.5-0.8 透明度，更明显
      scale: 0.4 + Math.random() * 0.6, // 0.4-1.0 缩放
      size: 12 + Math.random() * 16, // 12-28px 大小
    });
  }
  snowflakes.value = flakes;
};

onMounted(() => {
  generateSnowflakes();
});
</script>

<style scoped>
.snowflakes-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 5; /* 在背景之上，但在内容卡片之下 */
  overflow: hidden;
}

.snowflake {
  position: absolute;
  top: -50px;
  color: rgba(99, 102, 241, 0.7); /* 提高透明度，让雪花更明显 */
  will-change: transform;
  transform: scale(var(--scale, 1));
}

.snowflake svg {
  filter: drop-shadow(0 0 4px rgba(99, 102, 241, 0.5));
  display: block;
}

/* 使用单一动画，避免冲突 */
.snowflake {
  animation: snowfall linear infinite;
}

@keyframes snowfall {
  0% {
    transform: translateY(0) translateX(0) rotate(0deg) scale(var(--scale, 1));
  }
  100% {
    transform: translateY(calc(100vh + 100px)) translateX(50px) rotate(360deg) scale(var(--scale, 1));
  }
}

/* 为不同位置的雪花添加不同的摆动 */
.snowflake:nth-child(3n) {
  animation: snowfall-1 linear infinite;
}

.snowflake:nth-child(3n + 1) {
  animation: snowfall-2 linear infinite;
}

.snowflake:nth-child(3n + 2) {
  animation: snowfall-3 linear infinite;
}

@keyframes snowfall-1 {
  0% {
    transform: translateY(0) translateX(0) rotate(0deg) scale(var(--scale, 1));
  }
  100% {
    transform: translateY(calc(100vh + 100px)) translateX(40px) rotate(360deg) scale(var(--scale, 1));
  }
}

@keyframes snowfall-2 {
  0% {
    transform: translateY(0) translateX(0) rotate(0deg) scale(var(--scale, 1));
  }
  100% {
    transform: translateY(calc(100vh + 100px)) translateX(-30px) rotate(-360deg) scale(var(--scale, 1));
  }
}

@keyframes snowfall-3 {
  0% {
    transform: translateY(0) translateX(0) rotate(0deg) scale(var(--scale, 1));
  }
  100% {
    transform: translateY(calc(100vh + 100px)) translateX(60px) rotate(360deg) scale(var(--scale, 1));
  }
}
</style>

