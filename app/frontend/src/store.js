import { reactive } from 'vue'
import { getToken, GH, pullData, pushData } from './github.js'

// 全局共享状态：登录用户 + 云同步版本号 + 云服务可用性（'checking'|'on'|'off'）
export const store = reactive({
  username: '',
  syncTick: 0,
  syncMsg: '',
  cloud: 'checking'
})

// 两模块的 localStorage key（与静态版保持一致，同域名可互通）
export const LS_KEYS = {
  finance: { wrong: 'agfin_wrong', hist: 'agfin_hist' },
  spanish: { mark: 'agv_mark' }
}

export function lsGet(key, fallback) {
  try {
    const v = JSON.parse(localStorage.getItem(key))
    return v ?? fallback
  } catch { return fallback }
}

// 统一写入口：落盘后自动调度云同步（3 秒防抖合并连续写入）
let syncTimer = null
let applying = false
export function lsSet(key, value) {
  localStorage.setItem(key, JSON.stringify(value))
  scheduleSync()
}

export function collectAll() {
  return {
    finance: {
      wrongSet: lsGet(LS_KEYS.finance.wrong, []),
      histArr: lsGet(LS_KEYS.finance.hist, [])
    },
    spanish: {
      VMARK: lsGet(LS_KEYS.spanish.mark, {})
    }
  }
}

export function applyAll(remote) {
  if (!remote) return
  applying = true
  try {
    if (remote.finance) {
      lsSet(LS_KEYS.finance.wrong, remote.finance.wrongSet || [])
      lsSet(LS_KEYS.finance.hist, remote.finance.histArr || [])
    }
    if (remote.spanish) {
      lsSet(LS_KEYS.spanish.mark, remote.spanish.VMARK || {})
    }
  } finally {
    applying = false
  }
  store.syncTick++
  setSyncMsg('✅ 已从云端恢复到本机')
}

export function setSyncMsg(msg, isErr = false) {
  store.syncMsg = msg
  clearTimeout(setSyncMsg._t)
  setSyncMsg._t = setTimeout(() => { store.syncMsg = '' }, 4000)
}

// ===== 云同步（GitHub 私有仓库数据层）=====
export function cloudReady() {
  return GH.configured && !!getToken()
}

export async function uploadCloud(manual = false) {
  if (!cloudReady()) { if (manual) setSyncMsg('❌ 请先登录', true); return false }
  const data = collectAll()
  const empty = !data.finance.wrongSet.length && !data.finance.histArr.length && !Object.keys(data.spanish.VMARK).length
  if (empty && manual && !confirm('本地学习记录为空，上传将覆盖云端数据，确定继续？')) return false
  try {
    await pushData({ ...data, updatedAt: new Date().toISOString() })
    if (manual) setSyncMsg('✅ 已上传到云端')
    return true
  } catch (e) {
    if (manual) setSyncMsg('❌ ' + e.message, true)
    return false
  }
}

export async function pullCloud(manual = false) {
  if (!cloudReady()) { if (manual) setSyncMsg('❌ 请先登录', true); return false }
  try {
    const { exists, data } = await pullData()
    if (!exists) { if (manual) setSyncMsg('云端暂无数据'); return false }
    applyAll(data)
    return true
  } catch (e) {
    if (manual) setSyncMsg('❌ ' + e.message, true)
    return false
  }
}

// 自动同步：本地任何学习数据变更 → 防抖 3 秒后静默上传
export function scheduleSync() {
  if (applying || !cloudReady()) return
  clearTimeout(syncTimer)
  syncTimer = setTimeout(async () => {
    const ok = await uploadCloud(false)
    if (ok) setSyncMsg('☁️ 已自动同步到云端')
  }, 3000)
}
