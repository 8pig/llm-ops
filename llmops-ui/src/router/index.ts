import { createRouter, createWebHistory } from 'vue-router';
import DefaultLayout from '@/views/layouts/DefaultLayout.vue';
import BlankLayout from '@/views/layouts/BlankLayout.vue';
import { isLogin } from '@/utils/auth.ts';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: DefaultLayout,
      children: [
        {
          path: '',
          redirect: '/home',
        },
        {
          path: 'home',
          name: 'pages-home',
          component: () => import('@/views/pages/HomeView.vue'),
        },
        {
          path: 'space/apps',
          name: 'space-apps-list',
          component: () => import('@/views/space/apps/ListView.vue'),
        },
        {
          path: 'space/apps/:app_id',
          name: 'space-apps-detail',
          component: () => import('@/views/space/apps/DetailView.vue'),
        },
      ],
    },
    {
      path: '/',
      component: BlankLayout,
      children: [
        {
          path: 'auth/login',
          name: 'auth-login',
          component: () => import('@/views/auth/LoginView.vue'),
        },
      ],
    },
  ],
});
router.beforeEach((to, from) => {
  console.log(to);
  console.log(from);
  if (!isLogin() && to.name != 'auth-login') {
    return { path: '/auth/login' };
  }
});

export default router;
