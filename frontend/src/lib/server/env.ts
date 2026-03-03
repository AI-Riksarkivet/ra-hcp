import { env } from "$env/dynamic/private";

export const BACKEND_URL = env.BACKEND_URL ?? "http://localhost:8000";
