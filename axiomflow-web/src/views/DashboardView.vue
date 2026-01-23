<template>
  <section class="dashboard">
    <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px">
      <h2 style="margin: 0">我的文档</h2>
      <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap">
        <input
          class="simple-input"
          v-model="projectName"
          placeholder="项目名（可选）"
          style="width: 220px"
        />
        <AppButton primary @click="pickFile">上传PDF（单个）</AppButton>
        <AppButton @click="pickFiles">批量上传PDF</AppButton>
        <input ref="fileInput" type="file" accept="application/pdf" style="display: none" @change="onFileChange" />
        <input ref="filesInput" type="file" accept="application/pdf" multiple style="display: none" @change="onFilesChange" />
      </div>
    </div>
    <div class="card-grid" v-if="docs.length > 0">
      <AppCard
        v-for="d in docs"
        :key="d.document_id"
        class="doc-card"
        :class="{ 'doc-card--parsing': d.status === 'parsing', 'doc-card--ready': d.status === 'ready' }"
        @click="d.status === 'ready' ? openDoc(d.document_id) : undefined"
      >
        <div class="doc-header">
          <div class="doc-icon" :class="{ 'doc-icon--parsing': d.status === 'parsing' }">
            {{ d.status === 'parsing' ? '⏳' : '📄' }}
          </div>
          <div class="doc-info">
            <div class="doc-title" :class="{ 'doc-title--disabled': d.status === 'parsing' }">
              {{ d.title }}
            </div>
            <div class="doc-meta">
              <span v-if="d.status === 'uploading'">
                正在上传中...
              </span>
              <span v-else-if="d.status === 'parsing'">
                <span v-if="d.num_pages && d.num_pages > 0">{{ d.num_pages }} 页 · </span>解析中...
              </span>
              <span v-else>
                {{ d.num_pages || '?' }} 页 · {{ d.lang_in }} → {{ d.lang_out }} · 已解析
              </span>
            </div>
          </div>
        </div>
        <div v-if="d.status === 'uploading' || d.status === 'parsing'" class="doc-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${d.progress || 0}%` }"></div>
          </div>
          <div class="progress-text">
            <span v-if="d.status === 'uploading'">上传中...</span>
            <span v-else-if="d.status === 'parsing'">解析中... {{ d.progress || 0 }}%</span>
          </div>
        </div>
        <div v-else class="doc-status-badge">
          <span class="status-dot status-dot--ready"></span>
          <span>解析完成</span>
        </div>
      </AppCard>
    </div>
    <div v-else class="empty-state">
      <div class="empty-state-content">
        <div class="empty-state-icon">
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 14C18 12.8954 18.8954 12 20 12H44C45.1046 12 46 12.8954 46 14V42C46 43.1046 45.1046 44 44 44H20C18.8954 44 18 43.1046 18 42V14Z" stroke="url(#emptyGradient)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            <path d="M22 20H42M22 26H36M22 32H42" stroke="url(#emptyGradient)" stroke-width="2.5" stroke-linecap="round"/>
            <path d="M22 38H36" stroke="url(#emptyGradient)" stroke-width="2.5" stroke-linecap="round" opacity="0.6"/>
            <circle cx="50" cy="18" r="3" fill="url(#emptyGradient)" opacity="0.8"/>
            <defs>
              <linearGradient id="emptyGradient" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stop-color="#3b82f6"/>
                <stop offset="100%" stop-color="#8b5cf6"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h3 class="empty-state-title">暂无文档</h3>
        <p class="empty-state-description">开始上传您的第一个 PDF 文档，让我们帮您解析和翻译</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref, watch, onUnmounted } from "vue";
import AppCard from "@/components/AppCard.vue";
import AppButton from "@/components/AppButton.vue";
import { batchUpload, createProject, uploadPdf, getDocument, getProjectDocuments } from "@/lib/api";
import { useRouter, useRoute } from "vue-router";
import { DocumentProgressWebSocket } from "@/lib/websocket";

const router = useRouter();
const route = useRoute();

type DocStatus = "uploading" | "parsing" | "ready";

interface Doc {
  document_id: string;
  title: string;
  num_pages?: number;
  lang_in: string;
  lang_out: string;
  status: DocStatus;
  progress: number;
}

const docs = ref<Doc[]>([]);
const fileInput = ref<HTMLInputElement | null>(null);
const filesInput = ref<HTMLInputElement | null>(null);
const projectName = ref("我的项目");
const currentProjectId = ref<string | null>(null); // 当前项目ID
const activeWebSockets = new Map<string, DocumentProgressWebSocket>(); // document_id -> WebSocket

