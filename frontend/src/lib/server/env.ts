import { env } from "$env/dynamic/private";

export const BACKEND_URL = env.BACKEND_URL ?? "http://127.0.0.1:8000";
