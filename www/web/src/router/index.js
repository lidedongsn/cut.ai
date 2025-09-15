import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'HomePage',
      component: () => import('@/views/HomeView.vue'),
      meta: { layout: 'centered' }
    },
    {
      path: '/transcripts/:task_id',
      name: 'transcripts',
      component: () => import('@/views/FileTranscripts.vue')
    },
    {
      path: '/tasks',
      name: 'tasks',
      component: () => import('@/views/AllTasksView.vue')
    }
  ]
})

router.beforeEach((to, from, next) => {
  // const isLoggedIn = checkIfUserIsLoggedIn() // 根据您的登录状态检查方式返回一个布尔值

  // if (to.path !== '/' && !isLoggedIn) {
  //   // 用户未登录并且试图访问其他页面时重定向到登录页面
  //   next('/')
  // } else {
    // 用户已登录或访问登录页面
    next()
  // }
})

function checkIfUserIsLoggedIn() {
  // 从本地存储获取用户登录状态
  const loginInfo = sessionStorage.getItem('loginData')
  if (loginInfo === null || loginInfo === undefined || loginInfo === '') {
    return false
  }
  return true
}
export default router