// 从 API 加载项目文档列表
const loadProjectDocuments = async (project_id: string) => {
  try {
    const response = await getProjectDocuments(project_id);
    // 将 API 返回的文档转换为前端格式
    docs.value = response.documents.map((d) => ({
      document_id: d.document_id,
      title: d.title,
      num_pages: d.num_pages,
      lang_in: d.lang_in,
      lang_out: d.lang_out,
      status: d.status === "parsed" ? "ready" : (d.status === "parsing" ? "parsing" : "ready") as DocStatus,
      progress: d.status === "parsed" ? 100 : 0,
    }));
    currentProjectId.value = project_id;
  } catch (error) {
    console.error("加载文档列表失败:", error);
    // 如果项目不存在或加载失败，清空列表
    docs.value = [];
  }
};

const pickFile = () => fileInput.value?.click();
const pickFiles = () => filesInput.value?.click();

const onFileChange = async (e: Event) => {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  // 立即添加到列表
  const tempDoc: Doc = {
    document_id: `temp-${Date.now()}`,
    title: file.name,
    lang_in: "en",
    lang_out: "zh",
    status: "uploading",
    progress: 0,
  };
  docs.value.unshift(tempDoc);

  try {
    // 如果没有当前项目，创建新项目
    let project_id = currentProjectId.value;
    if (!project_id) {
      const projectRes = await createProject(projectName.value || "我的项目");
      project_id = projectRes.project_id;
      currentProjectId.value = project_id;
    }
    
    const res = await uploadPdf({ project_id, file, lang_in: "en", lang_out: "zh" });
    
    // 更新文档ID（WebSocket 会发送真实进度）
    tempDoc.document_id = res.document_id;
    tempDoc.num_pages = res.num_pages;
    
    // 记录开始时间，用于平滑进度显示
    const startTime = Date.now();
    const minDisplayTime = 2000;
    const finalProjectId = project_id; // 保存到外部作用域
    
    // 平滑进度动画函数
    const smoothProgress = (targetProgress: number, currentProgress: number) => {
      const diff = targetProgress - currentProgress;
      if (Math.abs(diff) < 1) return targetProgress;
      return currentProgress + Math.sign(diff) * Math.min(Math.abs(diff), 5);
    };
    
    // 使用 WebSocket 接收实时进度更新
    const ws = new DocumentProgressWebSocket(res.document_id);
    activeWebSockets.set(res.document_id, ws);
    
    ws.onMessage(async (data) => {
      const elapsed = Date.now() - startTime;
      
      // 根据状态更新进度
      if (data.status === "uploading") {
        tempDoc.status = "uploading";
        const targetProgress = Math.min(data.parse_progress || tempDoc.progress, 30);
        tempDoc.progress = smoothProgress(targetProgress, tempDoc.progress);
      } else if (data.status === "parsing") {
        tempDoc.status = "parsing";
        
        // 如果有parse_job，使用真实的进度（done/total）
        let targetProgress = 30;
        if (data.parse_job) {
          const parseJob = data.parse_job;
          if (parseJob.total && parseJob.total > 0) {
            const parseProgress = (parseJob.done || 0) / parseJob.total;
            targetProgress = 30 + parseProgress * 70; // 30-100%
          } else {
            targetProgress = 30 + (parseJob.progress || 0) * 70;
          }
        } else {
          targetProgress = Math.min(data.parse_progress || 30, 90);
        }
        tempDoc.progress = smoothProgress(targetProgress, tempDoc.progress);
      } else if (data.status === "parsed") {
        console.log(`解析完成 (${res.document_id}): num_pages=${data.num_pages}, elapsed=${elapsed}ms`);
        // 解析完成，平滑过渡到100%
        tempDoc.status = "parsing";
        
        if (tempDoc.progress < 100) {
          tempDoc.progress = smoothProgress(100, tempDoc.progress);
        } else {
          tempDoc.progress = 100;
        }
        
        // 如果 num_pages > 0，立即更新为 ready
        if (data.num_pages > 0) {
          tempDoc.status = "ready";
          tempDoc.num_pages = data.num_pages;
          ws.disconnect();
          activeWebSockets.delete(res.document_id);
          // 重新加载项目文档列表以获取最新状态
          if (finalProjectId) await loadProjectDocuments(finalProjectId);
        } else if (tempDoc.progress >= 100 && elapsed >= minDisplayTime) {
          // 如果没有 num_pages，等待 minDisplayTime 后再更新
          tempDoc.status = "ready";
          tempDoc.num_pages = data.num_pages || 0;
          ws.disconnect();
          activeWebSockets.delete(res.document_id);
          // 重新加载项目文档列表以获取最新状态
          if (finalProjectId) await loadProjectDocuments(finalProjectId);
        }
      }
    });
    
    ws.onError((error) => {
      console.error("WebSocket 错误:", error);
      tempDoc.status = "parsing";
      tempDoc.progress = 50;
    });
    
    ws.onClose(() => {
      activeWebSockets.delete(res.document_id);
    });
    
    // 连接 WebSocket
    ws.connect().catch((error) => {
      console.error("WebSocket 连接失败:", error);
      tempDoc.status = "parsing";
      tempDoc.progress = 50;
    });
    
  } catch (error) {
    console.error("Upload failed:", error);
    docs.value = docs.value.filter((d) => d.document_id !== tempDoc.document_id);
  }
  
  input.value = "";
};

