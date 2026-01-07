"""
Quick check to determine if using service_role or anon key
"""
import os
from dotenv import load_dotenv

load_dotenv()

key = os.environ.get("SUPABASE_KEY", "")

print(f"Key length: {len(key)}")
print(f"Key prefix: {key[:20]}...")

if not key:
    print("❌ No SUPABASE_KEY found in environment")
elif key.startswith("eyJ"):
    # Likely a JWT token
    try:
        import base64
        import json
        
        # JWT format: header.payload.signature
        parts = key.split('.')
        if len(parts) == 3:
            # Decode payload (add padding if needed)
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.b64decode(payload)
            data = json.loads(decoded)
            
            role = data.get('role', 'unknown')
            print(f"\n🔑 Key type: {role}")
            
            if role == 'anon':
                print("\n⚠️  WARNING: You're using the ANON key!")
                print("   This key respects Row Level Security (RLS) policies.")
                print("   Profile creation may fail if RLS policies are too restrictive.")
                print("\n✅ SOLUTION: Use the SERVICE_ROLE key instead:")
                print("   1. Go to Supabase Dashboard → Settings → API")
                print("   2. Copy the 'service_role' key (NOT the 'anon' key)")
                print("   3. Update SUPABASE_KEY in your .env file")
                print("\n   The service_role key bypasses RLS and is safe for backend use.")
            elif role == 'service_role':
                print("✅ Correct! You're using the SERVICE_ROLE key.")
                print("   This key bypasses RLS policies and can create profiles.")
            else:
                print(f"❓ Unknown role: {role}")
    except Exception as e:
        print(f"❌ Error decoding JWT: {e}")
else:
    print("\n⚠️  Key doesn't look like a standard Supabase JWT")
    print("   Supabase keys typically start with 'eyJ'")
    print("   Please verify you're using the correct key from:")
    print("   Supabase Dashboard → Settings → API")

