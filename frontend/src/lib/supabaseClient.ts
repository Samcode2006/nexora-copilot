import { createClient } from "@supabase/supabase-js";

// Supabase is used in the browser for AUTHENTICATION ONLY.
// All NEXORA data and business logic go through FastAPI (see ./api.ts).

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

if (!supabaseUrl || !supabaseKey) {
    throw new Error("Missing Supabase environment variables");
}

/** Refuse to start if a privileged key was put in the browser bundle by mistake. */
function assertPublicKey(key: string): void {
    if (key.startsWith("sb_secret_")) {
        throw new Error("A Supabase secret key must never be used in the frontend.");
    }
    const parts = key.split(".");
    if (parts.length === 3) {
        // Legacy JWT-style key: the anon key is fine, service_role is not.
        try {
            const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/")));
            if (payload?.role === "service_role") {
                throw new Error("The service_role key must never be used in the frontend.");
            }
        } catch (err) {
            if (err instanceof Error && err.message.includes("service_role")) throw err;
        }
    }
}

assertPublicKey(supabaseKey);

export const supabase = createClient(supabaseUrl, supabaseKey, {
    auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
    },
});