const onFilesChange = async (e: Event) => {
  const input = e.target as HTMLInputElement;
  const files = Array.from(input.files ?? []);
  if (files.length === 0) return;

  // 立即添加所有文件到列表
  const tempDocs: Doc[] = files.map((file, idx) => ({
    document_id: `temp-${Date.now()}-${idx}`,
    title: file.name,
    lang_in: "en",
    lang_out: "zh",
    status: "uploading" as DocStatus,
    progress: 0,
  }));
  docs.value.unshift(...tempDocs);

  // 模拟批量上传进度
  const progressIntervals = tempDocs.map((doc) => {
    return setInterval(() => {
      if (doc.progress < 40) {
        doc.progress += 5;
      }
    }, 150);
  });

  try {
    const res = await batchUpload({ project_name: projectName.value || "批量项目", files, lang_in: "en", lang_out: "zh" });
    
    // 清除进度模拟
    progressIntervals.forEach(clearInterval);
    
    // 更新临时文档为实际文档
    res.documents?.forEach((d, idx) => {
      if (tempDocs[idx]) {
        tempDocs[idx].document_id = d.document_id;
        tempDocs[idx].num_pages = d.num_pages;
        tempDocs[idx].status = "ready";
        tempDocs[idx].progress = 100;
      }
    });
    
    // 重新加载项目文档列表
    if (currentProjectId.value) await loadProjectDocuments(currentProjectId.value);
    // 批量上传默认自动翻译，跳转到批次进度面板
    router.push(`/batch/${res.batch_id}`);
  } catch (error) {
    console.error("Batch upload failed:", error);
    progressIntervals.forEach(clearInterval);
    // 移除失败的文档
    tempDocs.forEach((doc) => {
      docs.value = docs.value.filter((d) => d.document_id !== doc.document_id);
    });
  }
  
  input.value = "";
};

const openDoc = (document_id: string) => {
  router.push(`/project/${document_id}`);
};

// Demo functionality removed - would cause 404 errors
// const openDemo = () => router.push("/project/demo");

