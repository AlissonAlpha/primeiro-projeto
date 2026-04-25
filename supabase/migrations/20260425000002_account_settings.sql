-- Configurações por conta de anúncio
CREATE TABLE IF NOT EXISTS account_settings (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  ad_account_id TEXT NOT NULL UNIQUE,
  account_name TEXT,
  whatsapp_number TEXT,        -- ex: 5517991234567
  website_url TEXT,
  facebook_page_id TEXT,
  default_country TEXT DEFAULT 'BR',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER trg_account_settings_updated_at
  BEFORE UPDATE ON account_settings
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
