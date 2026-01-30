<template>
  <div 
    class="theme-toggle-container"
    :style="{ fontSize: `${size / 3}px` }"
  >
    <div 
      class="components"
      :style="componentsStyle"
      @click="handleClick"
      @mouseenter="handleMouseEnter"
      @mouseleave="handleMouseLeave"
    >
      <div 
        class="main-button"
        :style="mainButtonStyle"
        @mousemove="handleMainButtonMouseMove"
      >
        <div 
          v-for="i in 3" 
          :key="i"
          class="moon"
          :style="getMoonStyle(i)"
        ></div>
      </div>
      <div 
        v-for="i in 3" 
        :key="`bg-${i}`"
        class="daytime-background"
        :style="getDaytimeBackgroundStyle(i)"
      ></div>
      <div class="cloud" :style="cloudStyle">
        <div 
          v-for="i in 6" 
          :key="`cloud-${i}`"
          class="cloud-son"
          :style="getCloudSonStyle(i, false)"
        ></div>
      </div>
      <div class="cloud-light" :style="cloudLightStyle">
        <div 
          v-for="i in 6" 
          :key="`cloud-light-${i}`"
          class="cloud-son"
          :style="getCloudSonStyle(i, true)"
        ></div>
      </div>
      <div class="stars" :style="starsStyle">
        <div 
          v-for="(star, index) in starConfigs" 
          :key="`star-${index}`"
          class="star"
          :class="star.size"
          :style="getStarStyle(index)"
        >
          <div 
            v-for="j in 4" 
            :key="`star-son-${index}-${j}`"
            class="star-son"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';

interface Props {
  modelValue?: 'light' | 'dark';
  size?: number;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: 'light',
  size: 3,
});

const emit = defineEmits<{
  'update:modelValue': [value: 'light' | 'dark'];
  'change': [value: 'light' | 'dark'];
}>();

const isMoved = ref(props.modelValue === 'dark');
const isClicked = ref(false);
const isHovering = ref(false);

// 云朵随机移动
const cloudTransforms = ref<Record<string, string>>({});
let cloudInterval: number | null = null;

const starConfigs = [
  { size: 'big', top: '11em', left: '39em', duration: '3.5s' },
  { size: 'big', top: '39em', left: '91em', duration: '4.1s' },
  { size: 'medium', top: '26em', left: '19em', duration: '4.9s' },
  { size: 'medium', top: '37em', left: '66em', duration: '5.3s' },
  { size: 'small', top: '21em', left: '75em', duration: '3s' },
  { size: 'small', top: '51em', left: '38em', duration: '2.2s' },
];

// 组件样式
const componentsStyle = computed(() => ({
  backgroundColor: isMoved.value ? 'rgba(25,30,50,1)' : 'rgba(70, 133, 192,1)',
}));

// 主按钮样式
const mainButtonStyle = computed(() => {
  if (isMoved.value) {
    return {
      transform: isHovering.value ? 'translateX(100em)' : 'translateX(110em)',
      backgroundColor: 'rgba(195, 200,210,1)',
      boxShadow: '3em 3em 5em rgba(0, 0, 0, 0.5), inset  -3em -5em 3em -3em rgba(0, 0, 0, 0.5), inset  4em 5em 2em -2em rgba(255, 255, 210,1)',
    };
  } else {
    return {
      transform: isHovering.value ? 'translateX(10em)' : 'translateX(0)',
      backgroundColor: 'rgba(255, 195, 35,1)',
      boxShadow: '3em 3em 5em rgba(0, 0, 0, 0.5), inset  -3em -5em 3em -3em rgba(0, 0, 0, 0.5), inset  4em 5em 2em -2em rgba(255, 230, 80,1)',
    };
  }
});

// 月亮样式
const getMoonStyle = (index: number) => {
  const positions = [
    { top: '7.5em', left: '25em', width: '12.5em', height: '12.5em' },
    { top: '20em', left: '7.5em', width: '20em', height: '20em' },
    { top: '32.5em', left: '32.5em', width: '12.5em', height: '12.5em' },
  ];
  return {
    ...positions[index - 1],
    opacity: isMoved.value ? '1' : '0',
  };
};