const handlePendingUpload = async () => {
  const isUploading = route.query.uploading === "true";
  const filename = route.query.filename as string | undefined;
  
  if (!isUploading || !filename) return;
  
  // 检查是否有待上传的文件
  const pendingFile = (window as any).__pendingUploadFile as File | undefined;
  if (!pendingFile) {
    // 如果没有文件，清除参数
    router.replace('/app');
    return;
  }
  
  const decodedFilename = decodeURIComponent(filename);
  
  // 立即显示上传中的文档卡片
  const uploadingDoc: Doc = {
    document_id: `temp-${Date.now()}`,
    title: decodedFilename,
    lang_in: "en",
    lang_out: "zh",
    status: "uploading",
    progress: 0,
  };
  docs.value.unshift(uploadingDoc);
  console.log(`[上传] 创建文档卡片: ${uploadingDoc.document_id}, 初始进度: ${uploadingDoc.progress}%`);
  
  try {
    // 开始实际上传
    const { project_id } = await createProject("我的项目");
    const res = await uploadPdf({ project_id, file: pendingFile, lang_in: "en", lang_out: "zh" });
    
    // 更新文档ID（WebSocket 会发送真实进度）
    const docIndex = docs.value.findIndex(d => d.document_id === uploadingDoc.document_id);
    if (docIndex >= 0) {
      docs.value[docIndex] = {
        ...docs.value[docIndex],
        document_id: res.document_id,
        num_pages: res.num_pages,
      };
    }
    
    // 清除临时文件引用
    delete (window as any).__pendingUploadFile;
    
    // 更新 URL，添加 document_id
    router.replace({ query: { document_id: res.document_id, uploading: "true", filename } });
    
    // 记录开始时间，用于平滑进度显示
    const startTime = Date.now();
    const minDisplayTime = 2000; // 最少显示2秒，让用户看到进度
    
    // 平滑进度动画函数 - 使用更智能的步长算法
    const smoothProgress = (targetProgress: number, currentProgress: number) => {
      const diff = targetProgress - currentProgress;
      if (Math.abs(diff) < 0.5) return targetProgress;
      
      // 根据距离目标的远近调整步长：
      // - 距离远时（>20%），步长较大（10%），快速接近
      // - 距离中等时（5-20%），步长中等（5%）
      // - 距离近时（<5%），步长较小（2%），精确到达
      let stepSize: number;
      const absDiff = Math.abs(diff);
      if (absDiff > 20) {
        stepSize = 10; // 快速接近
      } else if (absDiff > 5) {
        stepSize = 5; // 中等速度
      } else {
        stepSize = 2; // 精确到达
      }
      
      return currentProgress + Math.sign(diff) * Math.min(absDiff, stepSize);
    };
    
    // 使用 WebSocket 接收实时进度更新
    const ws = new DocumentProgressWebSocket(res.document_id);
    activeWebSockets.set(res.document_id, ws);
    
    ws.onMessage((data) => {
      console.log(`收到进度更新 (${res.document_id}):`, data);
      const elapsed = Date.now() - startTime;
      
      // 找到文档在数组中的索引
      const docIndex = docs.value.findIndex(d => d.document_id === res.document_id);
      if (docIndex < 0) {
        console.warn(`文档 ${res.document_id} 不在列表中`);
        return;
      }
      
      const currentDoc = docs.value[docIndex];
      
      // 根据状态更新进度
      if (data.status === "uploading") {
        const targetProgress = Math.min(data.parse_progress || currentDoc.progress, 30);
        const newProgress = smoothProgress(targetProgress, currentDoc.progress);
        docs.value[docIndex] = {
          ...currentDoc,
          status: "uploading",
          progress: newProgress,
        };
        console.log(`[上传中] 目标进度: ${targetProgress}%, 当前进度: ${newProgress}%`);
      } else if (data.status === "parsing") {
        // 立即更新状态为 parsing（从 uploading 切换）
        
        // 如果有parse_job，使用真实的进度（done/total）
        let targetProgress = 30;
        if (data.parse_job) {
          const parseJob = data.parse_job;
          if (parseJob.total && parseJob.total > 0) {
            // 使用真实的进度：30% (上传) + 70% * (done/total) (解析)
            const parseProgress = (parseJob.done || 0) / parseJob.total;
            targetProgress = 30 + parseProgress * 70; // 30-100%
            console.log(`[解析中] 使用 Job 进度: ${parseJob.done}/${parseJob.total} = ${parseProgress}, 目标进度: ${targetProgress}%`);
          } else {
            // 没有total，使用progress字段（0-1范围）
            targetProgress = 30 + (parseJob.progress || 0) * 70;
            console.log(`[解析中] 使用 Job progress 字段: ${parseJob.progress}, 目标进度: ${targetProgress}%`);
          }
        } else if (data.parse_progress !== undefined) {
          // 没有Job信息，使用parse_progress（0-100范围）
          // parse_progress 是 0-100 的百分比，需要映射到 30-100% 的范围
          const parseProgressPercent = Math.min(data.parse_progress, 100) / 100; // 转换为 0-1
          targetProgress = 30 + parseProgressPercent * 70; // 30-100%
          console.log(`[解析中] 使用 parse_progress: ${data.parse_progress}% -> ${parseProgressPercent}, 目标进度: ${targetProgress}%`);
        } else {
          // 没有任何进度信息，保持在 30%
          targetProgress = 30;
          console.log(`[解析中] 无进度信息，保持在 30%`);
        }
        const oldProgress = currentDoc.progress;
        // 解析阶段：实时更新进度
        let newProgress: number;
        
        // 如果目标进度是30%（初始解析状态）
        if (targetProgress === 30) {
          if (currentDoc.progress >= 30) {
            // 当前进度已经>=30%，保持当前进度（避免倒退）
            newProgress = currentDoc.progress;
          } else {
            // 当前进度<30%，平滑过渡到30%（从上传切换到解析）
            newProgress = smoothProgress(30, currentDoc.progress);
          }
        } else {
          // 目标进度>30%，直接使用目标进度，实时更新
          newProgress = targetProgress;
        }
        
        // 如果消息中包含 num_pages，更新它（解析过程中可能会识别到页数）
        const updatedDoc: Doc = {
          ...currentDoc,
          status: "parsing",
          progress: newProgress,
        };
        if (data.num_pages !== undefined && data.num_pages > 0) {
          updatedDoc.num_pages = data.num_pages;
        }
        
        docs.value[docIndex] = updatedDoc;
        console.log(`[解析中] 进度更新: ${oldProgress}% -> ${newProgress}% (目标: ${targetProgress}%)${data.num_pages ? `, 页数: ${data.num_pages}` : ''}`);
      } else if (data.status === "parsed") {
        console.log(`解析完成 (${res.document_id}): num_pages=${data.num_pages}, elapsed=${elapsed}ms`);
        
        // 如果已经是 ready 状态，不再处理
        if (currentDoc.status === "ready") {
          console.log(`文档已经是 ready 状态，跳过处理`);
          return;
        }
        
        // 解析完成，先平滑过渡到100%，然后再更新为ready
        const newProgress = currentDoc.progress < 100 ? smoothProgress(100, currentDoc.progress) : 100;
        
        // 更新进度，但保持parsing状态，直到进度达到100%
        docs.value[docIndex] = {
          ...currentDoc,
          status: "parsing",
          progress: newProgress,
        };
        
        // 如果进度还没到100%，使用定时器继续更新
        if (newProgress < 99.5) {
          const progressInterval = setInterval(() => {
            const currentDoc2 = docs.value[docIndex];
            if (!currentDoc2 || currentDoc2.status === "ready") {
              clearInterval(progressInterval);
              return;
            }
            
            const nextProgress = smoothProgress(100, currentDoc2.progress);
            docs.value[docIndex] = {
              ...currentDoc2,
              progress: nextProgress,
            };
            
            // 当进度达到100%时，更新为ready状态
            if (nextProgress >= 99.5) {
              clearInterval(progressInterval);
              
              // 等待一小段时间让用户看到100%的进度
              setTimeout(async () => {
                const finalDoc = docs.value[docIndex];
                if (finalDoc && finalDoc.status !== "ready") {
                  // 获取完整文档信息（包括 num_pages）
                  getDocument(res.document_id).then(async (docData) => {
                    console.log(`获取文档信息成功 (${res.document_id}):`, docData);
                    const document = docData.document;
                    const finalDoc2 = docs.value[docIndex];
                    if (finalDoc2 && finalDoc2.status !== "ready") {
                      docs.value[docIndex] = {
                        ...finalDoc2,
                        title: document.title || finalDoc2.title,
                        num_pages: document.num_pages,
                        lang_in: document.lang_in || finalDoc2.lang_in,
                        lang_out: document.lang_out || finalDoc2.lang_out,
                        status: "ready",
                        progress: 100,
                      };
                      ws.disconnect();
                      activeWebSockets.delete(res.document_id);
                      // 重新加载项目文档列表
                      if (currentProjectId.value) await loadProjectDocuments(currentProjectId.value);
                      router.replace({ query: {} });
                      console.log(`文档状态已更新为 ready (${res.document_id})`);
                    }
                  }).catch(async (error) => {
                    console.error(`获取文档信息失败 (${res.document_id}):`, error);
                    // 如果获取失败，使用进度API的数据
                    const finalDoc3 = docs.value[docIndex];
                    if (finalDoc3 && finalDoc3.status !== "ready") {
                      docs.value[docIndex] = {
                        ...finalDoc3,
                        num_pages: data.num_pages || finalDoc3.num_pages || 0,
                        status: "ready",
                        progress: 100,
                      };
                      ws.disconnect();
                      activeWebSockets.delete(res.document_id);
                      // 重新加载项目文档列表
                      if (currentProjectId.value) await loadProjectDocuments(currentProjectId.value);
                      router.replace({ query: {} });
                      console.log(`使用进度数据更新文档状态为 ready (${res.document_id})`);
                    }
                  });
                }
              }, 300); // 显示100%进度300ms后再更新状态
            }
          }, 50); // 每50ms更新一次进度
        } else {
          // 进度已经接近100%，直接更新为ready
          setTimeout(async () => {
            const finalDoc = docs.value[docIndex];
            if (finalDoc && finalDoc.status !== "ready") {
              // 获取完整文档信息（包括 num_pages）
              getDocument(res.document_id).then(async (docData) => {
                console.log(`获取文档信息成功 (${res.document_id}):`, docData);
                const document = docData.document;
                const finalDoc2 = docs.value[docIndex];
                if (finalDoc2 && finalDoc2.status !== "ready") {
                  docs.value[docIndex] = {
                    ...finalDoc2,
                    title: document.title || finalDoc2.title,
                    num_pages: document.num_pages,
                    lang_in: document.lang_in || finalDoc2.lang_in,
                    lang_out: document.lang_out || finalDoc2.lang_out,
                    status: "ready",
                    progress: 100,
                  };
                  ws.disconnect();
                  activeWebSockets.delete(res.document_id);
                  // 重新加载项目文档列表
                  if (currentProjectId.value) await loadProjectDocuments(currentProjectId.value);
                  router.replace({ query: {} });
                  console.log(`文档状态已更新为 ready (${res.document_id})`);
                }
              }).catch(async (error) => {
                console.error(`获取文档信息失败 (${res.document_id}):`, error);
                // 如果获取失败，使用进度API的数据
                const finalDoc3 = docs.value[docIndex];
                if (finalDoc3 && finalDoc3.status !== "ready") {
                  docs.value[docIndex] = {
                    ...finalDoc3,
                    num_pages: data.num_pages || finalDoc3.num_pages || 0,
                    status: "ready",
                    progress: 100,
                  };
                  ws.disconnect();
                  activeWebSockets.delete(res.document_id);
                  // 重新加载项目文档列表
                  if (currentProjectId.value) await loadProjectDocuments(currentProjectId.value);
                  router.replace({ query: {} });
                  console.log(`使用进度数据更新文档状态为 ready (${res.document_id})`);
                }
              });
            }
          }, 300);
        }
      }
    });
    
    ws.onError((error) => {
      console.error("WebSocket 错误:", error);
      // WebSocket 错误时，显示错误状态
      uploadingDoc.status = "parsing";
      uploadingDoc.progress = 50; // 显示中间进度，等待重连
    });
    
    ws.onClose(() => {
      activeWebSockets.delete(res.document_id);
    });
    
    // 连接 WebSocket
    ws.connect().then(() => {
      console.log(`WebSocket 连接成功 (${res.document_id})`);
    }).catch((error) => {
      console.error("WebSocket 连接失败:", error);
      // WebSocket 连接失败时，显示错误状态
      uploadingDoc.status = "parsing";
      uploadingDoc.progress = 50; // 显示中间进度，等待重连
    });
    
  } catch (error) {
    console.error("Upload failed:", error);
    alert("上传失败，请重试");
    docs.value = docs.value.filter((d) => d.document_id !== uploadingDoc.document_id);
    router.replace('/app');
    delete (window as any).__pendingUploadFile;
  }
};

