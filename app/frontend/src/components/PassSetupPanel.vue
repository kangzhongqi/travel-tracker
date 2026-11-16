<script setup>
import { ref, defineEmits } from 'vue'
import { getToken, getOwner, saveCredential } from '../github.js'
import { setSyncMsg } from '../store.js'

const emit = defineEmits(['close'])
const pass = ref('')
const pass2 = ref('')
const state = ref('input') // input | busy | ok | error
const errMsg = ref('')

async function save() {
  if (pass.value.length < 6) { errMsg.value = '同步密码至少 6 位（建议 8 位以上含字母与数字）'; return }
  if (pass.value !== pass2.value) { errMsg.value = '两次输入不一致'; return }
  state.value = 'busy'
  errMsg.value = ''
  try {
    await saveCredential(getToken(), getOwner(), pass.value)
    state.value = 'ok'
    setSyncMsg('✅ 同步密码已设置，任何设备可密码直登')
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
          <div style="font-size:48px">🔐</div>
          <h3 style="margin-top:10px">密码登录已开启</h3>
          <div class="mode">以后任何设备：登录 → 密码登录 → 输 GitHub 用户名 + 该密码即可直接登录</div>
        </div>
      </template>
      <template v-else>
        <h3>设置密码登录</h3>
        <div class="mode">
          设置后，任何新设备输「GitHub 用户名 + 此密码」即可直接登录，无需其他设备参与。
          密码经高强度加密保护你的访问令牌（31 万次迭代），但请勿使用纯数字弱密码。
        </div>
        <input v-model="pass" type="password" placeholder="设置同步密码（≥6 位）" maxlength="64" @keyup.enter="save">
        <input v-model="pass2" type="password" placeholder="再输入一次" maxlength="64" @keyup.enter="save">
        <div class="auth-err">{{ errMsg }}</div>
        <button class="btn" style="width:100%" :disabled="state === 'busy'" @click="save">
          {{ state === 'busy' ? '正在加密保存…' : '保存并开启' }}
        </button>
      </template>
      <div style="text-align:center;margin-top:14px">
        <span class="hint" style="cursor:pointer" @click="emit('close')">关闭</span>
      </div>
    </div>
  </div>
</template>
