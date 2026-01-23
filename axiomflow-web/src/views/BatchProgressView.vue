<template>
  <section class="glass-card" style="padding: 18px">
    <div style="display:flex;justify-content:space-between;align-items:center;gap:12px">
      <div>
        <h2 style="margin:0">批次进度</h2>
        <div style="color:#9ca3af;font-size:12px;margin-top:6px">batch_id: {{ batchId }}</div>
      </div>
      <AppButton @click="refresh">刷新</AppButton>
    </div>

    <div v-if="loading" style="color:#9ca3af;margin-top:14px">加载中…</div>
    <div v-else-if="error" style="color:#fb7185;margin-top:14px">{{ error }}</div>
    <div v-else style="margin-top:14px">
      <div style="display:grid;gap:10px">
        <div
          v-for="it in items"
          :key="it.document_id"
          class="glass-card"
          style="padding:12px;display:flex;justify-content:space-between;align-items:center;gap:12px"
        >
          <div style="min-width:0">
            <div style="font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
              {{ it.title || it.document_id }}
            </div>
            <div style="color:#9ca3af;font-size:12px;margin-top:4px">
              {{ it.job?.stage || "pending" }} · {{ Math.round((it.job?.progress || 0) * 100) }}%
            </div>
          </div>
          <div style="display:flex;gap:10px;align-items:center">
            <AppButton primary @click="openDoc(it.document_id)">打开</AppButton>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import AppButton from "@/components/AppButton.vue";
import { getBatch } from "@/lib/api";

const route = useRoute();
const router = useRouter();
const batchId = computed(() => String(route.params.id || ""));

const loading = ref(true);
const error = ref<string | null>(null);
const items = ref<any[]>([]);
let timer: any = null;

const refresh = async () => {
  loading.value = true;
  error.value = null;
  try {
    const b = await getBatch({ batch_id: batchId.value });
    items.value = b.items ?? [];
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
};

const openDoc = (document_id: string) => {
  router.push(`/project/${document_id}`);
};

onMounted(async () => {
  await refresh();
  timer = setInterval(refresh, 1500);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>