const loadDocumentFromQuery = async () => {
  const documentId = route.query.document_id as string | undefined;
  const isUploading = route.query.uploading === "true";
  const filename = route.query.filename as string | undefined;
  
  // 如果没有 document_id 但有 uploading 标记，说明是新的上传
  if (!documentId && isUploading) {
    await handlePendingUpload();
    return;
  }
  
  if (!documentId) return;

  // 检查是否已经存在
  const existingDoc = docs.value.find((d) => d.document_id === documentId);
  if (existingDoc && existingDoc.status === "ready") {
    // 如果已经就绪，清除查询参数即可
    router.replace({ query: {} });
    return;
  }

  // 如果文档不存在，创建临时文档（WebSocket 会发送初始状态）
  let doc = existingDoc || docs.value.find((d) => d.document_id === documentId);
  
  if (!doc) {
    // 创建临时文档，等待 WebSocket 发送初始状态
    doc = {
      document_id: documentId,
      title: filename ? decodeURIComponent(filename) : "处理中...",
      lang_in: "en",
      lang_out: "zh",
      status: isUploading ? "uploading" : "parsing",
      progress: isUploading ? 0 : 30,
    };
    docs.value.unshift(doc);
  }

  // 记录开始时间，用于平滑进度显示
  const startTime = Date.now();
  const minDisplayTime = 2000; // 最少显示2秒
  
  // 平滑进度动画函数 - 使用更智能的步长算法
  const smoothProgress = (targetProgress: number, currentProgress: number) => {
    const diff = targetProgress - currentProgress;
    if (Math.abs(diff) < 0.5) return targetProgress;
    
    // 根据距离目标的远近调整步长：
    // - 距离远时（>20%），步长较大（10%），快速接近
    // - 距离中等时（5-20%），步长中等（5%）
    // - 距离近时（<5%），步长较小（2%），精确到达
    let stepSize: number;
    const absDiff = Math.abs(diff);
    if (absDiff > 20) {
      stepSize = 10; // 快速接近
    } else if (absDiff > 5) {
      stepSize = 5; // 中等速度
    } else {
      stepSize = 2; // 精确到达
    }
    
    return currentProgress + Math.sign(diff) * Math.min(absDiff, stepSize);
  };
  
  // 使用 WebSocket 接收实时进度更新
  const ws = new DocumentProgressWebSocket(documentId);
  activeWebSockets.set(documentId, ws);
  
  ws.onMessage((data) => {
    const elapsed = Date.now() - startTime;
    
    if (!doc) return;
    
    // 找到文档在数组中的索引
    const docIndex = docs.value.findIndex(d => d.document_id === documentId);
    if (docIndex < 0) {
      console.warn(`文档 ${documentId} 不在列表中`);
      return;
    }
    
    const currentDoc = docs.value[docIndex];
    
    // 根据状态更新进度
    if (data.status === "uploading") {
      const targetProgress = Math.min(data.parse_progress || currentDoc.progress, 30);
      const newProgress = smoothProgress(targetProgress, currentDoc.progress);
      docs.value[docIndex] = {
        ...currentDoc,
        status: "uploading",
        progress: newProgress,
      };
      console.log(`[上传中] 目标进度: ${targetProgress}%, 当前进度: ${newProgress}%`);
    } else if (data.status === "parsing") {
      // 立即更新状态为 parsing（从 uploading 切换）
      
      // 如果有parse_job，使用真实的进度（done/total）
      let targetProgress = 30;
      if (data.parse_job) {
        const parseJob = data.parse_job;
        if (parseJob.total && parseJob.total > 0) {
          const parseProgress = (parseJob.done || 0) / parseJob.total;
          targetProgress = 30 + parseProgress * 70; // 30-100%
          console.log(`[解析中] 使用 Job 进度: ${parseJob.done}/${parseJob.total} = ${parseProgress}, 目标进度: ${targetProgress}%`);
        } else {
          // 没有total，使用progress字段（0-1范围）
          targetProgress = 30 + (parseJob.progress || 0) * 70;
          console.log(`[解析中] 使用 Job progress 字段: ${parseJob.progress}, 目标进度: ${targetProgress}%`);
        }
      } else if (data.parse_progress !== undefined) {
        // 没有Job信息，使用parse_progress（0-100范围）
        // parse_progress 是 0-100 的百分比，需要映射到 30-100% 的范围
        const parseProgressPercent = Math.min(data.parse_progress, 100) / 100; // 转换为 0-1
        targetProgress = 30 + parseProgressPercent * 70; // 30-100%
        console.log(`[解析中] 使用 parse_progress: ${data.parse_progress}% -> ${parseProgressPercent}, 目标进度: ${targetProgress}%`);
      } else {
        // 没有任何进度信息，保持在 30%
        targetProgress = 30;
        console.log(`[解析中] 无进度信息，保持在 30%`);
      }
      const oldProgress = currentDoc.progress;
      // 解析阶段：实时更新进度
      let newProgress: number;
      
      // 如果目标进度是30%（初始解析状态）
      if (targetProgress === 30) {
        if (currentDoc.progress >= 30) {
          // 当前进度已经>=30%，保持当前进度（避免倒退）
          newProgress = currentDoc.progress;
        } else {
          // 当前进度<30%，平滑过渡到30%（从上传切换到解析）
          newProgress = smoothProgress(30, currentDoc.progress);
        }
      } else {
        // 目标进度>30%，直接使用目标进度，实时更新
        newProgress = targetProgress;
      }
      
      // 如果消息中包含 num_pages，更新它（解析过程中可能会识别到页数）
      const updatedDoc: Doc = {
        ...currentDoc,
        status: "parsing",
        progress: newProgress,
      };
      if (data.num_pages !== undefined && data.num_pages > 0) {
        updatedDoc.num_pages = data.num_pages;
      }
      
      docs.value[docIndex] = updatedDoc;
      console.log(`[解析中] 进度更新: ${oldProgress}% -> ${newProgress}% (目标: ${targetProgress}%)${data.num_pages ? `, 页数: ${data.num_pages}` : ''}`);
    } else if (data.status === "parsed") {
      console.log(`解析完成 (${documentId}): num_pages=${data.num_pages}, elapsed=${elapsed}ms, 当前状态=${currentDoc.status}`);
      
      // 如果已经是 ready 状态，不再处理
      if (currentDoc.status === "ready") {
        console.log(`文档已经是 ready 状态，跳过处理`);
        return;
      }
      
      // 解析完成，先平滑过渡到100%，然后再更新为ready
      const newProgress = currentDoc.progress < 100 ? smoothProgress(100, currentDoc.progress) : 100;
      
      // 更新进度，但保持parsing状态，直到进度达到100%
      docs.value[docIndex] = {
        ...currentDoc,
        status: "parsing",
        progress: newProgress,
      };
      
      // 如果进度还没到100%，使用定时器继续更新
      if (newProgress < 99.5) {
        const progressInterval = setInterval(() => {
          const currentDoc2 = docs.value[docIndex];
          if (!currentDoc2 || currentDoc2.status === "ready") {
            clearInterval(progressInterval);
            return;
          }
          
          const nextProgress = smoothProgress(100, currentDoc2.progress);
          docs.value[docIndex] = {
            ...currentDoc2,
            progress: nextProgress,
          };
          
          // 当进度达到100%时，更新为ready状态
          if (nextProgress >= 99.5) {
            clearInterval(progressInterval);
            
            // 等待一小段时间让用户看到100%的进度
            setTimeout(async () => {
              const finalDoc = docs.value[docIndex];
              if (finalDoc && finalDoc.status !== "ready") {
                // 获取完整文档信息
                getDocument(documentId).then(async (docData) => {
                  console.log(`获取文档信息成功 (${documentId}):`, docData);
                  const document = docData.document;
                  const finalDoc2 = docs.value[docIndex];
                  if (finalDoc2 && finalDoc2.status !== "ready") {
                    docs.value[docIndex] = {
                      ...finalDoc2,
                      title: document.title || finalDoc2.title,
                      num_pages: document.num_pages,
                      lang_in: document.lang_in || finalDoc2.lang_in,
                      lang_out: document.lang_out || finalDoc2.lang_out,
                      status: "ready",
                      progress: 100,
                    };
                    // 重新加载项目文档列表
                    if (currentProjectId.value) await loadProjectDocuments(currentProjectId.value);
                    router.replace({ query: {} });
                    ws.disconnect();
                    activeWebSockets.delete(documentId);
                    console.log(`文档状态已更新为 ready (${documentId})`);
                  }
                }).catch(async (error) => {
                  console.error(`获取文档信息失败 (${documentId}):`, error);
                  // 如果获取失败，使用进度API的数据
                  const finalDoc3 = docs.value[docIndex];
                  if (finalDoc3 && finalDoc3.status !== "ready") {
                    docs.value[docIndex] = {
                      ...finalDoc3,
                      num_pages: data.num_pages || finalDoc3.num_pages || 0,
                      status: "ready",
                      progress: 100,
                    };
                    // 重新加载项目文档列表
                    if (currentProjectId.value) await loadProjectDocuments(currentProjectId.value);
                    router.replace({ query: {} });
                    ws.disconnect();
                    activeWebSockets.delete(documentId);
                    console.log(`使用进度数据更新文档状态为 ready (${documentId})`);
                  }
                });
              }
            }, 300); // 显示100%进度300ms后再更新状态
          }
        }, 50); // 每50ms更新一次进度
      } else {
        // 进度已经接近100%，直接更新为ready
        setTimeout(async () => {
          const finalDoc = docs.value[docIndex];
          if (finalDoc && finalDoc.status !== "ready") {
            // 获取完整文档信息
            getDocument(documentId).then(async (docData) => {
              console.log(`获取文档信息成功 (${documentId}):`, docData);
              const document = docData.document;
              const finalDoc2 = docs.value[docIndex];
              if (finalDoc2 && finalDoc2.status !== "ready") {
                docs.value[docIndex] = {
                  ...finalDoc2,
                  title: document.title || finalDoc2.title,
                  num_pages: document.num_pages,
                  lang_in: document.lang_in || finalDoc2.lang_in,
                  lang_out: document.lang_out || finalDoc2.lang_out,
                  status: "ready",
                  progress: 100,
                };
                // 重新加载项目文档列表
                if (currentProjectId.value) await loadProjectDocuments(currentProjectId.value);
                router.replace({ query: {} });
                ws.disconnect();
                activeWebSockets.delete(documentId);
                console.log(`文档状态已更新为 ready (${documentId})`);
              }
            }).catch(async (error) => {
              console.error(`获取文档信息失败 (${documentId}):`, error);
              // 如果获取失败，使用进度API的数据
              const finalDoc3 = docs.value[docIndex];
              if (finalDoc3 && finalDoc3.status !== "ready") {
                docs.value[docIndex] = {
                  ...finalDoc3,
                  num_pages: data.num_pages || finalDoc3.num_pages || 0,
                  status: "ready",
                  progress: 100,
                };
                // 重新加载项目文档列表
                if (currentProjectId.value) await loadProjectDocuments(currentProjectId.value);
                router.replace({ query: {} });
                ws.disconnect();
                activeWebSockets.delete(documentId);
                console.log(`使用进度数据更新文档状态为 ready (${documentId})`);
              }
            });
          }
        }, 300);
      }
    }
  });
  
  ws.onError((error) => {
    console.error("WebSocket 错误:", error);
    // WebSocket 错误时，显示错误状态
    if (doc) {
      doc.status = "parsing";
      doc.progress = 50; // 显示中间进度，等待重连
    }
  });
  
  ws.onClose(() => {
    activeWebSockets.delete(documentId);
  });
  
  // 连接 WebSocket
  ws.connect().catch((error) => {
    console.error("WebSocket 连接失败:", error);
    // WebSocket 连接失败时，显示错误状态
    if (doc) {
      doc.status = "parsing";
      doc.progress = 50; // 显示中间进度，等待重连
    }
  });
};