// 白天背景样式
const getDaytimeBackgroundStyle = (index: number) => {
  const positions = [
    { top: '-20em', left: '-20em', width: '110em', height: '110em', bg: 'rgba(255, 255, 255,0.2)' },
    { top: '-32.5em', left: '-17.5em', width: '135em', height: '135em', bg: 'rgba(255, 255, 255,0.1)' },
    { top: '-45em', left: '-15em', width: '160em', height: '160em', bg: 'rgba(255, 255, 255,0.05)' },
  ];
  const pos = positions[index - 1];
  const translateX = isMoved.value 
    ? (isHovering.value ? ['100em', '73em', '46em'] : ['110em', '80em', '50em'])[index - 1]
    : (isHovering.value ? '10em' : '0');
  
  return {
    ...pos,
    backgroundColor: pos.bg,
    transform: `translateX(${translateX})`,
  };
};

// 云朵样式
const cloudStyle = computed(() => ({
  transform: isMoved.value ? 'translateY(80em)' : 'translateY(10em)',
}));

const cloudLightStyle = computed(() => ({
  transform: isMoved.value ? 'translateY(80em)' : 'translateY(10em)',
}));

// 云朵子元素样式
const getCloudSonStyle = (index: number, isLight: boolean) => {
  const basePositions = [
    { right: '-20em', bottom: '10em', width: '50em', height: '50em' },
    { right: '-10em', bottom: '-25em', width: '60em', height: '60em' },
    { right: '20em', bottom: '-40em', width: '60em', height: '60em' },
    { right: '50em', bottom: '-35em', width: '60em', height: '60em' },
    { right: '75em', bottom: '-60em', width: '75em', height: '75em' },
    { right: '110em', bottom: '-50em', width: '60em', height: '60em' },
  ];
  
  const base = basePositions[(index - 1) % 6];
  const key = `${isLight ? 'light-' : ''}cloud-${index}`;
  const transform = cloudTransforms.value[key] || '';
  
  if (isHovering.value && !isMoved.value) {
    // 浅色模式悬停时的云朵位置
    const hoverPositions = [
      { right: '-24em', bottom: '10em' },
      { right: '-12em', bottom: '-27em' },
      { right: '17em', bottom: '-43em' },
      { right: '46em', bottom: '-39em' },
      { right: '70em', bottom: '-65em' },
      { right: '109em', bottom: '-54em' },
    ];
    const hoverPos = hoverPositions[(index - 1) % 6];
    return {
      ...base,
      ...hoverPos,
      transform,
    };
  }
  
  return {
    ...base,
    transform,
  };
};

// 星星样式
const starsStyle = computed(() => ({
  transform: isMoved.value ? 'translateY(-62.5em)' : 'translateY(-125em)',
  opacity: isMoved.value ? '1' : '0',
}));

const getStarStyle = (index: number) => {
  const config = starConfigs[index];
  let top = config.top;
  let left = config.left;
  
  if (isHovering.value && isMoved.value) {
    // 深色模式悬停时的星星位置
    const hoverPositions = [
      { top: '10em', left: '36em' },
      { top: '40em', left: '87em' },
      { top: '26em', left: '16em' },
      { top: '38em', left: '63em' },
      { top: '20.5em', left: '72em' },
      { top: '51.5em', left: '35em' },
    ];
    if (hoverPositions[index]) {
      top = hoverPositions[index].top;
      left = hoverPositions[index].left;
    }
  }
  
  return {
    top,
    left,
    animationName: 'star',
    animationDuration: config.duration,
  };
};

// 点击处理
const handleClick = () => {
  isMoved.value = !isMoved.value;
  isClicked.value = true;
  
  const newTheme = isMoved.value ? 'dark' : 'light';
  emit('update:modelValue', newTheme);
  emit('change', newTheme);
  
  setTimeout(() => {
    isClicked.value = false;
  }, 500);
};

// 鼠标进入
const handleMouseEnter = () => {
  if (!isClicked.value) {
    isHovering.value = true;
  }
};

// 鼠标离开
const handleMouseLeave = () => {
  if (!isClicked.value) {
    isHovering.value = false;
  }
};

// 主按钮鼠标移动（用于更精细的交互）
const handleMainButtonMouseMove = () => {
  // 可以在这里添加额外的交互效果
};

