<script setup>
import { ref, defineEmits } from 'vue'
import { authorizePair } from '../github.js'
import { setSyncMsg } from '../store.js'

const emit = defineEmits(['close'])
const codeInput = ref('')
const state = ref('input') // input | busy | ok | error
const errMsg = ref('')

async function authorize() {
  const code = codeInput.value.trim().toUpperCase().replace(/[^A-Z2-9]/g, '')
  if (code.length !== 8) { errMsg.value = '请输入新设备显示的 8 位配对码'; return }
  state.value = 'busy'
  errMsg.value = ''
  try {
    await authorizePair(code)
    state.value = 'ok'
    setSyncMsg('✅ 已授权新设备')
  } catch (e) {
    state.value = 'error'
    errMsg.value = e.message
  }
}
</script>

<template>
  <div class="auth-modal" @click.self="emit('close')">
    <div class="auth-box">
      <template v-if="state === 'ok'">
        <div style="text-align:center;padding:16px 0">
          <div style="font-size:48px">🤝</div>
          <h3 style="margin-top:10px">授权完成</h3>
          <div class="mode">回到新设备，它会在几秒内自动登录 · 配对信息已加密且会自动清理</div>
        </div>
      </template>
      <template v-else>
        <h3>授权新设备</h3>
        <div class="mode">
          在新设备上打开本站学习中心，选择「接力登录」，会显示一个 8 位配对码。把它输入到下面：
        </div>
        <input v-model="codeInput" placeholder="8 位配对码" maxlength="8"
          style="text-transform:uppercase;letter-spacing:4px;font-size:20px;text-align:center;font-weight:800"
          @keyup.enter="authorize">
        <div class="auth-err">{{ errMsg }}</div>
        <button class="btn" style="width:100%" :disabled="state === 'busy'" @click="authorize">
          {{ state === 'busy' ? '正在加密授权…' : '确认授权' }}
        </button>
      </template>
      <div style="text-align:center;margin-top:14px">
        <span class="hint" style="cursor:pointer" @click="emit('close')">关闭</span>
      </div>
    </div>
  </div>
</template>
