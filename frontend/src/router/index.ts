import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      redirect: '/digest/new',
    },
    {
      path: '/digest/new',
      name: 'DigestNew',
      component: () => import('@/views/DigestNew.vue'),
    },
    {
      path: '/digest/list',
      name: 'DigestList',
      component: () => import('@/views/DigestList.vue'),
    },
    {
      path: '/digest/:task_id',
      name: 'DigestDetail',
      component: () => import('@/views/DigestDetail.vue'),
      props: true,
    },
    {
      path: '/actions',
      name: 'Actions',
      component: () => import('@/views/Actions.vue'),
    },
    {
      path: '/tags',
      name: 'Tags',
      component: () => import('@/views/Tags.vue'),
    },
    {
      path: '/review',
      name: 'Review',
      component: () => import('@/views/Review.vue'),
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta?.public || token) {
    next()
  } else {
    next('/login')
  }
})

export default router
