import { defineStore } from 'pinia';
import { ref } from 'vue';

const initialState = {
  name: '',
  email: '',
  avatar: '',
};

export const useAccountStore = defineStore('account', () => {
  const account = ref({ ...initialState });

  const update = (data: Partial<typeof initialState>) => {
    Object.assign(account.value, data);
  };

  const clear = () => {
    account.value = { ...initialState };
  };

  return {
    account,
    update,
    clear,
  };
});
