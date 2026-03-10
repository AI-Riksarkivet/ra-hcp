// See https://svelte.dev/docs/kit/types#app.d.ts
declare const __APP_VERSION__: string;

declare global {
  namespace App {
    // interface Error {}
    interface Locals {
      token?: string;
    }
    // interface PageData {}
    // interface PageState {}
    // interface Platform {}
  }
}

export {};
