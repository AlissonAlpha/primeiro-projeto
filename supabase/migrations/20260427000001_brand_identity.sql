ALTER TABLE account_settings ADD COLUMN IF NOT EXISTS logo_url TEXT;
ALTER TABLE account_settings ADD COLUMN IF NOT EXISTS brand_colors TEXT;
ALTER TABLE account_settings ADD COLUMN IF NOT EXISTS brand_palette TEXT;
