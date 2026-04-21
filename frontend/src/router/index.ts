import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
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
      path: '/actions',
      name: 'Actions',
      component: () => import('@/views/Actions.vue'),
    },
    {
      path: '/review',
      name: 'Review',
      component: () => import('@/views/Review.vue'),
    },
  ],
})

export default router