onMounted(async () => {
  // 尝试从 URL 参数获取项目ID，或者创建/使用默认项目
  const projectIdFromQuery = route.query.project_id as string | undefined;
  
  if (projectIdFromQuery) {
    currentProjectId.value = projectIdFromQuery;
    await loadProjectDocuments(projectIdFromQuery);
  } else {
    // 如果没有项目ID，创建一个新项目并加载文档列表
    try {
      const { project_id } = await createProject(projectName.value || "我的项目");
      currentProjectId.value = project_id;
      await loadProjectDocuments(project_id);
    } catch (error) {
      console.error("创建项目失败:", error);
    }
  }
  
  await loadDocumentFromQuery();
});

onUnmounted(() => {
  // 清理所有 WebSocket 连接
  activeWebSockets.forEach((ws) => ws.disconnect());
  activeWebSockets.clear();
});
</script>

<style scoped>
.dashboard {
  position: relative;
  min-height: calc(100vh - 200px);
}

.empty-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 60px 32px;
}

.empty-state-content {
  text-align: center;
  max-width: 480px;
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.empty-state-icon {
  margin: 0 auto 24px;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.95) 0%, 
    rgba(250, 245, 255, 0.92) 25%,
    rgba(240, 249, 255, 0.92) 50%,
    rgba(255, 250, 240, 0.92) 75%,
    rgba(255, 255, 255, 0.95) 100%);
  border-radius: 24px;
  border: 1px solid rgba(226, 232, 240, 0.6);
  box-shadow: 
    0 8px 24px rgba(99, 102, 241, 0.08),
    0 4px 12px rgba(139, 92, 246, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.empty-state-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 12px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.empty-state-description {
  font-size: 15px;
  line-height: 1.6;
  color: #64748b;
  margin: 0;
  padding: 0 20px;
}

@media (max-width: 640px) {
  .empty-state {
    padding: 40px 24px;
  }

  .empty-state-icon {
    width: 100px;
    height: 100px;
    margin-bottom: 20px;
  }

  .empty-state-title {
    font-size: 20px;
  }

  .empty-state-description {
    font-size: 14px;
    padding: 0;
  }
}
</style>

