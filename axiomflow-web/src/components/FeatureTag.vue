<template>
  <div 
    class="feature-tag-wrapper"
    @mouseenter="$emit('hover')"
    @mouseleave="$emit('unhover')"
  >
    <span 
      class="feature-tag" 
      tabindex="0"
      role="button"
      :aria-expanded="isHovered"
      :aria-label="$t(`landing.${labelKey}`)"
      :aria-describedby="isHovered ? `${id}-popover` : undefined"
      @keydown.enter.prevent="$emit('toggle')"
      @keydown.space.prevent="$emit('toggle')"
    >
      {{ $t(`landing.${labelKey}`) }}
    </span>
    <div 
      v-if="isHovered"
      :id="`${id}-popover`"
      class="feature-tag-popover"
      role="tooltip"
      @mouseenter="$emit('hover')"
      @mouseleave="$emit('unhover')"
    >
      <div class="feature-tag-popover-content">
        {{ $t(`landing.${descKey}`) }}
      </div>
      <div class="feature-tag-popover-arrow"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  id: string;
  labelKey: string;
  descKey: string;
  isHovered: boolean;
}>();

defineEmits<{
  hover: [];
  unhover: [];
  toggle: [];
}>();
</script>

