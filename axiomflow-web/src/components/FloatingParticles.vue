<template>
  <div class="floating-particles-container">
    <div
      v-for="particle in particles"
      :key="particle.id"
      class="floating-particle"
      :style="{
        left: particle.left + '%',
        top: particle.top + '%',
        animationDelay: particle.delay + 's',
        animationDuration: particle.duration + 's',
        width: particle.size + 'px',
        height: particle.size + 'px',
        opacity: particle.opacity,
      }"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";

interface Particle {
  id: number;
  left: number;
  top: number;
  delay: number;
  duration: number;
  size: number;
  opacity: number;
}

const particles = ref<Particle[]>([]);
const PARTICLE_COUNT = 20; // 粒子数量

const generateParticles = () => {
  const newParticles: Particle[] = [];
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    // 左侧和右侧各一半
    const isLeft = i % 2 === 0;
    newParticles.push({
      id: i,
      left: isLeft ? 5 + Math.random() * 15 : 80 + Math.random() * 15, // 左侧 5-20%，右侧 80-95%
      top: Math.random() * 100, // 0-100% 随机垂直位置
      delay: Math.random() * 3, // 0-3秒延迟
      duration: 15 + Math.random() * 10, // 15-25秒动画时长
      size: 4 + Math.random() * 6, // 4-10px 大小
      opacity: 0.2 + Math.random() * 0.3, // 0.2-0.5 透明度
    });
  }
  particles.value = newParticles;
};

onMounted(() => {
  generateParticles();
});
</script>

<style scoped>
.floating-particles-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1; /* 在背景之上，但在内容之下 */
  overflow: hidden;
}

.floating-particle {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    rgba(99, 102, 241, 0.6) 0%,
    rgba(139, 92, 246, 0.4) 50%,
    transparent 100%
  );
  box-shadow: 
    0 0 10px rgba(99, 102, 241, 0.4),
    0 0 20px rgba(139, 92, 246, 0.2);
  animation: float-particle ease-in-out infinite;
  will-change: transform;
}

@keyframes float-particle {
  0%, 100% {
    transform: translateY(0) translateX(0) scale(1);
  }
  25% {
    transform: translateY(-30px) translateX(15px) scale(1.1);
  }
  50% {
    transform: translateY(-60px) translateX(-10px) scale(0.9);
  }
  75% {
    transform: translateY(-30px) translateX(10px) scale(1.05);
  }
}

/* 为不同位置的粒子添加不同的动画 */
.floating-particle:nth-child(odd) {
  animation-name: float-particle-reverse;
}

@keyframes float-particle-reverse {
  0%, 100% {
    transform: translateY(0) translateX(0) scale(1);
  }
  25% {
    transform: translateY(-40px) translateX(-20px) scale(0.95);
  }
  50% {
    transform: translateY(-50px) translateX(15px) scale(1.15);
  }
  75% {
    transform: translateY(-20px) translateX(-5px) scale(1.05);
  }
}
</style>

