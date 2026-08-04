<template>
  <section class="content-grid two-columns">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>评估结果</span>
          <el-tag type="info">本地展示骨架</el-tag>
        </div>
      </template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="评测集">agent_eval_v1</el-descriptions-item>
        <el-descriptions-item label="Baseline">stage10-baseline</el-descriptions-item>
        <el-descriptions-item label="Candidate">stage11-candidate</el-descriptions-item>
        <el-descriptions-item label="回归状态">后续接入 Python evaluation 数据</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never">
      <template #header>Bad Case 闭环</template>
      <el-steps direction="vertical" :active="2" finish-status="success">
        <el-step title="收集坏例" description="从线上反馈或评估失败中沉淀问题" />
        <el-step title="分析失败层" description="区分 RAG、Tool、Prompt、权限或模型输出问题" />
        <el-step title="转回归样例" description="修复后进入 regression case" />
      </el-steps>
    </el-card>
  </section>
</template>
