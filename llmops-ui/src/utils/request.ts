import { apiPrefix, httpCode } from '@/config';
import { Message } from '@arco-design/web-vue';

const TIMEOUT = 1000 * 60 * 5;

const baseFetchOptions = {
  method: 'GET',
  mode: 'cors',
  credentials: 'include',
  headers: new Headers({
    'Content-Type': 'application/json',
  }),
  redirect: 'follow',
};

type FetchOptionType = Omit<RequestInit, 'body'> & {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  params?: Record<string, any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  body?: Record<string, any> | null | BodyInit;
};

const baseFetch = <T>(url: string, fetchOptions: FetchOptionType): Promise<T> => {
  const options: typeof baseFetchOptions & FetchOptionType = Object.assign(
    {},
    baseFetchOptions,
    fetchOptions,
  );

  const u = url.startsWith('/') ? url : `/${url}`;
  let urlWithPrefix = `${apiPrefix}${u}`;

  const { method, params, body } = options;
  if (method && method.toUpperCase() === 'GET' && params) {
    const paramsArray: string[] = [];
    Object.keys(params).forEach((key) => {
      paramsArray.push(`${key}=${encodeURIComponent(params[key])}`);
    });
    if (urlWithPrefix.search(/\?/) === -1) {
      urlWithPrefix += `?${paramsArray.join('&')}`;
    } else {
      urlWithPrefix += `&${paramsArray.join('&')}`;
    }
    delete options.params;
  }
  if (body) {
    options.body = JSON.stringify(body);
  }
  return Promise.race([
    new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error('接口请求超时'));
      }, TIMEOUT);
    }),
    new Promise((resolve, reject) => {
      globalThis
        .fetch(urlWithPrefix, options as RequestInit)
        .then(async (res) => {
          const json = await res.json();
          if (json.code === httpCode.success) {
            resolve(json);
          } else {
            Message.error(json.message);
            reject(new Error(json.message));
          }
        })
        .catch((err) => {
          Message.error(err.message);
          reject(err);
        });
    }),
  ]) as Promise<T>;
};

export const request = <T>(url: string, options = {}) => {
  return baseFetch<T>(url, options);
};

export const get = <T>(url: string, options = {}) => {
  return baseFetch<T>(url, {
    ...options,
    method: 'GET',
  });
};
export const post = <T>(url: string, options = {}) => {
  return baseFetch<T>(url, {
    ...options,
    method: 'POST',
  });
};