// 云朵随机移动
const moveElementRandomly = (key: string) => {
  const directions = ['2em', '-2em'];
  const randomX = directions[Math.floor(Math.random() * directions.length)];
  const randomY = directions[Math.floor(Math.random() * directions.length)];
  cloudTransforms.value[key] = `translate(${randomX}, ${randomY})`;
};

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  isMoved.value = newValue === 'dark';
});

onMounted(() => {
  // 初始化云朵位置
  for (let i = 1; i <= 6; i++) {
    moveElementRandomly(`cloud-${i}`);
    moveElementRandomly(`light-cloud-${i}`);
  }
  
  // 设置云朵随机移动
  cloudInterval = window.setInterval(() => {
    for (let i = 1; i <= 6; i++) {
      moveElementRandomly(`cloud-${i}`);
      moveElementRandomly(`light-cloud-${i}`);
    }
  }, 1000);
  
  // 根据初始值设置状态
  isMoved.value = props.modelValue === 'dark';
});

onUnmounted(() => {
  if (cloudInterval !== null) {
    clearInterval(cloudInterval);
  }
});
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  transition: 0.7s;
  -webkit-tap-highlight-color: rgba(0, 0, 0, 0);
}

.theme-toggle-container {
  position: relative;
  display: inline-block;
  vertical-align: bottom;
  transform: translate3d(0, 0, 0);
  width: 180em;
  height: 70em;
}

.components {
  position: relative;
  width: 180em;
  height: 70em;
  border-radius: 100em;
  box-shadow: inset 0 0 5em 3em rgba(0, 0, 0, 0.5);
  overflow: hidden;
  transition: 0.7s;
  transition-timing-function: cubic-bezier(0, 0.5, 1, 1);
  cursor: pointer;
}

.main-button {
  margin: 7.5em 0 0 7.5em;
  width: 55em;
  height: 55em;
  border-radius: 50%;
  transition: 1.0s;
  transition-timing-function: cubic-bezier(0.56, 1.35, 0.52, 1.00);
}

.moon {
  position: absolute;
  background-color: rgba(150, 160, 180, 1);
  box-shadow: inset 0em 0em 1em 1em rgba(0, 0, 0, 0.3);
  border-radius: 50%;
  transition: 0.5s;
}

.daytime-background {
  position: absolute;
  border-radius: 50%;
  transition: 1.0s;
  transition-timing-function: cubic-bezier(0.56, 1.35, 0.52, 1.00);
}

.daytime-background:nth-child(2) {
  z-index: -2;
}

.daytime-background:nth-child(3) {
  z-index: -3;
}

.daytime-background:nth-child(4) {
  z-index: -4;
}

.cloud,
.cloud-light {
  transition: 1.0s;
  transition-timing-function: cubic-bezier(0.56, 1.35, 0.52, 1.00);
}

.cloud {
  z-index: -2;
}

.cloud-light {
  position: absolute;
  right: 0em;
  bottom: 25em;
  opacity: 0.5;
  z-index: -3;
}

.cloud-son {
  position: absolute;
  background-color: #fff;
  border-radius: 50%;
  z-index: -1;
  transition: transform 6s, right 1s, bottom 1s;
}

.stars {
  z-index: -2;
  transition: 1.0s;
  transition-timing-function: cubic-bezier(0.56, 1.35, 0.52, 1.00);
}

.big {
  --size: 7.5em;
}

.medium {
  --size: 5em;
}

.small {
  --size: 3em;
}

.star {
  position: absolute;
  width: calc(2 * var(--size));
  height: calc(2 * var(--size));
  transform: scale(1);
  transition-timing-function: cubic-bezier(0.56, 1.35, 0.52, 1.00);
  transition: 1s;
  animation-iteration-count: infinite;
  animation-direction: alternate;
  animation-timing-function: linear;
}

@keyframes star {
  0%,
  20% {
    transform: scale(0);
  }
  20%,
  100% {
    transform: scale(1);
  }
}

.star-son {
  float: left;
}

.star-son:nth-child(1) {
  --pos: left 0;
}

.star-son:nth-child(2) {
  --pos: right 0;
}

.star-son:nth-child(3) {
  --pos: 0 bottom;
}

.star-son:nth-child(4) {
  --pos: right bottom;
}

.star-son {
  width: var(--size);
  height: var(--size);
  background-image: radial-gradient(
    circle var(--size) at var(--pos),
    transparent var(--size),
    #fff
  );
}
</style>

