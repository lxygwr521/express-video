import { ElMessage } from 'element-plus'

export function useToast() {
  function success(msg: string) {
    ElMessage.success(msg)
  }
  function error(msg: string) {
    ElMessage.error(msg)
  }
  function info(msg: string) {
    ElMessage.info(msg)
  }
  function warning(msg: string) {
    ElMessage.warning(msg)
  }
  return { success, error, info, warning }
}
