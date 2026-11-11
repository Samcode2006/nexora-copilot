import { createClient } from "@supabase/supabase-js";
import { assertPublicKey } from "./keyValidation";

// Supabase is used in the browser for AUTHENTICATION ONLY.
// All NEXORA data and business logic go through FastAPI (see ./api.ts).

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

if (!supabaseUrl || !supabaseKey) {
    throw new Error("Missing Supabase environment variables");
}

assertPublicKey(supabaseKey);

export const supabase = createClient(supabaseUrl, supabaseKey, {
    auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
    },
});
